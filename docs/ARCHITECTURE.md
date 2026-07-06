# VisionForge Mimari Notları

Bu belge VisionForge'un ana modüllerini ve çalışma zamanındaki veri akışını özetler. Amaç kod ayrıntısına boğmadan portfolyo sunumunda sistemin nasıl kurulduğunu açıklamaktır.

## Genel Sistem Yapısı

VisionForge tek bir masaüstü kamera döngüsü etrafında çalışır. `app.py` ana orkestrasyon katmanıdır; kamera karesini okur, algılayıcıları çalıştırır, profil/yetki kararını verir, büyü motorunu günceller ve UI çizimlerini tek ekranda toplar.

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

`camera.py`, OpenCV kamera kaynağını açar, kare okur, pencereyi gösterir ve `Esc` ile temiz kapanışı destekler. Uygulamada iki ayrı kare kavramı bulunur:

- `processing_frame`: Algılama ve tanıma işlemleri için ham kamera karesi.
- `display_frame`: Kullanıcıya gösterilen, gerekirse aynalanan kare.

Bu ayrım sayesinde kamera aynalama sadece görsel deneyimi etkiler; yüz tanıma, QR okuma ve el algılama ham görüntü üzerinde çalışır.

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

`effects.py`, kamera görüntüsü üzerine UI katmanlarını çizer:

- Kafa üstü profil etiketi.
- Sol üst büyü paneli.
- Büyü efektleri.
- Büyü Kitabı.
- Trial paneli.
- Q ayar menüsü.
- Debug paneli.
- Sistem Durumu paneli.
- Bildirimler.
- Demo Rehberi paneli.

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

1. `Camera` ham kareyi okur.
2. `FaceDetector` yüz kutusunu üretir.
3. `FaceIdentityDetector` yüz kimliği tahmini yapar.
4. `GuildSealDetector` QR/lonca mührünü kontrol eder.
5. `guild_profile.py` aktif profil ve yetki kararına destek verir.
6. `HandDetector` el landmark verisini üretir.
7. `HandStateTracker` el takip kalitesini ve yumuşatılmış hareket bilgisini üretir.
8. `SpellEngine` büyü kararını verir.
9. `TrialEngine` aktif büyüye göre görev ilerlemesini günceller.
10. `DemoGuide` demo adımlarını günceller.
11. `Effects` tüm görsel katmanları `display_frame` üzerine çizer.
