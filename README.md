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
