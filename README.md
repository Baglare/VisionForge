# VisionForge

VisionForge, kamera üzerinden yüz ve el algılayan; kullanıcıyı yerel yüz tanıma ve lonca mührüyle doğrulayan; el hareketlerini büyü komutlarına çeviren modern lonca temalı interaktif görüntü işleme prototipidir.

Bu proje profesyonel güvenlik sistemi değildir. Amaç, yerel çalışan ve portfolyoda gösterilebilir bir masaüstü bilgisayarlı görü deneyimi oluşturmaktır.

## VisionForge Nedir?

VisionForge; OpenCV, MediaPipe Tasks, yerel LBPH yüz tanıma, QR tabanlı lonca mührü doğrulama ve el landmark verisini birleştiren Python tabanlı bir masaüstü uygulamasıdır. Kamera görüntüsü üzerinde profil etiketi, Büyü Kitabı, büyü efektleri, Trial Mode, Demo Rehberi, ayarlar, debug ve sistem durumu panelleri çalışır.

Ana fikir, klasik webcam demosunu oyunlaştırılmış bir lonca arayüzüne dönüştürmektir: kullanıcı kamerada algılanır, yerel profil yetkisi belirlenir, el hareketleri Donma, Ateş ve Kalkan büyülerine çevrilir.

## Temel Özellikler

- Canlı OpenCV kamera akışı.
- MediaPipe Tasks Face Detector ile yüz var/yok algılama.
- OpenCV LBPH ile yerel yüz tanıma.
- QR/lonca mührü ile ikinci doğrulama katmanı.
- MediaPipe Tasks Hand Landmarker ile el landmark algılama.
- HandStateTracker ile el merkezi, kısa kayıp toleransı ve debug amaçlı takip kalitesi.
- Donma, Ateş ve Kalkan büyüleri.
- Yetkiye göre açık/kilitli büyü sistemi.
- Büyü Kitabı: kapak + iki sayfa görünümü, sayfa başına bir büyü.
- Mühürlü Kapı Trial Mode: Donma -> Ateş -> Kalkan sıralı görev.
- Demo Rehberi: portfolyo demosu için adım adım yönlendirme.
- Q menüsü, kalıcı ayarlar, debug sayfaları ve sistem durumu paneli.
- Türkçe karakter destekli UI metin çizimi.
- Kısa bildirim/toast sistemi.

## Demo Akışı

1. Uygulamayı başlat.
2. Q menüsü ve Sistem Durumu panelini kısa göster.
3. Kayıtlı kullanıcı yoksa E ile kayıt/eğitim akışını başlat veya hazır kayıt olduğunu açıkla.
4. Yüz tanıma sonucunu ve kafa üstü profil/lonca etiketini göster.
5. QR + Yüz modunda lonca mührünü göster veya Q > 3 ile Yalnızca Yüz moduna geç.
6. B ile Büyü Kitabı'nı aç, sağ/sol oklarla büyü sayfalarını gez.
7. Donma: açık avuç sabit.
8. Ateş: kontrollü yatay süpürme + avuç gösterme.
9. Kalkan: iki açık el.
10. T ile Mühürlü Kapı Trial Mode'u başlat.
11. Donma -> Ateş -> Kalkan sırasıyla kapıyı aç.
12. G ile Demo Rehberi'ni açıp portfolyo akışını özetle.

Detaylı video senaryosu için [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) dosyasına bak.

## Kurulum

Python 3.12 veya 3.13 önerilir. OpenCV tarafında contrib paketi gerekir; `opencv-python` ve `opencv-contrib-python` aynı ortamda birlikte tutulmamalıdır.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python tools/download_models.py
python app.py
```

Kurulum sırası:
1. Sanal ortam oluştur ve etkinleştir.
2. `requirements.txt` bağımlılıklarını kur.
3. `python tools/download_models.py` ile gerekli MediaPipe modellerini indir.
4. `python app.py` ile uygulamayı başlat.

## Gerekli Model Dosyaları

Model dosyaları Git'e dahil edilmez. Önerilen kolay yol:

```powershell
python tools/download_models.py
```

Bu komut şu dosyaları indirip doğru konuma koyar:

```text
models/face_detector.tflite
models/hand_landmarker.task
```

İstersen dosyaları manuel olarak aynı konumlara da yerleştirebilirsin. Script mevcut dosyayı tekrar indirmez; eksik veya indirilemeyen model için terminalde anlaşılır mesaj verir.

Kayıt/eğitim sonrasında uygulama yerel olarak şu dosyaları üretir:

```text
models/face_recognizer_lbph.yml
data/face_labels.json
data/local_profiles.json
assets/guild_seals/<username>_seal.png
```

Eksik model veya profil dosyaları uygulamayı çökertmez; Sistem Durumu panelinde uyarı olarak gösterilir.

## Kullanıcı Kaydı / Yüz Eğitimi

E tuşu yeni büyücü kaydını başlatır. Kayıt iki kaynaktan yapılabilir:

- Canlı kamera kaydı.
- Fotoğraf import: `data/import_faces/<username>/`.

Canlı kayıt rehberli aşamalarla ilerler:

- Düz bak.
- Hafif sağa dön.
- Hafif sola dön.
- Biraz yaklaş.
- Biraz uzaklaş.

Her aşamada kaliteli örnek alınmadan ilerlenmez. Yüz çok küçükse, bulanıksa, kadraj kenarındaysa veya algılama skoru düşükse örnek reddedilir. Eğitim tamamlanınca LBPH modeli, label dosyası, local profil ve QR/lonca mührü üretilir. Kayıt bitince yüz tanıma modeli uygulama kapanmadan yeniden yüklenir.

## QR / Lonca Mührü Doğrulama

Varsayılan doğrulama modu `QR + Yüz` modudur.

- Tanınmayan yüz: Misafir Büyücü, yalnızca Donma.
- Tanınan yüz + QR yok: sınırlı yetki, lonca mührü beklenir.
- Tanınan yüz + doğru QR: tam profil ve profilin açık büyüleri.
- Yanlış QR: tam yetki verilmez.

Q menüsünde `3` tuşu ile `QR + Yüz` ve `Yalnızca Yüz` modları arasında geçiş yapılır. Yalnızca Yüz modunda kayıtlı yüz stabil tanınırsa QR gerekmeden tam profil açılır.

## Büyüler

| Büyü | Tetikleme | Yetki |
| --- | --- | --- |
| Donma | Avucu açık ve sabit tut | Misafir ve üzeri |
| Ateş | Kontrollü yatay süpürme + avuç göster | S-Seviye profil |
| Kalkan | İki açık el göster | S-Seviye profil |

Cooldown sistemi büyü spamlenmesini engeller. Kilitli büyü denenirse efekt başlatılmaz ve kısa bildirim gösterilir.

## Trial Mode

Mühürlü Kapı görevi T tuşuyla başlar. Görev sırası sabittir:

```text
Donma -> Ateş -> Kalkan
```

Doğru büyü yapıldığında mühür ilerler. Yanlış büyü görevi sıfırlamaz. Tüm sıra tamamlanırsa `Kapı Açıldı` ve `Trial tamamlandı` mesajları görünür.

## Demo Rehberi

G tuşu Demo Rehberi'ni açar/kapatır. Rehber, portfolyo sunumunda sıradaki adımı gösteren küçük bir paneldir; gerçek sistem davranışının yerine geçmez.

- G: Demo Rehberi aç/kapat.
- N: sonraki demo adımı.
- P: önceki demo adımı.

Rehber adımları: Kamera ve profil, Doğrulama, Büyü Kitabı, Donma, Ateş, Kalkan, Trial Mode, Trial tamamlama, Final. Otomatik tamamlanan adımlar kısa süre görünür kalır.

## Kısayollar

| Tuş | İşlev |
| --- | --- |
| Q | Ayar menüsünü aç/kapat |
| Esc | Uygulamadan çık |
| E | Kayıt/eğitim başlat |
| B | Büyü Kitabı aç/kapat |
| H | El landmark/debug çizimi aç/kapat |
| R | Doğrulama oturumunu sıfırla |
| T | Trial Mode başlat/yeniden başlat |
| G | Demo Rehberi aç/kapat |
| N / P | Demo adımı ileri/geri |
| D | Debug paneli açıkken debug sayfası değiştir |
| Sağ/Sol ok | Büyü Kitabı sayfalarını değiştir |
| 1-9 / 0 | Q menüsü açıkken ayarları değiştir |

## Sistem Sınırlamaları

- Profesyonel güvenlik sistemi değildir.
- LBPH yüz tanıma ışık, açı ve kamera kalitesinden etkilenebilir.
- QR doğrulama yerel prototip amaçlıdır.
- Loş ışık veya hareket bulanıklığı el takibini zayıflatabilir.
- MediaPipe model dosyaları kullanıcı tarafından yerleştirilmelidir.
- Veriler yerelde tutulur; online hesap, bulut veya veritabanı sistemi yoktur.
- Büyü/rütbe sistemi prototip düzeyindedir; gerçek progression sistemi yoktur.

## Portfolyo Değeri

VisionForge, tek bir kamera penceresi içinde bilgisayarlı görü, kullanıcı doğrulama, el landmark analizi, gerçek zamanlı UI, oyunlaştırılmış görev akışı ve yerel veri yönetimini birleştirir. Proje; yalnızca "webcam açıldı" seviyesinde kalmaz, kullanıcı profili, yetki, spellbook, trial ve demo rehberiyle uçtan uca bir prototip deneyimi sunar.

## Roadmap

Kısa roadmap için [docs/ROADMAP.md](docs/ROADMAP.md) dosyasına bak. Özet hedefler:

- Daha iyi yüz tanıma modeli.
- Face Landmarker ile kafa yönü kontrolü.
- Büyü kalibrasyon modu.
- Daha gelişmiş hareket zincirleri.
- Rütbe/level ve lonca ilerleme sistemi.
- Daha sinematik Trial Mode.
- Paketlenmiş masaüstü sürüm.

## Belgeler

- [Mimari notları](docs/ARCHITECTURE.md)
- [Demo video senaryosu](docs/DEMO_SCRIPT.md)
- [Demo görsel rehberi](docs/DEMO_ASSETS.md)
- [Sorun giderme](docs/TROUBLESHOOTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Manuel test listesi](docs/MANUAL_TESTS.md)

Demo görselleri eklenecekse [docs/DEMO_ASSETS.md](docs/DEMO_ASSETS.md) rehberini takip et.
