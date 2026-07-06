"""Download required MediaPipe model files for VisionForge."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT_DIR / "models"

MODELS = [
    {
        "name": "Face Detector",
        "path": MODELS_DIR / "face_detector.tflite",
        "url": "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    },
    {
        "name": "Hand Landmarker",
        "path": MODELS_DIR / "hand_landmarker.task",
        "url": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    },
]


def download_file(url: str, target_path: Path) -> None:
    """Download a file atomically enough for this small setup helper."""
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            with temp_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)

        temp_path.replace(target_path)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"İndirme başarısız: {exc}") from exc


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    failed = False
    for model in MODELS:
        target_path = model["path"]
        if target_path.exists():
            print(f"{model['name']}: zaten var -> {target_path}")
            continue

        print(f"{model['name']}: indiriliyor...")
        try:
            download_file(model["url"], target_path)
        except RuntimeError as exc:
            failed = True
            print(f"{model['name']}: {exc}", file=sys.stderr)
            print(f"Manuel indirme için hedef konum: {target_path}", file=sys.stderr)
        else:
            print(f"{model['name']}: tamamlandı -> {target_path}")

    if failed:
        print("Bazı model dosyaları indirilemedi.", file=sys.stderr)
        return 1

    print("Model kontrolü tamamlandı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
