# El landmark verisinden basit büyü tetikleme durumunu üretir.

from collections import deque
from dataclasses import dataclass
import math
import time

import cv2


@dataclass
class SpellResult:
    """Tek karelik büyü motoru sonucunu temsil eder."""

    has_active_spell: bool
    active_spell_name: str | None
    status: str
    is_on_cooldown: bool
    progress: float
    cooldown_remaining: float = 0.0
    message: str = ""
    palm_open_score: float = 0.0
    freeze_stability_score: float = 0.0
    fire_horizontal_distance: float = 0.0
    fire_swing_detected: bool = False
    shield_two_hand_score: float = 0.0
    spell_prepare_progress: float = 0.0
    locked_spell_attempt: str = ""
    fire_state: str = "idle"
    fire_start_x: float = 0.0
    fire_current_x: float = 0.0
    fire_required_distance: float = 0.0
    fire_travel_distance: float = 0.0
    fire_missing_time: float = 0.0
    fire_seal_window_active: bool = False
    hand_tracking_quality_message: str = ""
    spell_uses_tracker: bool = False
    tracker_source_used: str = "-"
    freeze_state: str = "idle"
    freeze_elapsed_time: float = 0.0
    freeze_required_time: float = 0.0
    freeze_progress_raw: float = 0.0
    freeze_progress_display: float = 0.0
    freeze_velocity: float = 0.0
    freeze_velocity_deadzone: float = 0.0
    freeze_is_stable: bool = False
    freeze_block_reason: str = "-"
    competing_spell_candidate: str = "-"
    fire_candidate_active: bool = False
    fire_start_reason: str = "-"
    fire_min_distance_met: bool = False


class SpellEngine:
    """İlk MVP büyü sistemi: Donma, Ateş ve Kalkan büyülerini üretir."""

    FREEZE_SPELL_NAME = "Donma"
    FIRE_SPELL_NAME = "Ateş"
    SHIELD_SPELL_NAME = "Kalkan"

    def __init__(
        self,
        freeze_hold_seconds: float = 0.8,
        shield_hold_seconds: float = 0.8,
        cooldown_seconds: float = 2.0,
        effect_seconds: float = 1.1,
        fire_history_seconds: float = 1.3,
        fire_seal_window_seconds: float = 0.8,
    ) -> None:
        self.status = "Ateş: yatay süpürme bekleniyor"
        self.freeze_hold_seconds = freeze_hold_seconds
        self.shield_hold_seconds = shield_hold_seconds
        self.cooldown_seconds = cooldown_seconds
        self.effect_seconds = effect_seconds
        self.fire_history_seconds = fire_history_seconds
        self.fire_seal_window_seconds = fire_seal_window_seconds
        self._freeze_started_at: float | None = None
        self._shield_started_at: float | None = None
        self._last_palm_center: tuple[float, float, float] | None = None
        self._hand_center_history: deque[tuple[float, tuple[float, float, float]]] = deque()
        self._fire_seal_until = 0.0
        self._fire_state = "idle"
        self._fire_start_x: float | None = None
        self._fire_start_y: float | None = None
        self._fire_current_x: float | None = None
        self._fire_started_at = 0.0
        self._fire_last_seen_at = 0.0
        self._cooldown_until = 0.0
        self._active_until = 0.0
        self._active_spell_name: str | None = None
        self._locked_message_until = 0.0
        self._locked_spell_attempt = ""
        self._palm_open_history: deque[bool] = deque(maxlen=10)
        self._two_hand_history: deque[bool] = deque(maxlen=10)
        self._two_open_hand_history: deque[bool] = deque(maxlen=10)
        self._freeze_missing_frames = 0
        self._debug_scores = self._empty_debug_scores()

    def update(
        self,
        hand_result,
        allowed_spells: list[str] | None = None,
        detection_profile: str = "Dengeli",
        now: float | None = None,
        frame=None,
        hand_state=None,
    ) -> SpellResult:
        """El algılama sonucuna göre büyü durumunu günceller."""
        current_time = now if now is not None else time.monotonic()
        profile = self._profile_config(detection_profile)
        self._update_tracking_quality(frame)
        tracker_center = self._tracker_center(hand_state)
        tracker_source = self._tracker_source(hand_state)
        tracker_quality = float(getattr(hand_state, "tracking_quality", 0.0) or 0.0)
        tracker_velocity = getattr(hand_state, "hand_velocity", None)
        tracker_is_motion_usable = (
            tracker_center is not None
            and tracker_source in {"mediapipe", "optical_flow"}
            and tracker_quality >= profile["tracker_min_quality"]
        )
        self._debug_scores["spell_uses_tracker"] = bool(tracker_is_motion_usable)
        self._debug_scores["tracker_source_used"] = tracker_source if tracker_is_motion_usable else "-"
        allowed_spells = allowed_spells or [
            self.FREEZE_SPELL_NAME,
            self.FIRE_SPELL_NAME,
            self.SHIELD_SPELL_NAME,
        ]

        if hand_result is not None and not hand_result.is_active:
            self._reset_gesture_state()
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="El algılama pasif",
                is_on_cooldown=False,
                progress=0.0,
            )

        if current_time < self._locked_message_until:
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Lonca yetkisi yetersiz",
                is_on_cooldown=False,
                progress=0.0,
                message="Büyü kilitli",
            )

        if current_time < self._active_until and self._active_spell_name:
            return self._result(
                has_active_spell=True,
                active_spell_name=self._active_spell_name,
                status=f"{self._active_spell_name} büyüsü aktif",
                is_on_cooldown=current_time < self._cooldown_until,
                progress=1.0,
                cooldown_remaining=max(0.0, self._cooldown_until - current_time),
            )

        self._active_spell_name = None

        if current_time < self._cooldown_until:
            self._reset_gesture_state()
            remaining = self._cooldown_until - current_time
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status=f"Bekleme süresi: {remaining:.1f} sn",
                is_on_cooldown=True,
                progress=0.0,
                cooldown_remaining=remaining,
            )

        hand_center = self._hand_center(hand_result)
        raw_open_palm_centers = self._open_palm_centers(hand_result)
        open_palm_center = raw_open_palm_centers[0] if raw_open_palm_centers else None
        self._update_smoothing_scores(hand_result, raw_open_palm_centers, profile)
        motion_center = tracker_center if tracker_is_motion_usable else hand_center
        motion_source = tracker_source if tracker_is_motion_usable else "mediapipe"
        if hand_center is None:
            if motion_center is not None:
                fire_motion_result = self._update_fire_spell(
                    current_time,
                    motion_center,
                    open_palm_center=None,
                    allowed_spells=allowed_spells,
                    profile=profile,
                    tracker_source=motion_source,
                )
                if fire_motion_result is not None:
                    return fire_motion_result

            fire_missing_result = self._update_fire_missing(current_time, profile)
            if fire_missing_result is not None:
                return fire_missing_result
            self._reset_gesture_state(keep_history=False)
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş: yatay süpürme bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        self._remember_hand_center(current_time, motion_center)

        shield_result = self._update_shield_spell(
            current_time,
            hand_result,
            raw_open_palm_centers,
            allowed_spells,
            profile,
        )
        if shield_result is not None:
            return shield_result

        fire_result = self._update_fire_spell(
            current_time,
            motion_center,
            open_palm_center,
            allowed_spells,
            profile,
            tracker_source=motion_source,
        )
        if fire_result is not None:
            return fire_result

        freeze_center = motion_center if motion_source == "mediapipe" else open_palm_center
        return self._update_freeze_spell(
            current_time,
            open_palm_center,
            allowed_spells,
            profile,
            stability_center=freeze_center,
            tracker_source=motion_source,
            tracker_velocity=tracker_velocity if tracker_is_motion_usable else None,
        )

    def list_available_spells(self, profile) -> list[str]:
        """Profilde açık olan büyüleri döndürür."""
        return profile.unlocked_spells

    def _update_shield_spell(
        self,
        current_time: float,
        hand_result,
        open_palm_centers: list[tuple[float, float, float]],
        allowed_spells: list[str],
        profile: dict,
    ) -> SpellResult | None:
        """İki açık el pozundan Kalkan büyüsünü üretir."""
        two_hands_visible = bool(hand_result and hand_result.hand_count >= 2)
        two_open_hands = len(open_palm_centers) >= 2
        shield_score = self._debug_scores["shield_two_hand_score"]

        if not two_hands_visible:
            self._shield_started_at = None
            return None

        self._debug_scores["competing_spell_candidate"] = self.SHIELD_SPELL_NAME
        self._freeze_started_at = None
        self._last_palm_center = None

        if not two_open_hands or shield_score < profile["shield_score_threshold"]:
            self._shield_started_at = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Kalkan mührü bekleniyor",
                is_on_cooldown=False,
                progress=min(0.5, shield_score),
            )

        if self._shield_started_at is None:
            self._shield_started_at = current_time

        held_seconds = current_time - self._shield_started_at
        progress = min(1.0, held_seconds / profile["shield_hold_seconds"])

        if progress >= 1.0:
            return self._activate_spell(self.SHIELD_SPELL_NAME, current_time, allowed_spells)

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Kalkan mührü bekleniyor",
            is_on_cooldown=False,
            progress=progress,
        )

    def _update_fire_spell(
        self,
        current_time: float,
        hand_center: tuple[float, float, float],
        open_palm_center: tuple[float, float, float] | None,
        allowed_spells: list[str],
        profile: dict,
        tracker_source: str = "mediapipe",
    ) -> SpellResult | None:
        """Kontrollü yatay süpürme + açık avuç zincirinden Ateş büyüsünü üretir."""
        self._fire_last_seen_at = current_time
        self._debug_scores["fire_missing_time"] = 0.0

        if self._fire_state == "idle":
            if tracker_source != "mediapipe":
                self._debug_scores["fire_candidate_active"] = False
                self._debug_scores["fire_start_reason"] = "optical_flow_başlatmaz"
                self._debug_scores["fire_min_distance_met"] = False
                return None
            fire_candidate = self._fire_start_candidate(profile)
            self._debug_scores["fire_candidate_active"] = fire_candidate["active"]
            self._debug_scores["fire_start_reason"] = fire_candidate["reason"]
            self._debug_scores["fire_min_distance_met"] = fire_candidate["min_distance_met"]
            if not fire_candidate["active"]:
                return None
            self._debug_scores["competing_spell_candidate"] = self.FIRE_SPELL_NAME
            self._start_fire_tracking(current_time, fire_candidate["start_center"] or hand_center)

        if self._fire_state == "fire_seal_window":
            self._update_fire_position(hand_center, profile, current_time)
            self._debug_scores["fire_seal_window_active"] = True
            self._debug_scores["fire_candidate_active"] = True
            self._debug_scores["competing_spell_candidate"] = self.FIRE_SPELL_NAME
            if current_time > self._fire_seal_until:
                self._reset_fire_state()
                return None

            remaining = max(0.0, self._fire_seal_until - current_time)
            progress = 0.75 + 0.25 * (
                1.0 - remaining / profile["fire_seal_window_seconds"]
            )
            self._freeze_started_at = None
            self._last_palm_center = None

            if (
                tracker_source == "mediapipe"
                and open_palm_center is not None
                and self._debug_scores["palm_open_score"] >= profile["palm_score_threshold"]
            ):
                self._fire_state = "triggered"
                self._debug_scores["fire_state"] = "triggered"
                return self._activate_spell(self.FIRE_SPELL_NAME, current_time, allowed_spells)

            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş mührü: avuç göster",
                is_on_cooldown=False,
                progress=progress,
            )

        self._update_fire_position(hand_center, profile, current_time)
        self._debug_scores["fire_candidate_active"] = True
        self._debug_scores["competing_spell_candidate"] = self.FIRE_SPELL_NAME
        elapsed = current_time - self._fire_started_at
        required_distance = profile["fire_sweep_distance"]
        travel_distance = self._debug_scores["fire_travel_distance"]

        if elapsed > profile["fire_tracking_timeout_seconds"] and travel_distance < required_distance:
            if tracker_source != "mediapipe":
                return self._update_fire_missing(current_time, profile)
            self._start_fire_tracking(current_time, hand_center)
            return None

        if travel_distance >= required_distance:
            self._fire_state = "fire_seal_window"
            self._fire_seal_until = current_time + profile["fire_seal_window_seconds"]
            self._debug_scores["fire_swing_detected"] = True
            self._debug_scores["fire_state"] = self._fire_state
            self._debug_scores["fire_seal_window_active"] = True
            self._freeze_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş mührü: avuç göster",
                is_on_cooldown=False,
                progress=0.75,
            )

        progress = min(0.70, travel_distance / required_distance * 0.70)
        if progress >= profile["fire_visible_progress"]:
            self._freeze_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş: yatay süpürme",
                is_on_cooldown=False,
                progress=progress,
            )

        return None

    def _update_fire_missing(self, current_time: float, profile: dict) -> SpellResult | None:
        """Kısa el kayıplarında Ateş hazırlığını hemen sıfırlamadan korur."""
        if self._fire_state not in {"fire_tracking_sweep", "fire_seal_window"}:
            return None
        if self._fire_last_seen_at <= 0:
            self._reset_fire_state()
            return None

        missing_time = current_time - self._fire_last_seen_at
        self._debug_scores["fire_missing_time"] = max(0.0, missing_time)
        self._debug_scores["fire_state"] = self._fire_state
        self._debug_scores["fire_seal_window_active"] = self._fire_state == "fire_seal_window"
        if missing_time <= profile["fire_missing_tolerance_seconds"]:
            status = (
                "Ateş mührü: avuç göster"
                if self._fire_state == "fire_seal_window"
                else "Ateş: yatay süpürme"
            )
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status=status,
                is_on_cooldown=False,
                progress=self._fire_progress(profile),
            )

        self._reset_fire_state()
        return None

    def _update_freeze_spell(
        self,
        current_time: float,
        open_palm_center: tuple[float, float, float] | None,
        allowed_spells: list[str],
        profile: dict,
        stability_center: tuple[float, float, float] | None = None,
        tracker_source: str = "mediapipe",
        tracker_velocity=None,
    ) -> SpellResult:
        """Açık ve kısa süre sabit avuçtan Donma büyüsünü üretir."""
        palm_score = self._debug_scores["palm_open_score"]
        self._debug_scores["freeze_required_time"] = profile["freeze_hold_seconds"]
        self._debug_scores["freeze_velocity_deadzone"] = profile["freeze_velocity_deadzone"]
        self._debug_scores["competing_spell_candidate"] = "-"
        raw_palm_ready = open_palm_center is not None and tracker_source == "mediapipe"
        if not raw_palm_ready or palm_score < profile["palm_score_threshold"]:
            self._freeze_missing_frames += 1
            self._debug_scores["freeze_state"] = "waiting"
            self._debug_scores["freeze_block_reason"] = (
                "raw_avuç_yok" if not raw_palm_ready else "palm_score_düşük"
            )
            self._debug_scores["freeze_is_stable"] = False
            if self._freeze_missing_frames > profile["freeze_missing_tolerance"]:
                self._freeze_started_at = None
                self._last_palm_center = None
            held_seconds = 0.0
            if self._freeze_started_at is not None:
                held_seconds = max(0.0, current_time - self._freeze_started_at)
            raw_progress = min(1.0, held_seconds / profile["freeze_hold_seconds"])
            display_progress = min(raw_progress, palm_score * 0.60)
            self._debug_scores["freeze_elapsed_time"] = held_seconds
            self._debug_scores["freeze_progress_raw"] = raw_progress
            self._debug_scores["freeze_progress_display"] = display_progress
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş: yatay süpürme bekleniyor",
                is_on_cooldown=False,
                progress=display_progress,
            )

        self._freeze_missing_frames = 0
        stability_center = stability_center or open_palm_center
        stability_score = 1.0
        if (
            self._last_palm_center is not None
            and self._distance(stability_center, self._last_palm_center) > profile["freeze_stability_distance"]
        ):
            stability_score = 0.0
            self._freeze_started_at = current_time

        tracker_speed = self._tracker_speed(tracker_velocity)
        effective_speed = 0.0
        if tracker_source == "mediapipe" and tracker_speed is not None:
            effective_speed = max(0.0, tracker_speed - profile["freeze_velocity_deadzone"])
            velocity_range = max(
                0.001,
                profile["freeze_velocity_limit"] - profile["freeze_velocity_deadzone"],
            )
            velocity_score = max(0.0, 1.0 - effective_speed / velocity_range)
            stability_score = min(stability_score, velocity_score)
            if effective_speed > velocity_range:
                self._freeze_started_at = current_time

        self._debug_scores["freeze_stability_score"] = stability_score
        self._debug_scores["freeze_velocity"] = effective_speed
        self._last_palm_center = stability_center

        if self._freeze_started_at is None:
            self._freeze_started_at = current_time

        held_seconds = current_time - self._freeze_started_at
        raw_progress = min(1.0, held_seconds / profile["freeze_hold_seconds"])
        is_stable = stability_score >= profile["freeze_stability_threshold"]
        quality_cap = 1.0 if is_stable else (palm_score + max(stability_score, 0.80)) / 2
        display_progress = min(raw_progress, quality_cap)
        self._debug_scores["freeze_state"] = "charging"
        self._debug_scores["freeze_elapsed_time"] = held_seconds
        self._debug_scores["freeze_progress_raw"] = raw_progress
        self._debug_scores["freeze_progress_display"] = display_progress
        self._debug_scores["freeze_is_stable"] = is_stable
        self._debug_scores["freeze_block_reason"] = "-" if is_stable else "hareketli"

        if (
            held_seconds >= profile["freeze_hold_seconds"] * profile["freeze_trigger_ratio"]
            and palm_score >= profile["palm_score_threshold"]
            and is_stable
        ):
            self._debug_scores["freeze_state"] = "triggered"
            self._debug_scores["freeze_progress_display"] = 1.0
            return self._activate_spell(self.FREEZE_SPELL_NAME, current_time, allowed_spells)

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Avuç mührü hazırlanıyor",
            is_on_cooldown=False,
            progress=display_progress,
        )

    def _activate_spell(
        self,
        spell_name: str,
        current_time: float,
        allowed_spells: list[str],
    ) -> SpellResult:
        """Büyüyü aktif eder ve ortak cooldown başlatır."""
        fire_debug_snapshot = None
        if spell_name == self.FIRE_SPELL_NAME:
            fire_debug_snapshot = {
                key: self._debug_scores[key]
                for key in (
                    "fire_start_x",
                    "fire_current_x",
                    "fire_required_distance",
                    "fire_travel_distance",
                    "fire_horizontal_distance",
                )
            }
        self._reset_gesture_state()
        if fire_debug_snapshot:
            self._debug_scores.update(fire_debug_snapshot)
            self._debug_scores["fire_state"] = "triggered"
            self._debug_scores["fire_swing_detected"] = True
            self._debug_scores["fire_seal_window_active"] = False
        if spell_name not in allowed_spells:
            self._locked_message_until = current_time + 1.2
            self._locked_spell_attempt = spell_name
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Lonca yetkisi yetersiz",
                is_on_cooldown=False,
                progress=0.0,
                message="Büyü kilitli",
            )

        self._active_spell_name = spell_name
        self._locked_spell_attempt = ""
        self._active_until = current_time + self.effect_seconds
        self._cooldown_until = current_time + self.cooldown_seconds
        return self._result(
            has_active_spell=True,
            active_spell_name=spell_name,
            status=f"{spell_name} büyüsü aktif",
            is_on_cooldown=True,
            progress=1.0,
            cooldown_remaining=self.cooldown_seconds,
        )

    def _result(
        self,
        has_active_spell: bool,
        active_spell_name: str | None,
        status: str,
        is_on_cooldown: bool,
        progress: float,
        cooldown_remaining: float = 0.0,
        message: str = "",
    ) -> SpellResult:
        """Sonucu saklar ve çağırana döndürür."""
        self.status = status
        return SpellResult(
            has_active_spell=has_active_spell,
            active_spell_name=active_spell_name,
            status=status,
            is_on_cooldown=is_on_cooldown,
            progress=max(0.0, min(1.0, progress)),
            cooldown_remaining=max(0.0, cooldown_remaining),
            message=message,
            palm_open_score=self._debug_scores["palm_open_score"],
            freeze_stability_score=self._debug_scores["freeze_stability_score"],
            fire_horizontal_distance=self._debug_scores["fire_horizontal_distance"],
            fire_swing_detected=self._debug_scores["fire_swing_detected"],
            shield_two_hand_score=self._debug_scores["shield_two_hand_score"],
            spell_prepare_progress=max(0.0, min(1.0, progress)),
            locked_spell_attempt=self._locked_spell_attempt,
            fire_state=self._debug_scores["fire_state"],
            fire_start_x=self._debug_scores["fire_start_x"],
            fire_current_x=self._debug_scores["fire_current_x"],
            fire_required_distance=self._debug_scores["fire_required_distance"],
            fire_travel_distance=self._debug_scores["fire_travel_distance"],
            fire_missing_time=self._debug_scores["fire_missing_time"],
            fire_seal_window_active=self._debug_scores["fire_seal_window_active"],
            hand_tracking_quality_message=self._debug_scores["hand_tracking_quality_message"],
            spell_uses_tracker=self._debug_scores["spell_uses_tracker"],
            tracker_source_used=self._debug_scores["tracker_source_used"],
            freeze_state=self._debug_scores["freeze_state"],
            freeze_elapsed_time=self._debug_scores["freeze_elapsed_time"],
            freeze_required_time=self._debug_scores["freeze_required_time"],
            freeze_progress_raw=self._debug_scores["freeze_progress_raw"],
            freeze_progress_display=self._debug_scores["freeze_progress_display"],
            freeze_velocity=self._debug_scores["freeze_velocity"],
            freeze_velocity_deadzone=self._debug_scores["freeze_velocity_deadzone"],
            freeze_is_stable=self._debug_scores["freeze_is_stable"],
            freeze_block_reason=self._debug_scores["freeze_block_reason"],
            competing_spell_candidate=self._debug_scores["competing_spell_candidate"],
            fire_candidate_active=self._debug_scores["fire_candidate_active"],
            fire_start_reason=self._debug_scores["fire_start_reason"],
            fire_min_distance_met=self._debug_scores["fire_min_distance_met"],
        )

    def _remember_hand_center(
        self,
        current_time: float,
        hand_center: tuple[float, float, float],
    ) -> None:
        """Son el merkezi geçmişini zaman penceresi içinde tutar."""
        self._hand_center_history.append((current_time, hand_center))
        min_time = current_time - self.fire_history_seconds
        while self._hand_center_history and self._hand_center_history[0][0] < min_time:
            self._hand_center_history.popleft()

    def _has_horizontal_swipe(self, profile: dict) -> bool:
        """Küçük titreşimleri dışlayarak belirgin yatay savurma arar."""
        self._debug_scores["fire_horizontal_distance"] = self._horizontal_swipe_distance()
        self._debug_scores["fire_swing_detected"] = False
        if len(self._hand_center_history) < 5:
            return False

        first_time, first_center = self._hand_center_history[0]
        last_time, last_center = self._hand_center_history[-1]
        elapsed = last_time - first_time
        if elapsed < profile["fire_min_elapsed"]:
            return False

        horizontal_delta = abs(last_center[0] - first_center[0])
        vertical_delta = abs(last_center[1] - first_center[1])
        self._debug_scores["fire_horizontal_distance"] = horizontal_delta

        if horizontal_delta < profile["fire_min_horizontal_distance"]:
            return False

        if vertical_delta > profile["fire_max_vertical_distance"]:
            return False

        return horizontal_delta > vertical_delta * profile["fire_direction_ratio"]

    def _horizontal_swipe_distance(self) -> float:
        """Debug için mevcut el geçmişindeki yatay mesafeyi döndürür."""
        if len(self._hand_center_history) < 2:
            return 0.0
        return abs(self._hand_center_history[-1][1][0] - self._hand_center_history[0][1][0])

    def _fire_start_candidate(self, profile: dict) -> dict:
        """Ateş state'ini başlatmak için yeterli yatay hareket olup olmadığını döndürür."""
        result = {
            "active": False,
            "min_distance_met": False,
            "reason": "yetersiz_geçmiş",
            "start_center": None,
        }
        if len(self._hand_center_history) < 3:
            return result

        current_time, current_center = self._hand_center_history[-1]
        best_center = None
        best_horizontal = 0.0
        best_vertical = 0.0
        best_elapsed = 0.0
        for previous_time, previous_center in self._hand_center_history:
            elapsed = current_time - previous_time
            if elapsed < profile["fire_start_min_elapsed"]:
                continue
            horizontal = abs(current_center[0] - previous_center[0])
            vertical = abs(current_center[1] - previous_center[1])
            if horizontal > best_horizontal:
                best_horizontal = horizontal
                best_vertical = vertical
                best_elapsed = elapsed
                best_center = previous_center

        self._debug_scores["fire_horizontal_distance"] = best_horizontal
        result["min_distance_met"] = best_horizontal >= profile["fire_start_min_distance"]
        if not result["min_distance_met"]:
            result["reason"] = "küçük_hareket"
            return result

        if best_elapsed < profile["fire_start_min_elapsed"]:
            result["reason"] = "çok_kısa"
            return result

        if best_vertical > profile["fire_max_vertical_distance"]:
            result["reason"] = "dikey_sapma"
            return result

        if best_horizontal <= best_vertical * profile["fire_direction_ratio"]:
            result["reason"] = "yatay_yön_zayıf"
            return result

        result["active"] = True
        result["reason"] = "belirgin_yatay_süpürme"
        result["start_center"] = best_center
        return result

    def _start_fire_tracking(
        self,
        current_time: float,
        hand_center: tuple[float, float, float],
    ) -> None:
        """Ateş için kontrollü yatay süpürme takibini başlatır."""
        self._fire_state = "fire_tracking_sweep"
        self._fire_start_x = hand_center[0]
        self._fire_start_y = hand_center[1]
        self._fire_current_x = hand_center[0]
        self._fire_started_at = current_time
        self._fire_last_seen_at = current_time
        self._fire_seal_until = 0.0
        self._debug_scores["fire_state"] = self._fire_state
        self._debug_scores["fire_start_x"] = self._fire_start_x
        self._debug_scores["fire_current_x"] = self._fire_current_x
        self._debug_scores["fire_travel_distance"] = 0.0
        self._debug_scores["fire_horizontal_distance"] = 0.0
        self._debug_scores["fire_missing_time"] = 0.0
        self._debug_scores["fire_swing_detected"] = False
        self._debug_scores["fire_seal_window_active"] = False
        self._debug_scores["fire_candidate_active"] = False
        self._debug_scores["fire_start_reason"] = "-"
        self._debug_scores["fire_min_distance_met"] = False

    def _update_fire_position(
        self,
        hand_center: tuple[float, float, float],
        profile: dict,
        current_time: float,
    ) -> None:
        """Ateş süpürmesindeki güncel yatay ilerlemeyi debug skorlarına yazar."""
        if self._fire_start_x is None or self._fire_start_y is None:
            return

        vertical_drift = abs(hand_center[1] - self._fire_start_y)
        if (
            vertical_drift > profile["fire_max_vertical_distance"]
            and self._debug_scores["fire_travel_distance"] < profile["fire_sweep_distance"] * 0.45
        ):
            self._start_fire_tracking(current_time, hand_center)
            return

        self._fire_current_x = hand_center[0]
        travel_distance = abs(self._fire_current_x - self._fire_start_x)
        self._debug_scores["fire_state"] = self._fire_state
        self._debug_scores["fire_start_x"] = self._fire_start_x
        self._debug_scores["fire_current_x"] = self._fire_current_x
        self._debug_scores["fire_required_distance"] = profile["fire_sweep_distance"]
        self._debug_scores["fire_travel_distance"] = travel_distance
        self._debug_scores["fire_horizontal_distance"] = travel_distance
        self._debug_scores["fire_seal_window_active"] = self._fire_state == "fire_seal_window"

    def _fire_progress(self, profile: dict) -> float:
        """Ateş hazırlık ilerlemesini normalize eder."""
        required_distance = max(0.001, profile["fire_sweep_distance"])
        progress = self._debug_scores["fire_travel_distance"] / required_distance * 0.70
        if self._fire_state == "fire_seal_window":
            progress = max(0.75, progress)
        return max(0.0, min(1.0, progress))

    def _reset_fire_state(self) -> None:
        """Ateş süpürme durum makinesini temizler."""
        self._fire_state = "idle"
        self._fire_start_x = None
        self._fire_start_y = None
        self._fire_current_x = None
        self._fire_started_at = 0.0
        self._fire_last_seen_at = 0.0
        self._fire_seal_until = 0.0
        self._debug_scores["fire_state"] = "idle"
        self._debug_scores["fire_start_x"] = 0.0
        self._debug_scores["fire_current_x"] = 0.0
        self._debug_scores["fire_required_distance"] = 0.0
        self._debug_scores["fire_travel_distance"] = 0.0
        self._debug_scores["fire_horizontal_distance"] = 0.0
        self._debug_scores["fire_missing_time"] = 0.0
        self._debug_scores["fire_swing_detected"] = False
        self._debug_scores["fire_seal_window_active"] = False

    def _hand_center(self, hand_result) -> tuple[float, float, float] | None:
        """Algılanan ilk elin yaklaşık merkez noktasını döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return None

        landmarks = hand_result.hands[0].landmarks
        if len(landmarks) < 21:
            return None

        center_indices = [0, 5, 9, 13, 17]
        return self._average_point([landmarks[index] for index in center_indices])

    def _tracker_center(self, hand_state) -> tuple[float, float, float] | None:
        """Tracker merkezini büyü motorunun 3B normalize nokta formatına çevirir."""
        center = getattr(hand_state, "smoothed_hand_center", None)
        if center is None:
            return None
        return (float(center[0]), float(center[1]), 0.0)

    def _tracker_source(self, hand_state) -> str:
        """Tracker kaynağını debug ve güvenli kararlar için döndürür."""
        return str(getattr(hand_state, "tracking_source", "-") or "-")

    def _tracker_speed(self, velocity) -> float | None:
        """Tracker hız vektörünü normalize 2B hız büyüklüğüne çevirir."""
        if velocity is None:
            return None
        return math.hypot(float(velocity[0]), float(velocity[1]))

    def _open_palm_center(self, hand_result) -> tuple[float, float, float] | None:
        """Açık ve kullanılabilir ilk avucun merkez noktasını döndürür."""
        centers = self._open_palm_centers(hand_result)
        return centers[0] if centers else None

    def _open_palm_centers(self, hand_result) -> list[tuple[float, float, float]]:
        """Açık ve kullanılabilir avuç merkezlerini döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return []

        centers: list[tuple[float, float, float]] = []
        for hand in hand_result.hands:
            if self._is_open_hand(hand.landmarks):
                palm_indices = [0, 5, 9, 13, 17]
                centers.append(self._average_point([hand.landmarks[index] for index in palm_indices]))

        return centers

    def _is_open_hand(self, landmarks: list[tuple[float, float, float]]) -> bool:
        """Parmak uçları avuç merkezinden yeterince açıksa eli açık kabul eder."""
        if len(landmarks) < 21:
            return False

        palm_indices = [0, 5, 9, 13, 17]
        palm_center = self._average_point([landmarks[index] for index in palm_indices])
        palm_width = self._distance(landmarks[5], landmarks[17])
        if palm_width <= 0:
            return False

        fingertip_indices = [4, 8, 12, 16, 20]
        finger_base_indices = [2, 6, 10, 14, 18]
        extended_fingers = 0

        for tip_index, base_index in zip(fingertip_indices, finger_base_indices):
            tip_distance = self._distance(landmarks[tip_index], palm_center)
            base_distance = self._distance(landmarks[base_index], palm_center)
            if tip_distance > base_distance + palm_width * 0.18:
                extended_fingers += 1

        return extended_fingers >= 4

    def _update_smoothing_scores(self, hand_result, open_palm_centers, profile: dict) -> None:
        """Tek karelik el kararlarını kısa geçmiş skorlarına dönüştürür."""
        hand_detected = bool(hand_result and hand_result.detected and hand_result.hands)
        two_hands_visible = bool(hand_result and hand_result.hand_count >= 2)
        palm_open = hand_detected and len(open_palm_centers) >= 1
        two_open_hands = two_hands_visible and len(open_palm_centers) >= 2

        self._palm_open_history.append(palm_open)
        self._two_hand_history.append(two_hands_visible)
        self._two_open_hand_history.append(two_open_hands)

        self._debug_scores["palm_open_score"] = self._history_score(self._palm_open_history)
        two_hand_score = self._history_score(self._two_hand_history)
        two_open_score = self._history_score(self._two_open_hand_history)
        self._debug_scores["shield_two_hand_score"] = min(two_hand_score, two_open_score)

    def _history_score(self, history: deque[bool]) -> float:
        """Boolean geçmişten 0-1 arası oran döndürür."""
        if not history:
            return 0.0
        return sum(1 for item in history if item) / len(history)

    def _update_tracking_quality(self, frame) -> None:
        """El takibini etkileyebilecek basit ışık ve bulanıklık uyarılarını üretir."""
        self._debug_scores["hand_tracking_quality_message"] = ""
        if frame is None:
            return

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            brightness = float(gray.mean())
            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except cv2.error:
            return

        if brightness < 45.0:
            self._debug_scores["hand_tracking_quality_message"] = "Işık düşük: el takibi zayıflayabilir"
        elif blur_score < 28.0:
            self._debug_scores["hand_tracking_quality_message"] = "Görüntü bulanık: eli biraz yavaşlat"

    def _profile_config(self, detection_profile: str) -> dict:
        """Algılama profiline göre büyü karar eşiklerini döndürür."""
        configs = {
            "Hassas": {
                "palm_score_threshold": 0.45,
                "shield_score_threshold": 0.45,
                "freeze_hold_seconds": 0.65,
                "shield_hold_seconds": 0.65,
                "freeze_stability_distance": 0.10,
                "freeze_stability_threshold": 0.65,
                "freeze_trigger_ratio": 0.95,
                "freeze_velocity_deadzone": 0.18,
                "freeze_missing_tolerance": 4,
                "fire_min_elapsed": 0.16,
                "fire_start_min_elapsed": 0.10,
                "fire_start_min_distance": 0.075,
                "fire_min_horizontal_distance": 0.18,
                "fire_max_vertical_distance": 0.22,
                "fire_direction_ratio": 1.45,
                "fire_seal_window_seconds": 0.95,
                "fire_sweep_distance": 0.16,
                "fire_visible_progress": 0.12,
                "fire_missing_tolerance_seconds": 0.35,
                "fire_tracking_timeout_seconds": 2.2,
                "tracker_min_quality": 0.12,
                "freeze_velocity_limit": 0.70,
            },
            "Dengeli": {
                "palm_score_threshold": 0.58,
                "shield_score_threshold": 0.58,
                "freeze_hold_seconds": self.freeze_hold_seconds,
                "shield_hold_seconds": self.shield_hold_seconds,
                "freeze_stability_distance": 0.08,
                "freeze_stability_threshold": 0.72,
                "freeze_trigger_ratio": 0.95,
                "freeze_velocity_deadzone": 0.14,
                "freeze_missing_tolerance": 3,
                "fire_min_elapsed": 0.18,
                "fire_start_min_elapsed": 0.12,
                "fire_start_min_distance": 0.10,
                "fire_min_horizontal_distance": 0.22,
                "fire_max_vertical_distance": 0.18,
                "fire_direction_ratio": 1.8,
                "fire_seal_window_seconds": self.fire_seal_window_seconds,
                "fire_sweep_distance": 0.21,
                "fire_visible_progress": 0.15,
                "fire_missing_tolerance_seconds": 0.28,
                "fire_tracking_timeout_seconds": 1.9,
                "tracker_min_quality": 0.18,
                "freeze_velocity_limit": 0.50,
            },
            "Kararlı": {
                "palm_score_threshold": 0.72,
                "shield_score_threshold": 0.72,
                "freeze_hold_seconds": 0.95,
                "shield_hold_seconds": 0.95,
                "freeze_stability_distance": 0.055,
                "freeze_stability_threshold": 0.80,
                "freeze_trigger_ratio": 0.97,
                "freeze_velocity_deadzone": 0.10,
                "freeze_missing_tolerance": 2,
                "fire_min_elapsed": 0.22,
                "fire_start_min_elapsed": 0.15,
                "fire_start_min_distance": 0.13,
                "fire_min_horizontal_distance": 0.28,
                "fire_max_vertical_distance": 0.14,
                "fire_direction_ratio": 2.2,
                "fire_seal_window_seconds": 0.65,
                "fire_sweep_distance": 0.27,
                "fire_visible_progress": 0.18,
                "fire_missing_tolerance_seconds": 0.20,
                "fire_tracking_timeout_seconds": 1.5,
                "tracker_min_quality": 0.25,
                "freeze_velocity_limit": 0.35,
            },
        }
        return configs.get(detection_profile, configs["Dengeli"])

    def _empty_debug_scores(self) -> dict:
        """Büyü karar debug skorlarının varsayılanlarını döndürür."""
        return {
            "palm_open_score": 0.0,
            "freeze_stability_score": 0.0,
            "fire_horizontal_distance": 0.0,
            "fire_swing_detected": False,
            "shield_two_hand_score": 0.0,
            "fire_state": "idle",
            "fire_start_x": 0.0,
            "fire_current_x": 0.0,
            "fire_required_distance": 0.0,
            "fire_travel_distance": 0.0,
            "fire_missing_time": 0.0,
            "fire_seal_window_active": False,
            "hand_tracking_quality_message": "",
            "spell_uses_tracker": False,
            "tracker_source_used": "-",
            "freeze_state": "idle",
            "freeze_elapsed_time": 0.0,
            "freeze_required_time": 0.0,
            "freeze_progress_raw": 0.0,
            "freeze_progress_display": 0.0,
            "freeze_velocity": 0.0,
            "freeze_velocity_deadzone": 0.0,
            "freeze_is_stable": False,
            "freeze_block_reason": "-",
            "competing_spell_candidate": "-",
            "fire_candidate_active": False,
            "fire_start_reason": "-",
            "fire_min_distance_met": False,
        }

    def _reset_gesture_state(self, keep_history: bool = True) -> None:
        """Devam eden büyü hazırlık durumlarını temizler."""
        self._freeze_started_at = None
        self._shield_started_at = None
        self._last_palm_center = None
        self._reset_fire_state()
        self._freeze_missing_frames = 0
        if not keep_history:
            self._hand_center_history.clear()
            self._palm_open_history.clear()
            self._two_hand_history.clear()
            self._two_open_hand_history.clear()
            self._debug_scores = self._empty_debug_scores()

    def _average_point(self, points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
        """Verilen noktaların ortalamasını döndürür."""
        count = len(points)
        return (
            sum(point[0] for point in points) / count,
            sum(point[1] for point in points) / count,
            sum(point[2] for point in points) / count,
        )

    def _distance(self, first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
        """İki normalize landmark noktası arasındaki 2B mesafeyi hesaplar."""
        return math.hypot(first[0] - second[0], first[1] - second[1])
