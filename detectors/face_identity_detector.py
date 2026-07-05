# Kırpılmış yüz örnekleriyle LBPH tabanlı yerel yüz kimliği algılar.

from dataclasses import dataclass
import json
from pathlib import Path

import cv2
import numpy as np


FACE_SIZE = (160, 160)


@dataclass
class FaceIdentityResult:
    """Tek karelik yüz kimliği sonucunu temsil eder."""

    is_active: bool
    matched: bool = False
    face_label: str | None = None
    confidence: float | None = None
    message: str = ""


class FaceIdentityDetector:
    """OpenCV LBPH ile yerel yüz tanıma modeli çalıştırır."""

    MODULE_MISSING_MESSAGE = "OpenCV face modülü bulunamadı, yüz tanıma pasif."

    def __init__(
        self,
        model_path: str | None = None,
        labels_path: str | None = None,
        threshold: float = 75.0,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        self.model_path = Path(model_path) if model_path else root / "models" / "face_recognizer_lbph.yml"
        self.labels_path = Path(labels_path) if labels_path else root / "data" / "face_labels.json"
        self.threshold = threshold
        self.warning_message = ""
        self._recognizer = None
        self._labels: dict[int, str] = {}
        self.is_available = False
        self.reload()

    def reload(self) -> None:
        """Model ve etiketleri diskten yeniden yükler."""
        self._recognizer = None
        self._labels = {}
        self.is_available = False
        self.warning_message = ""

        if not _has_lbph():
            self.warning_message = self.MODULE_MISSING_MESSAGE
            return

        if not self.model_path.exists() or not self.labels_path.exists():
            self.warning_message = "Yüz tanıma modeli bulunamadı, E ile kayıt başlatılabilir."
            return

        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(str(self.model_path))
            self._labels = _load_labels(self.labels_path)
        except Exception as error:
            self.warning_message = f"Yüz tanıma modeli yüklenemedi: {error}"
            return

        if not self._labels:
            self.warning_message = "Yüz tanıma etiketleri boş, E ile kayıt başlatılabilir."
            return

        self._recognizer = recognizer
        self.is_available = True

    def predict(self, frame, face_box) -> FaceIdentityResult:
        """Yüz kutusundan kimlik tahmini yapar."""
        if not self.is_available or self._recognizer is None:
            return FaceIdentityResult(is_active=False, message=self.warning_message)

        face_image = extract_face_image(frame, face_box)
        if face_image is None:
            return FaceIdentityResult(is_active=True, matched=False)

        try:
            label_id, confidence = self._recognizer.predict(face_image)
        except Exception as error:
            return FaceIdentityResult(
                is_active=False,
                matched=False,
                message=f"Yüz tanıma çalışırken hata verdi: {error}",
            )

        face_label = self._labels.get(int(label_id))
        matched = face_label is not None and float(confidence) <= self.threshold
        return FaceIdentityResult(
            is_active=True,
            matched=matched,
            face_label=face_label if matched else None,
            confidence=float(confidence),
        )

    def has_registered_model(self) -> bool:
        """Kullanılabilir kayıtlı yüz modeli olup olmadığını döndürür."""
        return self.model_path.exists() and self.labels_path.exists()


def extract_face_image(frame, face_box, output_size: tuple[int, int] = FACE_SIZE):
    """Yüz kutusunu gri ve sabit boyutlu LBPH girdisine çevirir."""
    if frame is None or face_box is None:
        return None

    frame_height, frame_width = frame.shape[:2]
    x, y, width, height = [int(value) for value in face_box]

    if width < 50 or height < 50:
        return None

    padding_x = int(width * 0.16)
    padding_y = int(height * 0.22)
    x1 = max(0, x - padding_x)
    y1 = max(0, y - padding_y)
    x2 = min(frame_width, x + width + padding_x)
    y2 = min(frame_height, y + height + padding_y)

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return cv2.resize(gray, output_size, interpolation=cv2.INTER_AREA)


def train_lbph_from_gallery(
    gallery_root: Path,
    model_path: Path,
    labels_path: Path,
) -> int:
    """Yüz galerisinden LBPH modeli eğitir ve kaç örnek kullandığını döndürür."""
    if not _has_lbph():
        raise RuntimeError(FaceIdentityDetector.MODULE_MISSING_MESSAGE)

    images: list[np.ndarray] = []
    labels: list[int] = []
    label_map: dict[int, str] = {}

    if not gallery_root.exists():
        raise RuntimeError("Yüz galerisi bulunamadı.")

    label_id = 0
    for user_dir in sorted(path for path in gallery_root.iterdir() if path.is_dir()):
        samples = sorted(user_dir.glob("*.png"))
        if not samples:
            continue

        label_map[label_id] = user_dir.name
        for sample_path in samples:
            image = cv2.imread(str(sample_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            image = cv2.resize(image, FACE_SIZE, interpolation=cv2.INTER_AREA)
            images.append(image)
            labels.append(label_id)

        label_id += 1

    if not images:
        raise RuntimeError("Eğitim için geçerli yüz örneği bulunamadı.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels, dtype=np.int32))
    model_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    recognizer.write(str(model_path))
    labels_path.write_text(
        json.dumps({"labels": {str(key): value for key, value in label_map.items()}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(images)


def _has_lbph() -> bool:
    """OpenCV contrib face modülünün kullanılabilir olup olmadığını döndürür."""
    return hasattr(cv2, "face") and hasattr(cv2.face, "LBPHFaceRecognizer_create")


def _load_labels(path: Path) -> dict[int, str]:
    """Etiket dosyasını okur."""
    data = json.loads(path.read_text(encoding="utf-8"))
    labels = data.get("labels", {})
    return {int(key): str(value) for key, value in labels.items()}
