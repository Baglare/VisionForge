# VisionForge Mimarisi

Bu belge güncel PySide6 uygulamasının çalışma zamanı, görüntü işleme ve Windows paketleme yapısını özetler.

## Katmanlar

- `app.py`: Yazılabilir klasörleri hazırlar, `QApplication` ve özel ikonu yükler, `MainWindow`'u açar.
- `ui/main_window.py`: Yedi Qt sayfasını, navigasyonu, kalıcı ayar kontrollerini ve worker yaşam döngüsünü yönetir.
- `ui/camera_worker.py`: Kamera ile `VisionEngine` işini ayrı `QThread` içinde yürütür.
- `vision_engine.py`: Tek karelik algılama, doğrulama, büyü, Trial, bildirim ve kayıt kararlarını birleştirir.
- `ui/frame_view.py`: Son `QImage` karesini en-boy oranını koruyarak gösterir.
- `runtime_paths.py`: Source ve frozen ortamlarında statik/yazılabilir yolları ayırır.

## Kamera ve Latest-frame Pipeline

`CameraWorker`, OpenCV kaynağını açar ve kameradan 640×480 görüntü ister. Her döngüde:

1. UI aksiyon kuyruğu boşaltılır.
2. Kameradan ham `processing_frame` okunur.
3. Kare `VisionEngine.process_frame()` ile işlenir.
4. Sonuç görüntüsü kopyalanmış bir `QImage`e çevrilir.
5. QImage ve durum payload'u kilit korumalı tek bir `_latest_frame` alanına yazılır.
6. Qt ana thread'i `take_latest_frame()` ile bu alanı alıp temizler.

Bu yaklaşım eski kareleri biriktirmez. UI bir kareyi atlayabilir ancak giderek büyüyen bir görüntü kuyruğunun gecikmesine maruz kalmaz. Kamera okuma, MediaPipe, LBPH, QR ve büyü işlemleri UI thread'inde çalışmaz. Kapanışta worker durdurulur, kamera serbest bırakılır ve thread için sınırlı süre beklenir.

## VisionEngine İşleme Çekirdeği

`VisionEngine` iki kare görünümünü ayırır:

- `processing_frame`: Yüz, QR ve el kararlarında kullanılan ham kamera karesi.
- `display_frame`: Kamera aynalama ve kullanıcıya gösterilecek overlay'ler için kullanılan kopya.

Ana işlem sırası:

```text
FaceDetector + FaceIdentityDetector
  → GuildSealDetector + VerificationSession
  → HandDetector + HandStateTracker
  → SpellEngine + TrialEngine
  → Effects/notifications/debug payload
  → VisionEngineResult
```

Kayıt aktifken normal büyü akışı yerine `EnrollmentManager` güncellenir. Kayıt tamamlandığında yerel yüz tanıma bileşeni yeniden yüklenir.

## Yüz, QR ve VerificationSession

- `FaceDetector`, bundled `models/face_detector.tflite` dosyasını kullanır.
- `FaceIdentityDetector`, yazılabilir alandaki LBPH modeli ve etiket dosyasını kullanır.
- Stabil kimlik kararı tek karelik tahmin yerine kısa geçmiş üzerinden oluşur.
- `GuildSealDetector`, OpenCV `QRCodeDetector` ile lonca mührünü profil koduyla eşleştirir.
- `VerificationSession`, `UNAUTHENTICATED`, `PENDING_SEAL`, `VERIFIED`, `GRACE_PERIOD` ve `EXPIRED` durumlarını yönetir.
- Grace period sabiti 10 saniyedir. Aynı kullanıcı dönerse oturum yenilenir; başka stabil kullanıcı eski oturumu sıfırlar.

## El Takibi, Büyüler ve Trial

`HandDetector`, `models/hand_landmarker.task` üzerinden 21 landmark, el sayısı ve handedness üretir. `HandStateTracker`; merkez, yumuşatılmış merkez, hız, optical-flow devamlılığı, parlaklık, blur ve kadraj uyarılarını hesaplar.

Optical flow tek başına avuç veya iki el doğrulaması değildir. `SpellEngine` Donma, Ateş ve Kalkan kararlarını gerçek algılama, takip durumu, yetki ve cooldown ile birleştirir. `TrialEngine` Donma → Ateş → Kalkan sırasını izler.

## Qt Sayfaları ve Kamera Overlay Ayrımı

`MainWindow` şu sayfaları içerir: Canlı Görüş, Büyü Kitabı, Trial, Kayıt, Ayarlar, Sistem Durumu ve Debug.

Qt tarafında navigasyon, kartlar, rozetler, formlar, progress barlar, sekmeler ve teknik değerler bulunur. Kamera pikseliyle doğrudan ilişkili profil etiketi, yüz/el debug çizimi ve büyü efektleri `effects.py` üzerinden `display_frame` üzerine çizilir. Büyü Kitabı ve Trial ayrı Qt sayfalarıdır.

`FrameView`, gelen QImage'i widget boyutuna göre letterbox eder; görüntüyü yatay veya dikey esnetmez.

## Native Qt Kayıt Akışı

Kayıt sayfası kullanıcı adı, kayıt yöntemi ve isteğe bağlı fotoğraf klasörünü Qt kontrollerinden alır. `EnrollmentManager.start_with_options()` mevcut motoru başlatır. Canlı kayıt 30 kabul edilmiş örneği beş aşamaya böler; fotoğraf importu kabul/red nedenlerini raporlar.

Tamamlama çıktıları LBPH modeli, etiket eşlemesi, local profil ve QR/lonca mührüdür. Bu çıktılar statik bundle kaynakları değildir.

## Source ve Frozen Yol Ayrımı

`runtime_paths.py` üç kök tanımlar:

| Yol | Source | Frozen |
| --- | --- | --- |
| `bundle_root()` | Repo kökü | PyInstaller `_MEIPASS` |
| `executable_root()` | Repo kökü | `VisionForge.exe` klasörü |
| `writable_app_root()` | Repo kökü | `VisionForge.exe` klasörü |

`static_resource_path()` bundled yüz/el modelleri ve uygulama ikonu için kullanılır. `writable_path()` ayarlar, yüz galerisi, import klasörü, LBPH modeli, etiketler, local profiller ve lonca mühürleri için kullanılır.

## PyInstaller onedir Yapısı

`packaging/VisionForge.spec`:

- `VisionForge.exe` için özel `assets/branding/visionforge.ico` ikonunu kullanır.
- İki MediaPipe modelini ve native `libmediapipe.dll` dosyasını bundle'a ekler.
- Qt Windows platform eklentilerini PyInstaller toplamasıyla taşır.
- `COLLECT` ile `dist/VisionForge/` onedir çıktısı üretir.

Kullanıcı verileri bundle'a eklenmez. `tools/verify_distribution.py`; zorunlu runtime dosyalarını doğrular ve yüz galerisi, local profiller, ayarlar, eğitilmiş model, lonca mührü, kaynak kodu veya geliştirme klasörleri bulunursa dağıtımı reddeder.

## Tema

Ortak QSS `ui/theme.py` içindedir. Ana arka plan gece laciverti; yüzeyler koyu indigo; marka ve focus vurguları kontrollü mor/lavanta kullanır. Uyarı, hata ve gerçek başarı renkleri marka morundan ayrı semantik rollerde tutulur.
