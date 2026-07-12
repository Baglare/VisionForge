# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import get_package_paths


PROJECT_ROOT = Path(SPECPATH).resolve().parent
MEDIAPIPE_ROOT = Path(get_package_paths("mediapipe")[1])
ICON_PATH = PROJECT_ROOT / "assets" / "branding" / "visionforge.ico"

datas = [
    (str(PROJECT_ROOT / "models" / "face_detector.tflite"), "models"),
    (str(PROJECT_ROOT / "models" / "hand_landmarker.task"), "models"),
    (str(ICON_PATH), "assets/branding"),
    (str(MEDIAPIPE_ROOT / "tasks" / "c" / "libmediapipe.dll"), "mediapipe/tasks/c"),
]

hiddenimports = [
    "mediapipe.tasks.c",
    "mediapipe.tasks.python.vision",
    "qrcode.image.pil",
    "PIL.Image",
]

a = Analysis(
    [str(PROJECT_ROOT / "app.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VisionForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    icon=str(ICON_PATH),
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VisionForge",
)
