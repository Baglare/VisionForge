# Kırpılmış yüz örnekleriyle LBPH tabanlı yerel yüz kimliği algılar.

from dataclasses import dataclass
from collections import Counter, deque
import json
from pathlib import Path

import cv2
import numpy as np

from face_preprocessing import FACE_SIZE, preprocess_face
from identity_health import check_identity_health


@dataclass
class FaceIdentityResult:
    """Tek karelik yüz kimliği sonucunu temsil eder."""

    is_active: bool
    matched: bool = False
    face_label: str | None = None
    confidence: float | None = None
    message: str = ""
    selected_variant: str = ""
    quality_message: str = ""
    raw_face_label: str | None = None
    stable_face_label: str | None = None
    threshold: float = 75.0
    match_status: str = ""
    stability_count: int = 0
    health_warnings: list[str] | None = None


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
        self._match_history = deque(maxlen=8)
        self._stability_required = 5
        self.health_warnings: list[str] = []
        self.is_available = False
        self.reload()

    def reload(self) -> None:
        """Model ve etiketleri diskten yeniden yükler."""
        self._recognizer = None
        self._labels = {}
        self._match_history.clear()
        self.is_available = False
        self.warning_message = ""
        health = check_identity_health()
        self.health_warnings = health.warnings

        if not _has_lbph():
            self.warning_message = self.MODULE_MISSING_MESSAGE
            return

        if not self.model_path.exists() or not self.labels_path.exists():
            self.warning_message = "Yüz tanıma modeli bulunamadı, E ile kayıt başlatılabilir."
            if self.health_warnings:
                self.warning_message = f"{self.warning_message} {'; '.join(self.health_warnings)}"
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
        if self.health_warnings:
            self.warning_message = "; ".join(self.health_warnings)

    def reset_stability(self) -> None:
        """Yüz kaybolduğunda stabil tanıma geçmişini sıfırlar."""
        self._match_history.clear()

    def predict(self, frame, face_box) -> FaceIdentityResult:
        """Yüz kutusundan normal ve aynalı kırpımla kimlik tahmini yapar."""
        if not self.is_available or self._recognizer is None:
            return FaceIdentityResult(
                is_active=False,
                message=self.warning_message,
                threshold=self.threshold,
                match_status="pasif",
                health_warnings=self.health_warnings,
            )

        face_image = extract_face_image(frame, face_box)
        if face_image is None:
            return FaceIdentityResult(
                is_active=True,
                matched=False,
                quality_message="Yüz kırpımı hazırlanamadı",
                threshold=self.threshold,
                match_status="kalite yetersiz",
                stability_count=0,
                health_warnings=self.health_warnings,
            )

        candidates = [("normal", face_image), ("mirrored", cv2.flip(face_image, 1))]
        best_label_id = None
        best_confidence = None
        selected_variant = ""

        try:
            for variant, candidate in candidates:
                label_id, confidence = self._recognizer.predict(candidate)
                if best_confidence is None or float(confidence) < best_confidence:
                    best_label_id = int(label_id)
                    best_confidence = float(confidence)
                    selected_variant = variant
        except Exception as error:
            return FaceIdentityResult(
                is_active=False,
                matched=False,
                message=f"Yüz tanıma çalışırken hata verdi: {error}",
                threshold=self.threshold,
                match_status="hata",
                health_warnings=self.health_warnings,
            )

        raw_face_label = self._labels.get(int(best_label_id)) if best_label_id is not None else None
        single_frame_match = (
            raw_face_label is not None
            and best_confidence is not None
            and best_confidence <= self.threshold
        )
        self._match_history.append(raw_face_label if single_frame_match else None)
        stable_label, stability_count = self._stable_label()
        matched = stable_label is not None
        match_status = self._match_status(raw_face_label, best_confidence, single_frame_match, matched)
        return FaceIdentityResult(
            is_active=True,
            matched=matched,
            face_label=stable_label or raw_face_label,
            confidence=best_confidence,
            selected_variant=selected_variant,
            quality_message="Kalite uygun",
            raw_face_label=raw_face_label,
            stable_face_label=stable_label,
            threshold=self.threshold,
            match_status=match_status,
            stability_count=stability_count,
            health_warnings=self.health_warnings,
        )

    def has_registered_model(self) -> bool:
        """Kullanılabilir kayıtlı yüz modeli olup olmadığını döndürür."""
        return self.model_path.exists() and self.labels_path.exists()

    def _stable_label(self) -> tuple[str | None, int]:
        """Son tahminlerden stabil kullanıcı etiketini döndürür."""
        labels = [label for label in self._match_history if label]
        if not labels:
            return None, 0

        label, count = Counter(labels).most_common(1)[0]
        if count >= self._stability_required:
            return label, count
        return None, count

    def _match_status(
        self,
        raw_face_label: str | None,
        confidence: float | None,
        single_frame_match: bool,
        stable_match: bool,
    ) -> str:
        """Debug paneli için LBPH eşleşme durumunu üretir."""
        if raw_face_label is None:
            return "etiket yok"
        if confidence is None:
            return "skor yok"
        if stable_match:
            return "stabil eşleşti"
        if abs(float(confidence) - self.threshold) <= 5.0:
            return "Yüz skoru eşik sınırında"
        if single_frame_match:
            return "stabilite bekleniyor"
        return "eşik dışında"


def extract_face_image(frame, face_box, output_size: tuple[int, int] = FACE_SIZE):
    """Yüz kutusunu gri ve sabit boyutlu LBPH girdisine çevirir."""
    return preprocess_face(frame, face_box, output_size=output_size)


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
            images.append(cv2.flip(image, 1))
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
