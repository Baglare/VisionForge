# VisionForge Mimari Notları

Bu belge VisionForge'un ana modüllerini ve çalışma zamanındaki veri akışını özetler. Amaç kod ayrıntısına boğmadan portfolyo sunumunda sistemin nasıl kurulduğunu açıklamaktır.

## Genel Sistem Yapısı

VisionForge PySide6 tabanlı bir masaüstü kabuğu içinde çalışır. `app.py` yalnızca Qt uygulamasını başlatır. Kamera okuma `ui/camera_worker.py` içinde ayrı thread'de yapılır; tek karelik görüntü işleme ve karar akışı `vision_engine.py` içinde toplanır.

Ana katmanlar:

- Kamera ve görüntü akışı.
- Yüz algılama ve yüz tanıma.
- QR/lonca mührü doğrulama.
- El algılama ve el takip durumu.
- Büyü motoru.
- Trial görev motoru.
- Demo rehberi.
- UI/effects çizim katmanı.
- Yerel veri ve ayar dosyaları.

## Kamera Akışı

Kamera okuma işlemi Qt ana thread'inde çalışmaz. `CameraWorker`, OpenCV kamera kaynağını açar, öncelikle 1280x720 çözünürlük ister, ham kareyi okur ve `VisionEngine` ile işler. Uygulamada iki ayrı kare kavramı bulunur:

- `processing_frame`: Algılama ve tanıma işlemleri için ham kamera karesi.
- `display_frame`: Kullanıcıya gösterilen, gerekirse aynalanan kare.

Bu ayrım sayesinde kamera aynalama sadece görsel deneyimi etkiler; yüz tanıma, QR okuma ve el algılama ham görüntü üzerinde çalışır. Qt tarafında `FrameView`, işlenmiş görüntüyü en-boy oranını bozmadan letterbox ile gösterir.

## Yüz Algılama

`detectors/face_detector.py`, MediaPipe Tasks Face Detector kullanır. Model dosyası:

```text
models/face_detector.tflite
```

Model yoksa uygulama çökmez; yüz algılama pasif kalır ve kullanıcı Sistem Durumu panelinde uyarı görür.

## Yüz Tanıma

`detectors/face_identity_detector.py`, OpenCV LBPH yüz tanıma modelini kullanır. Eğitim çıktıları:

```text
models/face_recognizer_lbph.yml
data/face_labels.json
```

Tahmin sırasında normal ve aynalanmış yüz kırpımı denenir. Daha iyi skor veren sonuç kullanılır. Tek karelik sonuçla profil değiştirilmez; kısa geçmiş içinde stabil etiket oluşması beklenir.

`identity_health.py`, model, label ve profil dosyalarının tutarlılığını kontrol eder. Label dosyasında olan her yüz etiketi demo veya local profil dosyasında bulunmalıdır.

## QR / Lonca Mührü Doğrulama

`detectors/guild_seal_detector.py`, OpenCV `QRCodeDetector` ile kameradaki QR/lonca mührünü okur. QR içeriği kullanıcı profilindeki `guild_seal_code` ile eşleşirse QR onayı verilir.

Doğrulama modları:

- `QR + Yüz`: Tam yetki için stabil yüz tanıma ve doğru QR gerekir.
- `Yalnızca Yüz`: Stabil yüz tanıma tam yetki için yeterlidir.

`auth/verification_session.py`, tam doğrulanan kullanıcı için 10 saniyelik yüz kaybı toleransını yönetir. Tolerans sırasında aynı kullanıcının profil, rütbe, açık büyü ve Trial yetkileri korunur. Aynı kullanıcı süre dolmadan geri dönerse QR tekrar istenmez. Başka kayıtlı kullanıcı stabil tanınırsa eski oturum iptal edilir.

## El Algılama

`detectors/hand_detector.py`, MediaPipe Tasks Hand Landmarker kullanır. Model dosyası:

```text
models/hand_landmarker.task
```

El algılama sonucu 21 landmark noktası, el sayısı ve sağ/sol bilgisi içerir. Kalkan gibi iki el isteyen kararlar raw MediaPipe el sonucuna dayanır.

## HandStateTracker

`tracking/hand_state_tracker.py`, raw el algılama sonucundan daha stabil bir takip durumu üretir:

- El merkezi.
- Yumuşatılmış el merkezi.
- El hızı.
- Kısa süreli kayıp toleransı.
- Optical flow tabanlı kısa hareket devamlılığı.
- Parlaklık, blur ve kadraj kenarı uyarıları.

Bu katman özellikle Ateş büyüsünde kontrollü yatay süpürme hareketinin daha kararlı izlenmesine yardım eder. Optical flow tek başına avuç açık veya Kalkan gibi kararları tetiklemez.

## SpellEngine

`spell_engine.py`, el verisini büyü kararlarına çevirir:

- Donma: Açık avuç ve sabitlik.
- Ateş: Kontrollü yatay süpürme + açık avuç mührü.
- Kalkan: İki gerçek açık el.

Yetki listesi aktif profile göre `app.py` tarafından verilir. Guest kullanıcı yalnızca Donma kullanabilir. Cooldown sistemi aynı anda birden fazla büyü tetiklenmesini engeller.

## TrialEngine

`trial_engine.py`, Mühürlü Kapı görevini yönetir. Görev sırası:

```text
Donma -> Ateş -> Kalkan
```

Doğru büyü ilerletir, yanlış büyü görevi sıfırlamaz. Tamamlandığında kısa süreli sonuç paneli ve bildirim gösterilir.

## DemoGuide

`demo_guide.py`, portfolyo demosu için adım adım yönlendirme sağlar. Gerçek sistemin yerine geçmez; sadece sıradaki demo adımını gösterir. Bazı olayları okuyarak otomatik ilerleyebilir:

- Büyü Kitabı açıldı.
- Donma, Ateş veya Kalkan tetiklendi.
- Trial başladı veya tamamlandı.

Manuel kontrol için `G`, `N`, `P` kısayolları kullanılır.

## UI / Effects Katmanı

`effects.py`, kamera görüntüsüyle doğrudan ilişkili overlay'leri çizer:

- Kafa üstü profil etiketi.
- Büyü efektleri.
- Yüz debug kutusu.
- El landmark çizimleri.

Profil, doğrulama, büyü, Trial, ayarlar, sistem durumu, debug ve bildirim bilgileri PySide6 panellerinde gösterilir. Eski OpenCV panel çizimleri gerektiğinde uyumluluk için korunur ancak ana pencere artık Qt tarafındadır.

Kullanıcıya görünen metinler Pillow tabanlı Unicode çizimle işlenir; Türkçe karakterler OpenCV `putText` sınırlamasına takılmaz.

## Veri Dosyaları ve Yerel Kullanıcı Verileri

Demo profilleri:

```text
data/profiles.json
```

Yerel kullanıcı verileri:

```text
data/local_profiles.json
data/face_gallery/
data/import_faces/
data/face_labels.json
models/face_recognizer_lbph.yml
assets/guild_seals/*.png
data/settings.json
```

Bu yerel dosyalar Git dışında tutulur.

## Modüller Arası Akış

1. `MainWindow` Qt kabuğunu açar.
2. `CameraWorker` ayrı thread'de kameradan ham kare okur.
3. `VisionEngine.process_frame()` ham kareyi işler.
4. `FaceDetector` yüz kutusunu üretir.
5. `FaceIdentityDetector` yüz kimliği tahmini yapar.
6. `GuildSealDetector` QR/lonca mührünü kontrol eder.
7. `VerificationSession` tam doğrulama ve grace period durumunu yönetir.
8. `guild_profile.py` aktif profil ve yetki kararına destek verir.
9. `HandDetector` el landmark verisini üretir.
10. `HandStateTracker` el takip kalitesini ve yumuşatılmış hareket bilgisini üretir.
11. `SpellEngine` büyü kararını verir.
12. `TrialEngine` aktif büyüye göre görev ilerlemesini günceller.
13. `DemoGuide` demo adımlarını günceller.
14. `VisionEngineResult` Qt tarafına görüntü, profil, yetki, debug ve bildirim bilgisini taşır.
15. `FrameView` görüntüyü oranı bozmadan gösterir; Qt panelleri durum bilgilerini günceller.
