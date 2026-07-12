# Kamera karesinde el landmark noktalarını MediaPipe Tasks ile algılayan modül.

from dataclasses import dataclass
from pathlib import Path
import time

import cv2

from runtime_paths import static_resource_path

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision
except ImportError as import_error:
    mp = None
    mp_tasks = None
    vision = None
    _MEDIAPIPE_IMPORT_ERROR = import_error
else:
    _MEDIAPIPE_IMPORT_ERROR = None


@dataclass
class HandData:
    """Algılanan tek ele ait temel landmark bilgisini temsil eder."""

    handedness: str
    confidence: float | None
    landmarks: list[tuple[float, float, float]]


@dataclass
class HandDetectionResult:
    """Tek karelik el algılama sonucunu temsil eder."""

    detected: bool
    hand_count: int = 0
    hands: list[HandData] | None = None
    is_active: bool = True
    message: str = ""


class HandDetectorError(RuntimeError):
    """El algılama modülü başlatılamadığında kullanılan anlaşılır hata."""


class HandDetector:
    """MediaPipe Tasks Hand Landmarker ile kamera karesinde el landmarkları algılar."""

    MODEL_MISSING_MESSAGE = "MediaPipe hand model bulunamadı, el algılama pasif."

    def __init__(
        self,
        model_path: str | None = None,
        num_hands: int = 2,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.name = "HandDetector"
        self.model_path = Path(model_path) if model_path else self._default_model_path()
        self.num_hands = num_hands
        self.min_hand_detection_confidence = min_hand_detection_confidence
        self.min_hand_presence_confidence = min_hand_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._landmarker = None
        self._last_timestamp_ms = 0
        self.is_available = False
        self.is_ready = False
        self.warning_message = ""
        self.initialize()

    def initialize(self) -> None:
        """MediaPipe Tasks Hand Landmarker modelini hazırlar."""
        if mp is None or mp_tasks is None or vision is None:
            self._disable("MediaPipe Tasks API yüklenemedi, el algılama pasif.")
            return

        if not self.model_path.exists():
            self._disable(self.MODEL_MISSING_MESSAGE)
            return

        try:
            base_options = mp_tasks.BaseOptions(model_asset_path=str(self.model_path))
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.num_hands,
                min_hand_detection_confidence=self.min_hand_detection_confidence,
                min_hand_presence_confidence=self.min_hand_presence_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self._landmarker = vision.HandLandmarker.create_from_options(options)
        except Exception as error:
            self._disable(f"MediaPipe hand landmarker başlatılamadı, el algılama pasif: {error}")
            return

        self.is_available = True
        self.is_ready = True
        self.warning_message = ""

    def detect(self, frame) -> HandDetectionResult:
        """Verilen BGR kamera karesinde el landmark noktalarını arar."""
        if not self.is_available or self._landmarker is None:
            return HandDetectionResult(
                detected=False,
                hand_count=0,
                hands=[],
                is_active=False,
                message=self.warning_message,
            )

        if frame is None:
            return HandDetectionResult(detected=False, hand_count=0, hands=[], is_active=True)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        try:
            landmarker_result = self._landmarker.detect_for_video(
                mp_image,
                self._next_timestamp_ms(),
            )
        except Exception as error:
            self._disable(f"MediaPipe hand landmarker çalışırken hata verdi, el algılama pasif: {error}")
            return HandDetectionResult(
                detected=False,
                hand_count=0,
                hands=[],
                is_active=False,
                message=self.warning_message,
            )

        hands = self._hands_from_result(landmarker_result)
        return HandDetectionResult(
            detected=len(hands) > 0,
            hand_count=len(hands),
            hands=hands,
            is_active=True,
        )

    def close(self) -> None:
        """MediaPipe landmarker kaynağını temizler."""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

        self.is_available = False
        self.is_ready = False

    def _disable(self, message: str) -> None:
        """El algılamayı uygulamayı çökertmeden pasif hale getirir."""
        self._landmarker = None
        self.is_available = False
        self.is_ready = True
        self.warning_message = message

    def _default_model_path(self) -> Path:
        """Varsayılan MediaPipe el modeli dosyası yolunu döndürür."""
        return static_resource_path("models", "hand_landmarker.task")

    def _next_timestamp_ms(self) -> int:
        """VIDEO modu için sürekli artan kare zaman damgası üretir."""
        timestamp_ms = int(time.monotonic() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms

    def _hands_from_result(self, landmarker_result) -> list[HandData]:
        """MediaPipe sonucunu VisionForge içi sade veri yapısına çevirir."""
        hand_landmarks = getattr(landmarker_result, "hand_landmarks", None) or []
        handedness = getattr(landmarker_result, "handedness", None) or []
        hands: list[HandData] = []

        for index, landmarks in enumerate(hand_landmarks):
            landmark_points = [
                (
                    float(getattr(landmark, "x", 0.0)),
                    float(getattr(landmark, "y", 0.0)),
                    float(getattr(landmark, "z", 0.0)),
                )
                for landmark in landmarks
            ]

            if len(landmark_points) != 21:
                continue

            label, confidence = self._handedness_from_result(handedness, index)
            hands.append(
                HandData(
                    handedness=label,
                    confidence=confidence,
                    landmarks=landmark_points,
                )
            )

        return hands

    def _handedness_from_result(self, handedness, index: int) -> tuple[str, float | None]:
        """Sağ/sol el bilgisini ve yaklaşık güven skorunu okur."""
        if len(handedness) <= index or not handedness[index]:
            return "Bilinmiyor", None

        category = handedness[index][0]
        label = (
            getattr(category, "category_name", None)
            or getattr(category, "display_name", None)
            or "Bilinmiyor"
        )
        score = getattr(category, "score", None)
        return str(label), float(score) if score is not None else None
