# Yüz kırpma, kalite kontrolü ve LBPH ön işleme yardımcıları.

from dataclasses import dataclass

import cv2


FACE_SIZE = (160, 160)


@dataclass
class FaceQualityResult:
    """Tek yüz örneği için kalite kontrol sonucunu temsil eder."""

    is_acceptable: bool
    message: str
    face_image: object | None = None
    blur_score: float = 0.0


def preprocess_face(frame, face_box, output_size: tuple[int, int] = FACE_SIZE):
    """Yüz kutusunu LBPH için gri, kontrastlı ve sabit boyutlu hale getirir."""
    if frame is None or face_box is None:
        return None

    crop = crop_face(frame, face_box)
    if crop is None:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, output_size, interpolation=cv2.INTER_AREA)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(resized)


def crop_face(frame, face_box, padding_x_ratio: float = 0.16, padding_y_ratio: float = 0.22):
    """Yüz kutusunu biraz genişletip görüntü sınırları içinde kırpar."""
    if frame is None or face_box is None:
        return None

    frame_height, frame_width = frame.shape[:2]
    x, y, width, height = [int(value) for value in face_box]
    if width <= 0 or height <= 0:
        return None

    padding_x = int(width * padding_x_ratio)
    padding_y = int(height * padding_y_ratio)
    x1 = max(0, x - padding_x)
    y1 = max(0, y - padding_y)
    x2 = min(frame_width, x + width + padding_x)
    y2 = min(frame_height, y + height + padding_y)
    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    return crop if crop.size else None


def assess_face_quality(
    frame,
    face_box,
    confidence: float | None = None,
    min_confidence: float = 0.58,
    min_face_ratio: float = 0.16,
    margin_ratio: float = 0.06,
    blur_threshold: float = 45.0,
) -> FaceQualityResult:
    """Yüz örneğinin kayıt/eğitim için yeterli kalitede olup olmadığını kontrol eder."""
    if frame is None or face_box is None:
        return FaceQualityResult(False, "Yüz bulunamadı")

    if confidence is not None and confidence < min_confidence:
        return FaceQualityResult(False, "Biraz daha ışık gerekli")

    frame_height, frame_width = frame.shape[:2]
    x, y, width, height = [int(value) for value in face_box]
    min_face_size = int(min(frame_width, frame_height) * min_face_ratio)
    if width < min_face_size or height < min_face_size:
        return FaceQualityResult(False, "Yüz çok küçük")

    margin = int(min(frame_width, frame_height) * margin_ratio)
    if x < margin or y < margin or x + width > frame_width - margin or y + height > frame_height - margin:
        return FaceQualityResult(False, "Kamera ortasına gel")

    face_image = preprocess_face(frame, face_box)
    if face_image is None:
        return FaceQualityResult(False, "Yüz çok küçük")

    blur_score = float(cv2.Laplacian(face_image, cv2.CV_64F).var())
    if blur_score < blur_threshold:
        return FaceQualityResult(False, "Görüntü bulanık", face_image=face_image, blur_score=blur_score)

    return FaceQualityResult(True, "Kalite uygun", face_image=face_image, blur_score=blur_score)
