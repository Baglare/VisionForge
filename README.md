# VisionForge

VisionForge, kamera karşısındaki kullanıcıyı algılamayı, kullanıcıya modern lonca temalı bir profil göstermeyi ve ilerleyen aşamalarda el hareketlerinden büyü komutları üretmeyi hedefleyen Python tabanlı bir masaüstü görüntü işleme projesidir.

Bu ilk sürüm yalnızca temiz ve genişletilebilir bir proje iskeleti içerir. Gerçek yüz tanıma, el hareketi tanıma, büyü animasyonu veya karmaşık görüntü işleme henüz eklenmemiştir.

## Klasor Yapisi

```text
VisionForge/
|-- .gitignore
|-- app.py
|-- camera.py
|-- effects.py
|-- guild_profile.py
|-- requirements.txt
|-- spell_engine.py
|-- data/
|   `-- profiles.json
`-- detectors/
    |-- face_detector.py
    `-- hand_detector.py
```

## Bileşenler

- `app.py`: Projenin ana çalışma dosyasıdır.
- `camera.py`: Kamera akışının ileride yönetileceği temel sınıftır.
- `detectors/face_detector.py`: Yüz algılama iskeletini barındırır.
- `detectors/hand_detector.py`: El hareketi algılama iskeletini barındırır.
- `spell_engine.py`: Hareketlerden büyü komutları üretme mantığı için ayrılmıştır.
- `guild_profile.py`: Lonca profili verisini yükler ve temsil eder.
- `effects.py`: Profil ve büyü efektleri için genişletilebilir yer tutucudur.
- `data/profiles.json`: Örnek kullanıcı profilini içerir.
- `.gitignore`: Yerel Python, sanal ortam, cache ve çıktı dosyalarını Git dışında tutar.

## İkinci Aşama: Kamera Modu

Bu aşamada uygulama varsayılan kamerayı OpenCV ile açar ve canlı görüntünün üzerine basit bir lonca profil paneli çizer.

Panelde örnek `baglare` profili, rütbe, açık büyüler ve kamera modu durumu gösterilir. Çıkış için kamera penceresindeyken `q` veya `Esc` tuşuna basın.

## Üçüncü Aşama: Yüz Algılama

Bu aşamada uygulama MediaPipe Tasks Face Detector ile kamera görüntüsünde yüz olup olmadığını algılar. Eski `mp.solutions.face_detection` API'si kullanılmaz.

Yüz algılama model dosyası şu konuma elle yerleştirilmelidir:

```text
models/face_detector.tflite
```

Model dosyası yoksa uygulama çökmez; kamera modu çalışır, panelde yüz algılamanın pasif olduğu gösterilir ve terminalde kısa bir uyarı yazılır.

Model dosyası varsa yüz algılama sonucu birkaç karelik kararlılık filtresinden geçirilir. Böylece tek karelik yanlış pozitif sonuçlar profil durumunu aktif etmez ve ekranda rastgele yanıp sönen kutu çizilmez.

## Dördüncü Aşama: El Algılama

Bu aşamada uygulama MediaPipe Tasks Hand Landmarker ile kamera görüntüsünde el landmark noktalarını algılar. Eski `mp.solutions.hands` API'si kullanılmaz.

El algılama model dosyası şu konuma elle yerleştirilmelidir:

```text
models/hand_landmarker.task
```

Model dosyası yoksa uygulama çökmez; kamera modu, profil paneli ve yüz algılama çalışmaya devam eder, el algılama pasif kalır.

Model dosyası varsa kamera görüntüsünde el üzerinde 21 landmark noktası ve sade bağlantı çizgileri gösterilir. Panelde `El Durumu: El algılandı`, el yoksa `El Durumu: El bekleniyor` bilgisi görünür.

## Beşinci Aşama: Donma Büyüsü

Bu aşamada ilk basit büyü sistemi eklenmiştir. Kullanıcı açık avucunu kameraya gösterip yaklaşık `0.8` saniye sabit tuttuğunda `Donma` büyüsü tetiklenir.

Büyü aktifken panelde `Aktif Büyü: Donma` bilgisi görünür ve kamera görüntüsünün üzerinde kısa süreli mavi/soğuk tonlu Donma efekti gösterilir. Büyü tetiklendikten sonra yaklaşık `2` saniyelik bekleme süresi uygulanır.

Bu aşama yalnızca ilk MVP büyü davranışını içerir; hareket zinciri, farklı büyüler veya kişi tanıma eklenmemiştir.

## Altıncı Aşama: Ateş Büyüsü

Bu aşamada ilk hareket zinciri büyüsü eklenmiştir. Kullanıcı elini kısa süre içinde belirgin şekilde yatay savurup ardından açık avuç gösterdiğinde `Ateş` büyüsü tetiklenir.

Donma büyüsü açık ve sabit avuç ile çalışmaya devam eder. Ateş büyüsü ise savurma hareketi ve ardından açık avuç mührü ister. Aktif büyü veya bekleme süresi varken yeni büyü başlatılmaz.

Ateş aktifken panelde `Aktif Büyü: Ateş` bilgisi görünür ve kamera görüntüsünde kısa süreli kırmızı/turuncu parlama efekti gösterilir.

## Yedinci Aşama: Kalkan Büyüsü

Bu aşamada iki el algılamaya dayalı `Kalkan` büyüsü eklenmiştir. Kullanıcı iki açık avucunu kameraya yaklaşık `0.8` saniye gösterdiğinde Kalkan tetiklenir.

Mevcut büyü tetiklemeleri:

- `Donma`: Açık avuç kısa süre sabit tutulur.
- `Ateş`: El belirgin yatay savrulur, ardından açık avuç gösterilir.
- `Kalkan`: İki açık el kısa süre birlikte gösterilir.

Aktif büyü veya bekleme süresi varken yeni büyü başlatılmaz. Kalkan aktifken panelde `Aktif Büyü: Kalkan` görünür ve kamera görüntüsünde kısa süreli koruma halkası efekti gösterilir.

## Sekizinci Aşama: Büyü Defteri ve Arayüz

Bu aşamada kamera üzerindeki arayüz toparlanmıştır. Sol üstte kompakt lonca/profil kartı, altında aktif büyü ve cooldown alanı, sağ tarafta ise Büyü Defteri paneli gösterilir.

Büyü Defteri açık büyüleri ve kilitli büyüleri profil verisinden okur. Açık büyüler:

- `Donma`: Avucu açık tut
- `Ateş`: Yatay savur + avuç göster
- `Kalkan`: İki açık el göster

Kilitli büyüler: `Şimşek`, `Alan Mührü`, `Zaman Kırığı`.

Klavye kısayolları:

- `B`: Büyü Defteri panelini açar/kapatır.
- `H`: El landmark/debug çizimini açar/kapatır.
- `q` veya `Esc`: Uygulamayı kapatır.

## Dokuzuncu Aşama: Büyücü Kaydı ve Lonca Mührü

Bu aşamada uygulama içinden yerel kullanıcı kaydı, yüz örneği toplama, LBPH yüz tanıma eğitimi ve QR tabanlı lonca mührü doğrulaması eklenmiştir.

Bu sistem profesyonel güvenlik sistemi değildir. Portfolyo amaçlı, yerelde çalışan, kamera tabanlı bir doğrulama prototipidir.

Normal kullanıcı akışı:

1. `python app.py` ile uygulamayı aç.
2. `E` ile yeni büyücü kaydını başlat.
3. Kullanıcı adını gir.
4. Kameraya bakarak yüz örneklerinin alınmasını bekle.
5. Oluşturulan QR/lonca mührünü sakla.
6. Sonraki girişte yüz + kendi lonca mührün ile tam doğrulan.

Doğrulama davranışı:

- Yüz yoksa profil beklemede kalır.
- Tanınmayan yüz `Misafir Büyücü` olur ve yalnızca `Donma` kullanabilir.
- Yüz tanınır ama lonca mührü okunmazsa tam yetki verilmez.
- Yüz ve doğru lonca mührü birlikte doğrulanırsa kullanıcının tam profili açılır.
- Başka kullanıcıya ait mühür gösterilirse tam yetki verilmez.

Klavye kısayolları:

- `E`: Yeni büyücü kaydı / yüz eğitimi başlatır.
- `R`: Doğrulama oturumunu sıfırlar.
- `B`: Büyü Defteri panelini açar/kapatır.
- `H`: El landmark/debug çizimini açar/kapatır.
- `q` veya `Esc`: Uygulamayı kapatır.

Yerel yüz verileri ve kullanıcı QR dosyaları şu konumlarda saklanır:

```text
data/face_gallery/
models/face_recognizer_lbph.yml
data/face_labels.json
data/local_profiles.json
assets/guild_seals/
```

Bu verileri silerek yerel yüz eğitimini ve kullanıcı kayıtlarını temizleyebilirsin. Otomatik üretilen kullanıcı QR dosyaları ve yüz eğitim verileri Git dışında tutulur.

## Kurulum

Python 3.12 veya 3.13 kullanılması önerilir. Python 3.14 ile gelen OpenCV 5 paketinde bu aşamada kullanılan bazı klasik OpenCV yüz algılama API'leri bulunmayabilir.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Çalıştırma

```powershell
python app.py
```

Komut çalıştığında kamera penceresi açılır ve canlı görüntünün üzerinde örnek lonca profil paneli gösterilir.
