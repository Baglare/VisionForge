# HandDetector çıktısından debug amaçlı daha kararlı el takip durumu üretir.

from __future__ import annotations

from dataclasses import dataclass, field
import math
import time

import cv2
import numpy as np


@dataclass
class HandState:
    """Tek karelik ortak el takip durumunu temsil eder."""

    hand_detected: bool = False
    tracking_source: str = "lost"
    active_hand: str = "-"
    hand_count: int = 0
    handedness: list[str] = field(default_factory=list)
    hand_center: tuple[float, float] | None = None
    smoothed_hand_center: tuple[float, float] | None = None
    hand_velocity: tuple[float, float] | None = None
    palm_open_score: float = 0.0
    two_hand_score: float = 0.0
    tracking_quality: float = 0.0
    missing_time: float = 0.0
    quality_warnings: list[str] = field(default_factory=list)
    brightness_score: float = 0.0
    blur_score: float = 0.0
    hand_near_edge: bool = False


class HandStateTracker:
    """MediaPipe el sonucunu smoothing ve kısa kayıp toleransıyla takip eder."""

    STABLE_LANDMARKS = (0, 1, 5, 9, 13, 17)

    def __init__(self) -> None:
        self._prev_gray = None
        self._prev_points = None
        self._last_center: tuple[float, float] | None = None
        self._smoothed_center: tuple[float, float] | None = None
        self._last_update_at: float | None = None
        self._last_seen_at: float | None = None
        self._flow_confidence = 0.0

    def update(
        self,
        frame,
        hand_result,
        detection_profile: str = "Dengeli",
        now: float | None = None,
    ) -> HandState:
        """Yeni kare ve HandDetector sonucundan shadow/debug el durumunu üretir."""
        current_time = now if now is not None else time.monotonic()
        config = self._profile_config(detection_profile)
        gray = self._to_gray(frame)
        brightness_score, blur_score = self._quality_scores(gray)
        quality_warnings = self._quality_warnings(brightness_score, blur_score, config)
        dt = self._delta_time(current_time)

        if hand_result is not None and hand_result.detected and hand_result.hands:
            state = self._state_from_mediapipe(
                hand_result,
                frame,
                gray,
                quality_warnings,
                brightness_score,
                blur_score,
                config,
                current_time,
                dt,
            )
        else:
            state = self._state_from_flow(
                gray,
                quality_warnings,
                brightness_score,
                blur_score,
                config,
                current_time,
                dt,
            )

        self._prev_gray = gray
        self._last_update_at = current_time
        return state

    def _state_from_mediapipe(
        self,
        hand_result,
        frame,
        gray,
        quality_warnings: list[str],
        brightness_score: float,
        blur_score: float,
        config: dict,
        current_time: float,
        dt: float,
    ) -> HandState:
        hand = self._select_active_hand(hand_result)
        center = self._hand_center(hand)
        smoothed = self._smooth_center(center, config["ema_alpha"])
        velocity = self._velocity(smoothed, dt)
        self._last_center = center
        self._last_seen_at = current_time
        self._flow_confidence = 1.0
        self._prev_points = self._tracking_points(hand, frame)

        hand_near_edge = bool(center and self._is_near_edge(center))
        if hand_near_edge:
            quality_warnings.append("El kadraj kenarında")

        if hand and hand.confidence is not None and hand.confidence < 0.45:
            quality_warnings.append("El takibi kararsız")

        tracking_quality = self._tracking_quality(
            base_quality=1.0,
            quality_warnings=quality_warnings,
            confidence=hand.confidence if hand else None,
        )
        return HandState(
            hand_detected=True,
            tracking_source="mediapipe",
            active_hand=hand.handedness if hand else "-",
            hand_count=hand_result.hand_count,
            handedness=[item.handedness for item in hand_result.hands if item.handedness],
            hand_center=center,
            smoothed_hand_center=smoothed,
            hand_velocity=velocity,
            palm_open_score=1.0 if hand and self._is_open_hand(hand.landmarks) else 0.0,
            two_hand_score=self._two_hand_score(hand_result),
            tracking_quality=tracking_quality,
            missing_time=0.0,
            quality_warnings=quality_warnings,
            brightness_score=brightness_score,
            blur_score=blur_score,
            hand_near_edge=hand_near_edge,
        )

    def _state_from_flow(
        self,
        gray,
        quality_warnings: list[str],
        brightness_score: float,
        blur_score: float,
        config: dict,
        current_time: float,
        dt: float,
    ) -> HandState:
        missing_time = 0.0 if self._last_seen_at is None else current_time - self._last_seen_at
        if missing_time > config["missing_tolerance"] or self._prev_gray is None or self._prev_points is None:
            self._clear_tracking()
            return HandState(
                tracking_source="lost",
                missing_time=max(0.0, missing_time),
                quality_warnings=quality_warnings,
                brightness_score=brightness_score,
                blur_score=blur_score,
            )

        predicted_center = self._optical_flow_center(gray)
        if predicted_center is None:
            quality_warnings.append("El takibi kararsız")
            self._clear_tracking()
            return HandState(
                tracking_source="lost",
                missing_time=max(0.0, missing_time),
                quality_warnings=quality_warnings,
                brightness_score=brightness_score,
                blur_score=blur_score,
            )

        self._flow_confidence *= config["flow_decay"]
        if self._flow_confidence < config["min_flow_confidence"]:
            quality_warnings.append("El takibi kararsız")
            self._clear_tracking()
            return HandState(
                tracking_source="lost",
                missing_time=max(0.0, missing_time),
                quality_warnings=quality_warnings,
                brightness_score=brightness_score,
                blur_score=blur_score,
            )

        smoothed = self._smooth_center(predicted_center, config["ema_alpha"])
        velocity = self._velocity(smoothed, dt)
        self._last_center = predicted_center
        hand_near_edge = bool(predicted_center and self._is_near_edge(predicted_center))
        if hand_near_edge:
            quality_warnings.append("El kadraj kenarında")
        if self._flow_confidence < 0.45:
            quality_warnings.append("El takibi kararsız")

        return HandState(
            hand_detected=True,
            tracking_source="optical_flow",
            active_hand="-",
            hand_count=1,
            handedness=[],
            hand_center=predicted_center,
            smoothed_hand_center=smoothed,
            hand_velocity=velocity,
            palm_open_score=0.0,
            two_hand_score=0.0,
            tracking_quality=self._tracking_quality(self._flow_confidence, quality_warnings),
            missing_time=max(0.0, missing_time),
            quality_warnings=quality_warnings,
            brightness_score=brightness_score,
            blur_score=blur_score,
            hand_near_edge=hand_near_edge,
        )

    def _optical_flow_center(self, gray) -> tuple[float, float] | None:
        if gray is None:
            return None

        try:
            next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                self._prev_gray,
                gray,
                self._prev_points,
                None,
                winSize=(21, 21),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
            )
        except cv2.error:
            return None
        if next_points is None or status is None:
            return None

        tracked = next_points[status.reshape(-1) == 1]
        if len(tracked) < 3:
            return None

        self._prev_points = tracked.reshape(-1, 1, 2).astype(np.float32)
        height, width = gray.shape[:2]
        center_px = tracked.reshape(-1, 2).mean(axis=0)
        return (
            max(0.0, min(1.0, float(center_px[0]) / max(1, width))),
            max(0.0, min(1.0, float(center_px[1]) / max(1, height))),
        )

    def _select_active_hand(self, hand_result):
        hands = hand_result.hands or []
        if not hands:
            return None
        return max(hands, key=lambda hand: hand.confidence if hand.confidence is not None else 0.0)

    def _hand_center(self, hand) -> tuple[float, float] | None:
        if hand is None or len(hand.landmarks) < 18:
            return None
        points = [hand.landmarks[index] for index in self.STABLE_LANDMARKS]
        return (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )

    def _tracking_points(self, hand, frame):
        if hand is None or frame is None or len(hand.landmarks) < 18:
            return None
        height, width = frame.shape[:2]
        points = [
            [hand.landmarks[index][0] * width, hand.landmarks[index][1] * height]
            for index in self.STABLE_LANDMARKS
        ]
        return np.array(points, dtype=np.float32).reshape(-1, 1, 2)

    def _smooth_center(
        self,
        center: tuple[float, float] | None,
        alpha: float,
    ) -> tuple[float, float] | None:
        if center is None:
            return self._smoothed_center
        if self._smoothed_center is None:
            self._smoothed_center = center
        else:
            self._smoothed_center = (
                self._smoothed_center[0] * (1.0 - alpha) + center[0] * alpha,
                self._smoothed_center[1] * (1.0 - alpha) + center[1] * alpha,
            )
        return self._smoothed_center

    def _velocity(self, center: tuple[float, float] | None, dt: float) -> tuple[float, float] | None:
        if center is None or self._last_center is None:
            return None
        safe_dt = max(0.001, dt)
        return (
            (center[0] - self._last_center[0]) / safe_dt,
            (center[1] - self._last_center[1]) / safe_dt,
        )

    def _is_open_hand(self, landmarks) -> bool:
        if len(landmarks) < 21:
            return False
        palm_center = self._average_point([landmarks[index] for index in (0, 5, 9, 13, 17)])
        palm_width = self._distance(landmarks[5], landmarks[17])
        if palm_width <= 0:
            return False

        extended = 0
        for tip_index, base_index in zip((4, 8, 12, 16, 20), (2, 6, 10, 14, 18)):
            tip_distance = self._distance(landmarks[tip_index], palm_center)
            base_distance = self._distance(landmarks[base_index], palm_center)
            if tip_distance > base_distance + palm_width * 0.18:
                extended += 1
        return extended >= 4

    def _two_hand_score(self, hand_result) -> float:
        if not hand_result or not hand_result.hands or hand_result.hand_count < 2:
            return 0.0
        open_count = sum(1 for hand in hand_result.hands if self._is_open_hand(hand.landmarks))
        if open_count >= 2:
            return 1.0
        return min(0.5, hand_result.hand_count / 2)

    def _quality_scores(self, gray) -> tuple[float, float]:
        if gray is None:
            return 0.0, 0.0
        return (
            float(gray.mean()),
            float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        )

    def _quality_warnings(self, brightness: float, blur_score: float, config: dict) -> list[str]:
        warnings = []
        if brightness < config["min_brightness"]:
            warnings.append("Işık düşük")
        if blur_score < config["min_blur"]:
            warnings.append("Görüntü bulanık")
        return warnings

    def _tracking_quality(
        self,
        base_quality: float,
        quality_warnings: list[str],
        confidence: float | None = None,
    ) -> float:
        score = base_quality
        if confidence is not None:
            score = min(score, max(0.0, min(1.0, confidence)))
        score -= 0.18 * len(quality_warnings)
        return max(0.0, min(1.0, score))

    def _is_near_edge(self, center: tuple[float, float]) -> bool:
        x, y = center
        return x < 0.08 or x > 0.92 or y < 0.08 or y > 0.92

    def _to_gray(self, frame):
        if frame is None:
            return None
        if len(frame.shape) == 2:
            return frame
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _clear_tracking(self) -> None:
        self._prev_points = None
        self._last_center = None
        self._smoothed_center = None
        self._flow_confidence = 0.0

    def _delta_time(self, current_time: float) -> float:
        if self._last_update_at is None:
            return 0.0
        return current_time - self._last_update_at

    def _profile_config(self, detection_profile: str) -> dict:
        configs = {
            "Hassas": {
                "ema_alpha": 0.65,
                "missing_tolerance": 0.35,
                "flow_decay": 0.90,
                "min_flow_confidence": 0.18,
                "min_brightness": 38.0,
                "min_blur": 22.0,
            },
            "Dengeli": {
                "ema_alpha": 0.45,
                "missing_tolerance": 0.28,
                "flow_decay": 0.85,
                "min_flow_confidence": 0.25,
                "min_brightness": 45.0,
                "min_blur": 28.0,
            },
            "Kararlı": {
                "ema_alpha": 0.28,
                "missing_tolerance": 0.20,
                "flow_decay": 0.80,
                "min_flow_confidence": 0.34,
                "min_brightness": 55.0,
                "min_blur": 38.0,
            },
        }
        return configs.get(detection_profile, configs["Dengeli"])

    def _average_point(self, points) -> tuple[float, float, float]:
        count = len(points)
        return (
            sum(point[0] for point in points) / count,
            sum(point[1] for point in points) / count,
            sum(point[2] for point in points) / count,
        )

    def _distance(self, first, second) -> float:
        return math.hypot(first[0] - second[0], first[1] - second[1])
