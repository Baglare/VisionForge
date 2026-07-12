# Kamera karesinde yüz olup olmadığını MediaPipe Tasks ile algılayan modül.

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
class FaceDetectionResult:
    """Tek karelik yüz algılama sonucunu temsil eder."""

    detected: bool
    confidence: float | None = None
    box: tuple[int, int, int, int] | None = None
    is_active: bool = True
    message: str = ""


class FaceDetectorError(RuntimeError):
    """Yüz algılama modülü başlatılamadığında kullanılan anlaşılır hata."""


class FaceDetector:
    """MediaPipe Tasks Face Detector ile kamera karesinde yüz var/yok algılar."""

    MODEL_MISSING_MESSAGE = "MediaPipe face model bulunamadı, yüz algılama pasif."

    def __init__(
        self,
        model_path: str | None = None,
        min_detection_confidence: float = 0.6,
    ) -> None:
        self.name = "FaceDetector"
        self.model_path = Path(model_path) if model_path else self._default_model_path()
        self.min_detection_confidence = min_detection_confidence
        self._detector = None
        self._last_timestamp_ms = 0
        self.is_available = False
        self.is_ready = False
        self.warning_message = ""
        self.initialize()

    def initialize(self) -> None:
        """MediaPipe Tasks Face Detector modelini hazırlar."""
        if mp is None or mp_tasks is None or vision is None:
            self._disable(
                "MediaPipe Tasks API yüklenemedi, yüz algılama pasif."
            )
            return

        if not self.model_path.exists():
            self._disable(self.MODEL_MISSING_MESSAGE)
            return

        try:
            base_options = mp_tasks.BaseOptions(model_asset_path=str(self.model_path))
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                min_detection_confidence=self.min_detection_confidence,
            )
            self._detector = vision.FaceDetector.create_from_options(options)
        except Exception as error:
            self._disable(f"MediaPipe face detector başlatılamadı, yüz algılama pasif: {error}")
            return

        self.is_available = True
        self.is_ready = True
        self.warning_message = ""

    def detect(self, frame) -> FaceDetectionResult:
        """Verilen BGR kamera karesinde en güvenilir yüzü arar."""
        if not self.is_available or self._detector is None:
            return FaceDetectionResult(
                detected=False,
                is_active=False,
                message=self.warning_message,
            )

        if frame is None:
            return FaceDetectionResult(detected=False, is_active=True)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        try:
            detection_result = self._detector.detect_for_video(
                mp_image,
                self._next_timestamp_ms(),
            )
        except Exception as error:
            self._disable(f"MediaPipe face detector çalışırken hata verdi, yüz algılama pasif: {error}")
            return FaceDetectionResult(
                detected=False,
                is_active=False,
                message=self.warning_message,
            )

        if not detection_result.detections:
            return FaceDetectionResult(detected=False, is_active=True)

        detection = max(
            detection_result.detections,
            key=self._confidence_from_detection,
        )
        confidence = self._confidence_from_detection(detection)
        box = self._box_from_detection(detection, frame.shape[1], frame.shape[0])

        return FaceDetectionResult(
            detected=box is not None,
            confidence=confidence,
            box=box,
            is_active=True,
        )

    def close(self) -> None:
        """MediaPipe detector kaynağını temizler."""
        if self._detector is not None:
            self._detector.close()
            self._detector = None

        self.is_available = False
        self.is_ready = False

    def _disable(self, message: str) -> None:
        """Yüz algılamayı uygulamayı çökertmeden pasif hale getirir."""
        self._detector = None
        self.is_available = False
        self.is_ready = True
        self.warning_message = message

    def _default_model_path(self) -> Path:
        """Varsayılan MediaPipe model dosyası yolunu döndürür."""
        return static_resource_path("models", "face_detector.tflite")

    def _next_timestamp_ms(self) -> int:
        """VIDEO modu için sürekli artan kare zaman damgası üretir."""
        timestamp_ms = int(time.monotonic() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms

    def _confidence_from_detection(self, detection) -> float:
        """MediaPipe detection nesnesinden güven skorunu okur."""
        categories = getattr(detection, "categories", None)
        if not categories:
            return 0.0

        return float(getattr(categories[0], "score", 0.0) or 0.0)

    def _box_from_detection(
        self,
        detection,
        frame_width: int,
        frame_height: int,
    ) -> tuple[int, int, int, int] | None:
        """MediaPipe kutusunu OpenCV çizim koordinatına çevirir."""
        bounding_box = getattr(detection, "bounding_box", None)
        if bounding_box is None:
            return None

        x = max(0, min(frame_width - 1, int(bounding_box.origin_x)))
        y = max(0, min(frame_height - 1, int(bounding_box.origin_y)))
        width = max(0, int(bounding_box.width))
        height = max(0, int(bounding_box.height))

        if width <= 0 or height <= 0:
            return None

        x2 = min(frame_width - 1, x + width)
        y2 = min(frame_height - 1, y + height)
        width = max(1, x2 - x)
        height = max(1, y2 - y)

        return x, y, width, height
