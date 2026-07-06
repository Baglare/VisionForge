# VisionForge için model, profil ve QR dosyalarının yerel durumunu kontrol eder.

from dataclasses import dataclass
from pathlib import Path

from identity_health import check_identity_health


@dataclass
class SystemStatusItem:
    """Tek sistem durumu satırını temsil eder."""

    label: str
    exists: bool
    required: bool
    hint: str = ""
    ok_text: str = "Var"
    missing_text: str = "Eksik"

    @property
    def status_text(self) -> str:
        """Kullanıcıya gösterilecek kısa durum metnini döndürür."""
        return self.ok_text if self.exists else self.missing_text

    @property
    def importance_text(self) -> str:
        """Durumun gerekli mi opsiyonel mi olduğunu döndürür."""
        return "gerekli" if self.required else "opsiyonel"


def project_root() -> Path:
    """Proje kök klasörünü döndürür."""
    return Path(__file__).resolve().parent


def get_system_status() -> list[SystemStatusItem]:
    """Model, profil ve QR kaynaklarının durumunu döndürür."""
    root = project_root()
    guild_seal_root = root / "assets" / "guild_seals"
    has_qr_png = guild_seal_root.exists() and any(guild_seal_root.glob("*.png"))
    identity_health = check_identity_health()
    identity_hint = "; ".join(identity_health.warnings[:2]) if identity_health.warnings else "label/profil uyumlu"

    return [
        SystemStatusItem(
            "Face Detector modeli",
            (root / "models" / "face_detector.tflite").exists(),
            True,
            "models/face_detector.tflite",
        ),
        SystemStatusItem(
            "Hand Landmarker modeli",
            (root / "models" / "hand_landmarker.task").exists(),
            True,
            "models/hand_landmarker.task",
        ),
        SystemStatusItem(
            "Yüz tanıma modeli",
            (root / "models" / "face_recognizer_lbph.yml").exists(),
            False,
            "E ile kayıt oluştur",
        ),
        SystemStatusItem(
            "Yüz etiketleri",
            (root / "data" / "face_labels.json").exists(),
            False,
            "E ile kayıt oluştur",
        ),
        SystemStatusItem(
            "Yerel profiller",
            (root / "data" / "local_profiles.json").exists(),
            False,
            "E ile kayıt oluştur",
        ),
        SystemStatusItem(
            "QR/lonca mühürleri",
            has_qr_png,
            False,
            "kayıt sonrası oluşur",
        ),
        SystemStatusItem(
            "Label/Profile eşleşmesi",
            identity_health.labels_match_profiles,
            False,
            identity_hint,
            ok_text="Uyumlu",
            missing_text="Uyarı",
        ),
    ]


def has_registered_wizard() -> bool:
    """Kayıtlı yerel yüz modeli ve profil var mı bilgisini döndürür."""
    root = project_root()
    return (
        (root / "models" / "face_recognizer_lbph.yml").exists()
        and (root / "data" / "face_labels.json").exists()
        and (root / "data" / "local_profiles.json").exists()
    )
