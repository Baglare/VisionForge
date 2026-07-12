"""Source ve PyInstaller çalışma ortamları için merkezi yol çözümü."""

from __future__ import annotations

from pathlib import Path
import sys


def is_frozen() -> bool:
    """Uygulama PyInstaller içinden çalışıyorsa True döndürür."""
    return bool(getattr(sys, "frozen", False))


def source_project_root() -> Path:
    """Normal source çalışmasında repo kökünü döndürür."""
    return Path(__file__).resolve().parent


def bundle_root() -> Path:
    """Statik PyInstaller kaynaklarının açıldığı kökü döndürür."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return source_project_root()


def executable_root() -> Path:
    """Frozen çalışmada EXE klasörünü, source çalışmada repo kökünü döndürür."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return source_project_root()


def static_resource_path(*parts: str) -> Path:
    """Paket içinden salt okunur statik bir kaynak yolu üretir."""
    return bundle_root().joinpath(*parts)


def writable_app_root() -> Path:
    """Taşınabilir kullanıcı verilerinin yazılacağı uygulama kökünü döndürür."""
    return executable_root()


def writable_path(*parts: str) -> Path:
    """EXE yanında veya source repo içinde yazılabilir bir yol üretir."""
    return writable_app_root().joinpath(*parts)


def ensure_writable_directories() -> None:
    """İlk çalıştırmada gereken taşınabilir kullanıcı klasörlerini oluşturur."""
    for relative_parts in (
        ("data",),
        ("data", "face_gallery"),
        ("data", "import_faces"),
        ("models",),
        ("assets", "guild_seals"),
    ):
        writable_path(*relative_parts).mkdir(parents=True, exist_ok=True)
