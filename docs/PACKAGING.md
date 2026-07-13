# VisionForge Windows Paketleme

VisionForge'un mevcut Windows build iş akışı PyInstaller `onedir` biçimindedir. Çıktı tek EXE değildir; çalıştırılabilir dosya Qt, OpenCV, MediaPipe ve model dosyalarıyla aynı dağıtım klasöründe bulunur.

## Build

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools\build_windows.ps1
```

Çıktı:

```text
dist\VisionForge\VisionForge.exe
```

Build betiği gerekli iki MediaPipe modelini kontrol eder, eski `build/` ve `dist/VisionForge/` çıktılarını güvenli biçimde temizler, `packaging/VisionForge.spec` ile onedir build alır ve dağıtım doğrulayıcısını çalıştırır.

## Bundle İçeriği

Spec şu statik kaynakları dahil eder:

- `models\face_detector.tflite`
- `models\hand_landmarker.task`
- `assets\branding\visionforge.ico`
- MediaPipe native runtime dosyası
- PySide6/Qt runtime ve Windows platform eklentileri

Özel ikon hem `VisionForge.exe` üzerinde hem uygulama penceresinde kullanılır.

## Source/Frozen Yolları

`runtime_paths.py`, salt okunur bundle kaynakları ile yazılabilir portable veriyi ayırır:

- Source: statik ve yazılabilir yollar repo kökünden çözülür.
- Frozen: statik kaynaklar PyInstaller bundle kökünden; kullanıcı verileri `VisionForge.exe` klasöründen çözülür.

Frozen uygulama ilk çalıştırmada EXE yanında gereken `data/`, `models/` ve `assets/guild_seals/` klasörlerini oluşturur.

## Dağıtıma Alınmayan Yerel Veriler

- Ayarlar ve local profiller
- Yüz galerisi ve içe aktarılan fotoğraflar
- Yüz etiketleri ve eğitilmiş LBPH modeli
- Kullanıcıya özel QR/lonca mühürleri
- Geliştirme klasörleri, kaynak dosyaları ve kişisel çalışma verileri

Manuel doğrulama:

```powershell
.venv\Scripts\python.exe tools\verify_distribution.py dist\VisionForge
```

## Portable Kullanım

1. Build tamamlandıktan sonra `dist\VisionForge\` klasörünün tamamını taşıyın.
2. ZIP ile aktarılıyorsa önce normal, yazılabilir bir klasöre çıkarın.
3. Uygulamayı doğrudan ZIP içinden veya salt okunur `Program Files` konumundan çalıştırmayın.
4. Kalıcı ayarlar ve kayıt verileri isteniyorsa EXE klasörünün yazılabilir kaldığını doğrulayın.

## Release Durumu

Build iş akışı mevcuttur; ancak bu repo henüz installer, kod imzalama, sürümlü ZIP, checksum veya public indirme bağlantısı yayımlamaz. Bunlar release hazırlığı aşamasına bırakılmıştır.
