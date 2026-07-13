# VisionForge

VisionForge; kamera görüntüsünde yüz ve el algılama, yerel kullanıcı doğrulama ve hareket tabanlı büyü komutlarını birleştiren PySide6 masaüstü prototipidir. Uygulama; MediaPipe, OpenCV LBPH, QR tabanlı lonca mührü ve yerel profil verileriyle tamamen cihaz üzerinde çalışır.

> VisionForge profesyonel bir güvenlik veya production-grade biyometrik doğrulama ürünü değildir. Yerel çalışan bir bilgisayarlı görü ve etkileşim prototipidir.

## English Overview

VisionForge is a local-first PySide6 desktop computer-vision prototype. It combines MediaPipe face and hand detection, OpenCV LBPH face recognition, QR-based guild-seal verification, gesture-driven spells, and a native Qt enrollment workflow. It is not a professional security or production biometric-authentication product.

## Güncel Özellikler

- PySide6 tabanlı, yeniden boyutlandırılabilir masaüstü arayüzü.
- Gece laciverti, indigo, mor ve lavanta renk sistemi; özel VisionForge uygulama ikonu.
- MediaPipe Tasks ile yüz ve el algılama.
- OpenCV LBPH ile yerel yüz tanıma ve stabil etiket kararı.
- QR/lonca mührü ile isteğe bağlı ikinci doğrulama katmanı.
- Tam doğrulama sonrasında 10 saniyelik yüz kaybı toleransı.
- `HandStateTracker` ile yumuşatılmış hareket, kısa kayıp toleransı ve kalite ölçümleri.
- Donma, Ateş ve Kalkan büyüleri; yetki ve cooldown kontrolleri.
- Sıralı Donma → Ateş → Kalkan Trial görevi.
- Canlı kamera veya fotoğraf içe aktarma ile native Qt kayıt/yüz eğitimi akışı.
- Sistem kaynaklarını ve performans değerlerini gösteren durum/debug sayfaları.
- PyInstaller `onedir` Windows build ve portable veri yerleşimi.

## Uygulama Sayfaları

| Sayfa | Amaç |
| --- | --- |
| Canlı Görüş | Oranı korunan kamera görüntüsü, profil, doğrulama, aktif büyü, Trial ve bildirim özeti |
| Büyü Kitabı | Açık/kilitli büyüler, tetikleme, etki ve gereken rütbe bilgileri |
| Trial | Üç adımlı görevin aktif, tamamlanmış ve yetki bekleyen durumları |
| Kayıt | Canlı kamera veya fotoğraf içe aktarma ile yerel profil ve LBPH eğitimi |
| Ayarlar | Overlay seçenekleri, kamera aynalama, doğrulama modu ve algılama profili |
| Sistem Durumu | Kamera, MediaPipe modelleri, yerel tanıma dosyaları ve lonca mühürleri |
| Debug | Genel, Yüz/Doğrulama, El/Tracker ve Büyü/Trial teknik değerleri |

## Mimari Akış

```text
Kamera (640×480)
  → CameraWorker / ayrı QThread
  → VisionEngine.process_frame()
  → yüz + kimlik + QR + doğrulama oturumu
  → el + HandStateTracker + SpellEngine + TrialEngine
  → en güncel QImage ve durum payload'u
  → MainWindow + FrameView + Qt sayfaları
```

`CameraWorker` kamera ve görüntü işleme işini Qt ana thread'inden ayırır. Worker yalnızca en güncel kareyi tutar; böylece UI yavaşladığında eski karelerden oluşan büyüyen bir kuyruk oluşmaz. `FrameView`, 640×480 işleme görüntüsünü pencere alanına en-boy oranını koruyarak yerleştirir.

Kamera görüntüsüne bağlı profil etiketi, debug kutuları ve büyü efektleri OpenCV/Pillow çizim katmanında kalır. Navigasyon, kartlar, ayarlar, kayıt, Büyü Kitabı, Trial, sistem durumu ve debug arayüzleri Qt widget'larıdır.

Ayrıntılar için [Mimari](docs/ARCHITECTURE.md) belgesine bakın.

## Doğrulama ve Grace Period

Varsayılan mod `QR + Yüz`dür. Kayıtlı yüz stabil tanındıktan sonra doğru kullanıcıya ait lonca mührü okunursa tam profil açılır. `Yalnızca Yüz` modunda stabil yüz tanıma yeterlidir. Tanınmayan veya henüz tam doğrulanmamış kullanıcı Misafir yetkileriyle kalır.

Tam doğrulanmış kullanıcı kameradan çıktığında oturum hemen kapanmaz. `VerificationSession`, profil ve yetkileri en fazla 10 saniye korur. Aynı kullanıcı süre dolmadan geri dönerse oturum devam eder; farklı bir stabil kullanıcı görülürse veya süre biterse eski oturum korunmaz.

## Büyüler ve Trial

| Büyü | Tetikleme | Varsayılan yetki |
| --- | --- | --- |
| Donma | Açık avucu kısa süre sabit tutma | Misafir ve üzeri |
| Ateş | Kontrollü yatay süpürme, ardından açık avuç | Yetkili profil |
| Kalkan | İki gerçek açık el | Yetkili profil |

Trial sayfası Donma → Ateş → Kalkan sırasını izler. Doğru büyü ilerletir; yanlış büyü görevi sıfırlamaz. Gerekli büyü yetkisi olmayan adımlar kilitli gösterilir.

## Kayıt Sistemi

Kayıt sayfası iki kaynak destekler:

- **Canlı Kamera:** Düz bakma, sağ/sol dönüş, yaklaşma ve uzaklaşma aşamalarında 30 kabul edilen örnek toplar.
- **Fotoğraf İçe Aktarma:** Seçilen klasördeki desteklenen görselleri yüz ve kalite kontrolünden geçirir.

Tamamlandığında yerel LBPH modeli, etiket eşlemesi, profil ve kullanıcıya özel QR/lonca mührü üretilir. Yeni model uygulama kapatılmadan yeniden yüklenir.

## Source Kurulum

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tools\download_models.py
python app.py
```

`opencv-contrib-python` LBPH için gereklidir. Aynı sanal ortamda ayrıca `opencv-python` veya headless OpenCV varyantları bırakılmamalıdır.

## Windows Portable Build

Build bağımlılıklarını kurun ve mevcut `onedir` iş akışını çalıştırın:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools\build_windows.ps1
```

Çıktı:

```text
dist\VisionForge\VisionForge.exe
```

Portable kullanımda yalnız EXE'yi değil, `dist\VisionForge\` klasörünün tamamını taşıyın. Bu repo henüz yayımlanmış bir public release, ZIP veya indirme bağlantısı sunmaz. Ayrıntılar için [Windows Paketleme](docs/PACKAGING.md) belgesine bakın.

## Yerel Veri ve Gizlilik

Source çalışmada kullanıcı verileri repo kökünde, frozen çalışmada `VisionForge.exe` yanındaki portable klasörlerde tutulur:

```text
data/settings.json
data/face_gallery/
data/import_faces/
data/face_labels.json
data/local_profiles.json
models/face_recognizer_lbph.yml
assets/guild_seals/*.png
```

Bu dosyalar Git dışında tutulur ve dağıtım doğrulayıcısı tarafından build içine alınmaları engellenir. Uygulama bulut hesabı veya uzak veritabanı kullanmaz. Paylaşmadan önce yüz görüntülerinin ve lonca mühürlerinin kişisel veri olduğunu göz önünde bulundurun.

## Testler

```powershell
python -m unittest
python -m py_compile app.py vision_engine.py runtime_paths.py auth\verification_session.py ui\main_window.py ui\camera_worker.py ui\frame_view.py enrollment\enrollment_manager.py
```

Manuel doğrulama için [Manuel Testler](docs/MANUAL_TESTS.md) listesini kullanın.

## Sınırlamalar

- LBPH; ışık, açı, kamera ve kayıt örneği kalitesinden etkilenir.
- QR/lonca mührü yerel prototip doğrulamasıdır; güvenli kimlik belgesi değildir.
- MediaPipe algılama ve hareket eşikleri farklı kamera/ışık koşullarında kalibrasyon gerektirebilir.
- Rütbe bilgisi bilgilendiricidir; kalıcı XP veya progression sistemi yoktur.
- Installer, kod imzalama ve public release otomasyonu henüz yoktur.

## Belgeler

- [Mimari](docs/ARCHITECTURE.md)
- [Manuel Testler](docs/MANUAL_TESTS.md)
- [Sorun Giderme](docs/TROUBLESHOOTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Demo Senaryosu](docs/DEMO_SCRIPT.md)
- [Windows Paketleme](docs/PACKAGING.md)
- [Demo Görsel Rehberi](docs/DEMO_ASSETS.md)

## Kısa Roadmap

Gelecek hedefleri; daha dayanıklı yüz tanıma, hareket kalibrasyonu, profil/veri yönetimi, otomatik GUI-performans testleri ve imzalı/yayımlanabilir Windows dağıtımıdır. Ayrıntılar için [Roadmap](docs/ROADMAP.md) belgesine bakın.
