# Kullanıcı arayüz ayarlarını yerel JSON dosyasında saklar.

import json
from pathlib import Path


DEFAULT_SETTINGS = {
    "hand_debug_visible": False,
    "face_debug_visible": False,
    "verification_mode": "QR + Yüz",
    "detection_profile": "Dengeli",
    "spellbook_visible": True,
    "debug_panel_visible": False,
    "spell_effects_enabled": True,
    "camera_mirror_enabled": False,
}


def settings_path() -> Path:
    """Yerel ayar dosyasının yolunu döndürür."""
    return Path(__file__).resolve().parent / "data" / "settings.json"


def load_settings() -> dict:
    """Ayarları dosyadan okur; dosya yoksa varsayılanları oluşturur."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    settings = DEFAULT_SETTINGS.copy()
    settings.update(_sanitize_settings(data))
    save_settings(settings)
    return settings


def save_settings(settings: dict) -> None:
    """Ayarları JSON dosyasına yazar."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized_settings = _sanitize_settings(settings)
    payload = {key: sanitized_settings.get(key, value) for key, value in DEFAULT_SETTINGS.items()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_ui_settings() -> dict:
    """Kalıcı ayarları app.py içindeki çalışma zamanı ayarlarına çevirir."""
    settings = load_settings()
    return {
        "show_settings_menu": False,
        "show_hand_debug": settings["hand_debug_visible"],
        "show_face_debug": settings["face_debug_visible"],
        "verification_requires_qr": settings["verification_mode"] == "QR + Yüz",
        "detection_profile": settings["detection_profile"],
        "show_spellbook": settings["spellbook_visible"],
        "show_debug_page": settings["debug_panel_visible"],
        "spell_effects_enabled": settings["spell_effects_enabled"],
        "mirror_camera": settings["camera_mirror_enabled"],
        "show_system_status": False,
    }


def save_ui_settings(ui_settings: dict) -> None:
    """Çalışma zamanı ayarlarını kalıcı JSON ayarlarına çevirip kaydeder."""
    settings = {
        "hand_debug_visible": bool(ui_settings.get("show_hand_debug", False)),
        "face_debug_visible": bool(ui_settings.get("show_face_debug", False)),
        "verification_mode": "QR + Yüz" if ui_settings.get("verification_requires_qr", True) else "Yalnızca Yüz",
        "detection_profile": ui_settings.get("detection_profile", "Dengeli"),
        "spellbook_visible": bool(ui_settings.get("show_spellbook", True)),
        "debug_panel_visible": bool(ui_settings.get("show_debug_page", False)),
        "spell_effects_enabled": bool(ui_settings.get("spell_effects_enabled", True)),
        "camera_mirror_enabled": bool(ui_settings.get("mirror_camera", False)),
    }
    save_settings(settings)


def _sanitize_settings(data: dict) -> dict:
    """JSON içindeki beklenen ayar tiplerini güvenli hale getirir."""
    sanitized = {}
    for key, default_value in DEFAULT_SETTINGS.items():
        value = data.get(key, default_value)
        if isinstance(default_value, bool):
            sanitized[key] = value if isinstance(value, bool) else default_value
        elif key == "verification_mode":
            sanitized[key] = value if value in {"QR + Yüz", "Yalnızca Yüz"} else default_value
        elif key == "detection_profile":
            sanitized[key] = value if value in {"Hassas", "Dengeli", "Kararlı"} else default_value
        else:
            sanitized[key] = value
    return sanitized
