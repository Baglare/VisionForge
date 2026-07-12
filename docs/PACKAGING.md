# Windows paketleme

VisionForge'un ilk Windows dağıtımı PyInstaller `onedir` biçimindedir. Bu yapı Qt, OpenCV ve MediaPipe çalışma dosyalarını ayrı dosyalar halinde tuttuğu için `onefile` paketine göre daha kolay doğrulanır, daha hızlı başlar ve sorun ayıklaması daha güvenilirdir.

## Build ortamı

Build, proje içindeki `.venv` sanal ortamından alınır. Geliştirme bağımlılıklarını kurmak için:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

PySide6, Shiboken ve PyInstaller'ın bu sanal ortamdan geldiğini doğruladıktan sonra build alın:

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_windows.ps1
```

Çıktı `dist\VisionForge\` klasöründe, çalıştırılabilir dosya ise `dist\VisionForge\VisionForge.exe` yolunda oluşur.

## Paket içeriği ve kullanıcı verileri

Paket, uygulama kodu ile `models\face_detector.tflite` ve `models\hand_landmarker.task` sabit modellerini içerir. Kişisel ayarlar, yüz galerileri, içe aktarılan fotoğraflar, yüz etiketleri, yerel profiller, eğitilmiş LBPH modeli ve oluşturulmuş lonca mühürleri build'e alınmaz.

Frozen uygulama aşağıdaki yazılabilir verileri `VisionForge.exe` dosyasının bulunduğu klasöre göre oluşturur:

- `data\settings.json`
- `data\face_gallery\`
- `data\import_faces\`
- `data\face_labels.json`
- `data\local_profiles.json`
- `models\face_recognizer_lbph.yml`
- `assets\guild_seals\`

Portable kullanımda kalıcılık için tüm `dist\VisionForge\` klasörünü birlikte taşıyın. Uygulama `Program Files` gibi salt okunur bir konuma kopyalanırsa kayıt ve ayar yazma işlemleri çalışmayabilir.

## Doğrulama ve kısıtlar

Build betiği gerekli MediaPipe modellerini, EXE oluşumunu ve dağıtım gizlilik kurallarını otomatik kontrol eder. Ayrı kontrol şu komutla çalıştırılabilir:

```powershell
.venv\Scripts\python.exe tools\verify_distribution.py dist\VisionForge
```

Bu aşamada installer, kod imzalama, özel Windows ikonu ve `onefile` dağıtımı yoktur. Bunlar `onedir` paketi gerçek makinelerde doğrulandıktan sonraki aşamadır.
