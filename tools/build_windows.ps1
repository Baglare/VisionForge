[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Spec = Join-Path $RepoRoot "packaging\VisionForge.spec"
$BuildDir = Join-Path $RepoRoot "build"
$DistAppDir = Join-Path $RepoRoot "dist\VisionForge"
$ExePath = Join-Path $DistAppDir "VisionForge.exe"
$Verifier = Join-Path $RepoRoot "tools\verify_distribution.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Proje sanal ortamı bulunamadı: $Python"
}

Write-Host "Python ortamı ve build bağımlılıkları kontrol ediliyor..."
& $Python -c "import sys, PyInstaller, PySide6, cv2, mediapipe; print('python=' + sys.version.split()[0]); print('executable=' + sys.executable); print('pyinstaller=' + PyInstaller.__version__); print('pyside6=' + PySide6.__version__); print('opencv=' + cv2.__version__); print('mediapipe=' + mediapipe.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Build bağımlılıkları eksik. Önce: .venv\Scripts\python.exe -m pip install -r requirements-dev.txt"
}

$RequiredModels = @(
    (Join-Path $RepoRoot "models\face_detector.tflite"),
    (Join-Path $RepoRoot "models\hand_landmarker.task")
)
foreach ($Model in $RequiredModels) {
    if (-not (Test-Path -LiteralPath $Model -PathType Leaf)) {
        throw "Gerekli model eksik: $Model`nÖnce çalıştırın: .venv\Scripts\python.exe tools\download_models.py"
    }
}

function Remove-BuildDirectory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $Resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $Resolved.StartsWith($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Güvenli olmayan temizleme hedefi reddedildi: $Resolved"
    }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}

Write-Host "Eski build çıktıları temizleniyor..."
Remove-BuildDirectory $BuildDir
Remove-BuildDirectory $DistAppDir

Push-Location $RepoRoot
try {
    Write-Host "PyInstaller onedir build başlatılıyor..."
    & $Python -m PyInstaller $Spec --noconfirm --clean
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build başarısız oldu (exit code: $LASTEXITCODE)."
    }

    if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
        throw "Build tamamlandı ancak EXE bulunamadı: $ExePath"
    }

    Write-Host "Dağıtım doğrulanıyor..."
    & $Python $Verifier $DistAppDir
    if ($LASTEXITCODE -ne 0) {
        throw "Dağıtım doğrulaması başarısız oldu."
    }
}
finally {
    Pop-Location
}

Write-Host "VisionForge Windows build hazır."
Write-Host "EXE: $ExePath"
Write-Host "Dağıtım klasörü: $DistAppDir"
