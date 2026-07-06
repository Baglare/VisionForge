# Yüz tanıma modeli, etiketleri ve profil dosyaları arasındaki tutarlılığı kontrol eder.

from dataclasses import dataclass, field
import json
from pathlib import Path

from guild_profile import default_profiles_path, load_profiles_from_file, local_profiles_path, project_root


@dataclass
class IdentityHealthResult:
    """Yüz tanıma dosyalarının sağlık durumunu temsil eder."""

    model_exists: bool
    labels_exists: bool
    local_profiles_exists: bool
    labels_match_profiles: bool
    known_users: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_identity_health() -> IdentityHealthResult:
    """LBPH modeli, label dosyası ve profil dosyalarının tutarlılığını kontrol eder."""
    root = project_root()
    model_path = root / "models" / "face_recognizer_lbph.yml"
    labels_path = root / "data" / "face_labels.json"
    local_path = local_profiles_path()
    demo_path = default_profiles_path()

    model_exists = model_path.exists()
    labels_exists = labels_path.exists()
    local_profiles_exists = local_path.exists()
    warnings: list[str] = []

    labels = _load_label_values(labels_path, warnings) if labels_exists else []
    profile_keys = _load_profile_keys(demo_path, local_path, warnings)
    missing_labels = sorted(label for label in labels if label not in profile_keys)
    labels_match_profiles = (not labels_exists) or (bool(labels) and not missing_labels)

    if model_exists and not labels_exists:
        warnings.append("Model var ama face_labels.json eksik")
    if labels_exists and not model_exists:
        warnings.append("face_labels.json var ama LBPH model dosyası eksik")
    if labels_exists and not labels:
        warnings.append("face_labels.json içinde etiket yok")
    if labels_exists and missing_labels:
        warnings.append("Yüz etiketi profil dosyasında bulunamadı: " + ", ".join(missing_labels))
    if not local_profiles_exists:
        warnings.append("Yerel profil dosyası yok; demo ve Misafir profilleriyle devam ediliyor")

    return IdentityHealthResult(
        model_exists=model_exists,
        labels_exists=labels_exists,
        local_profiles_exists=local_profiles_exists,
        labels_match_profiles=labels_match_profiles,
        known_users=sorted(profile_keys),
        warnings=warnings,
    )


def _load_label_values(path: Path, warnings: list[str]) -> list[str]:
    """face_labels.json içindeki kullanıcı etiketlerini okur."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        warnings.append(f"face_labels.json okunamadı: {error}")
        return []

    labels = data.get("labels", {})
    if not isinstance(labels, dict):
        warnings.append("face_labels.json formatı geçersiz")
        return []

    return [str(value) for value in labels.values()]


def _load_profile_keys(demo_path: Path, local_path: Path, warnings: list[str]) -> set[str]:
    """Demo ve local profil dosyalarındaki username/face_label anahtarlarını toplar."""
    profile_keys: set[str] = {"guest", "Misafir"}
    for path in (demo_path, local_path):
        try:
            profiles = load_profiles_from_file(path)
        except Exception as error:
            warnings.append(f"{path.name} okunamadı: {error}")
            continue

        for profile in profiles:
            if profile.username:
                profile_keys.add(str(profile.username))
            if profile.face_label:
                profile_keys.add(str(profile.face_label))

    return profile_keys
