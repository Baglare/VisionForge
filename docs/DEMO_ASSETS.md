# VisionForge Demo Görsel Rehberi

Bu belge public README veya teknik belgelerde kullanılabilecek gerçek uygulama ekranlarının kapsamını tanımlar. Görseller hazır değilken Markdown içine placeholder veya kırık bağlantı eklenmemelidir.

Önerilen klasör:

```text
assets/demo/
```

## Görsel Kimlik

Güncel ekranlar PySide6 masaüstü uygulamasından alınmalıdır:

- Gece laciverti ana arka plan
- Koyu indigo kart yüzeyleri
- Kontrollü mor aktif/focus vurguları
- Lavanta başlık/rütbe detayları
- Ayrı amber uyarı, kırmızı hata ve soğuk yeşil başarı durumları

Legacy OpenCV ana pencere ve görüntü içine çizilmiş menü/panel görselleri kullanılmamalıdır.

## Önerilen Ekranlar

### 1. Canlı Görüş

- PySide6 pencere çerçevesi, sol navigasyon ve üst profil alanı görünmeli.
- Kamera görüntüsü, oturum, aktif büyü, Trial ve bildirim kartları aynı kadrajda olmalı.
- Paylaşılabilir yüz veya temsili profil kullanılmalı.

### 2. Büyü Kitabı

- Ayrı Qt sayfası ve arşiv navigasyonu görünmeli.
- Açık/kilitli durum, tetikleme, etki ve gereken rütbe alanları okunmalı.

### 3. Trial

- Tamamlanan, aktif, bekleyen ve yetki yetersiz adımların semantik renkleri ayrışmalı.
- Mümkünse 1/3 veya 2/3 ilerleme anı seçilmeli.

### 4. Kayıt

- Native kullanıcı adı/yöntem kontrolleri, aşama durumu ve iki progress bar görünmeli.
- Gerçek yerel dosya yolu, kullanıcı adı veya yüz örneği paylaşılmamalı.

### 5. Ayarlar

- Overlay checkbox'ları, doğrulama modu ve algılama profili görünmeli.
- Focus veya checked durumu kontrollü mor vurguya örnek olabilir.

### 6. Sistem Durumu

- Hazır ve eksik/opsiyonel kaynaklar birlikte anlaşılır görünmeli.
- Kullanıcıya özel dosya adları kadraja girmemeli.

### 7. Debug / Performans

- Genel sekmede FPS, 640×480 çözünürlük ve pipeline değerleri gösterilebilir.
- Makineye özel hassas dosya yolu veya kişisel veri bulunmamalı.

### 8. Büyü Efektleri

- Donma, Ateş ve Kalkan için ayrı Canlı Görüş kareleri alınabilir.
- El/yüz görüntüsü paylaşılacaksa açık izin ve uygun demo verisi kullanılmalı.

## Önerilen Dosya Adları

```text
assets/demo/01-live-view.png
assets/demo/02-spellbook.png
assets/demo/03-trial.png
assets/demo/04-enrollment.png
assets/demo/05-settings.png
assets/demo/06-system-status.png
assets/demo/07-debug-performance.png
assets/demo/08-freeze.png
assets/demo/09-fire.png
assets/demo/10-shield.png
```

## Yayın Öncesi Kontrol

1. Görselin güncel mor/indigo PySide6 arayüzünden alındığını doğrulayın.
2. Yüz, kullanıcı adı, QR/lonca mührü ve yerel yolları kişisel veri açısından inceleyin.
3. Görselin gerçekten repoda bulunduğunu kontrol edin.
4. Ancak bundan sonra README'ye göreli Markdown bağlantısı ekleyin.
