"""VisionForge PyInstaller onedir çıktısının bütünlük ve gizlilik kontrolü."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


FORBIDDEN_FILE_NAMES = {
    "settings.json",
    "local_profiles.json",
    "face_labels.json",
    "face_recognizer_lbph.yml",
}
FORBIDDEN_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "face_gallery",
    "import_faces",
    "private",
}
PROJECT_SOURCE_ROOTS = {
    "detectors",
    "enrollment",
    "tests",
    "tools",
    "ui",
}
PROJECT_SOURCE_FILES = {
    "app.py",
    "vision_engine.py",
    "runtime_paths.py",
}


def _find_relative(root: Path, *parts: str) -> Path | None:
    expected = tuple(part.casefold() for part in parts)
    for path in root.rglob(parts[-1]):
        relative_parts = tuple(part.casefold() for part in path.relative_to(root).parts)
        if relative_parts[-len(expected) :] == expected:
            return path
    return None


def verify_distribution(dist_root: Path) -> list[str]:
    errors: list[str] = []
    if not dist_root.is_dir():
        return [f"Dağıtım klasörü bulunamadı: {dist_root}"]

    required_paths = {
        "VisionForge.exe": dist_root / "VisionForge.exe",
        "Face Detector modeli": _find_relative(dist_root, "models", "face_detector.tflite"),
        "Hand Landmarker modeli": _find_relative(dist_root, "models", "hand_landmarker.task"),
        "MediaPipe native runtime": _find_relative(
            dist_root, "mediapipe", "tasks", "c", "libmediapipe.dll"
        ),
        "VisionForge uygulama ikonu": _find_relative(
            dist_root, "assets", "branding", "visionforge.ico"
        ),
        "Qt Windows platform plugin": _find_relative(dist_root, "platforms", "qwindows.dll"),
    }
    for label, path in required_paths.items():
        if path is None or not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"Eksik zorunlu dağıtım kaynağı: {label}")

    for path in dist_root.rglob("*"):
        relative = path.relative_to(dist_root)
        lowered_parts = {part.casefold() for part in relative.parts}
        if lowered_parts.intersection(FORBIDDEN_DIRECTORY_NAMES):
            errors.append(f"Yasaklı klasör bulundu: {relative}")
            continue
        if path.is_file() and path.name.casefold() in FORBIDDEN_FILE_NAMES:
            errors.append(f"Yasaklı kullanıcı dosyası bulundu: {relative}")
        if path.is_file() and path.suffix.casefold() in {".pyc", ".pyo"}:
            errors.append(f"Python geliştirme cache dosyası bulundu: {relative}")
        if path.is_file() and (
            relative.name.casefold() in PROJECT_SOURCE_FILES
            or (relative.parts and relative.parts[0].casefold() in PROJECT_SOURCE_ROOTS)
        ):
            errors.append(f"Proje kaynak dosyası bulundu: {relative}")
        parts = tuple(part.casefold() for part in relative.parts)
        if path.is_file() and "guild_seals" in parts and path.suffix.casefold() == ".png":
            errors.append(f"Kişisel lonca mührü bulundu: {relative}")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dist_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist" / "VisionForge",
    )
    args = parser.parse_args()
    dist_root = args.dist_root.resolve()
    errors = verify_distribution(dist_root)
    if errors:
        print("VisionForge dağıtım doğrulaması BAŞARISIZ:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"VisionForge dağıtım doğrulaması başarılı: {dist_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
