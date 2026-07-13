# VisionForge Manuel Test Listesi

Bu liste source ve frozen uygulamanın güncel PySide6 sayfaları üzerinden doğrulanması içindir. Test verisi olarak yalnız paylaşımı ve işlenmesi uygun yüz/QR verileri kullanılmalıdır.

## 1. Otomatik Ön Kontrol

```powershell
python -m unittest
python -m py_compile app.py vision_engine.py runtime_paths.py auth\verification_session.py ui\main_window.py ui\camera_worker.py ui\frame_view.py enrollment\enrollment_manager.py
```

Beklenen: Komutlar hata vermeden tamamlanır.

## 2. Source Kurulum

1. Sanal ortamı oluşturup etkinleştirin.
2. `python -m pip install -r requirements.txt` çalıştırın.
3. `python tools\download_models.py` çalıştırın.
4. `python app.py` ile uygulamayı açın.

Beklenen:

- PySide6 penceresi özel VisionForge ikonuyla açılır.
- Ayrı bir ana OpenCV penceresi açılmaz.
- Canlı Görüş, Büyü Kitabı, Trial, Kayıt, Ayarlar, Sistem Durumu ve Debug navigasyonda görünür.

## 3. Kamera, FrameView ve Performans

1. Canlı Görüş sayfasını açın.
2. Çözünürlük rozetinin `640x480` olduğunu kontrol edin.
3. Pencereyi büyütüp minimum 1180×700 boyutuna kadar küçültün.
4. Kamera görüntüsünün gerilmediğini ve boş alanların letterbox olarak kaldığını doğrulayın.
5. Sayfalar arasında hızla geçerken kameranın ve UI'ın yanıt vermeye devam ettiğini gözleyin.
6. Debug → Genel sayfasında FPS, kamera okuma, pipeline, Qt dönüşümü ve UI frame aralığı değerlerini kontrol edin.
7. `Esc` ile kapatın.

Beklenen:

- Görüntü 640×480 işleme çözünürlüğünde ve oranı korunarak gösterilir.
- UI eski karelerden oluşan giderek büyüyen bir gecikme üretmez.
- Kapanışta kamera serbest bırakılır ve worker thread temiz kapanır.

## 4. Native Kayıt ve Yüz Eğitimi

### Canlı kamera

1. Kayıt sayfasında kullanıcı adı girin.
2. `Canlı Kamera` yöntemini seçip **Kayıt Başlat** düğmesine basın.
3. Düz, sağ, sol, yakın ve uzak aşamalarını izleyin.
4. Aşama/genel progress barlarını, kalite mesajını ve kabul/red sayılarını kontrol edin.
5. Tamamlanınca sonuç kartını ve lonca mührü yolunu doğrulayın.

### Fotoğraf içe aktarma

1. `Fotoğraf İçe Aktarma` yöntemini seçin.
2. **Klasör Seç** ile yüz görsellerini içeren klasörü seçin.
3. Kaydı başlatıp kabul/red özetini kontrol edin.

Beklenen:

- Kalitesiz, bulanık, küçük veya bulunamayan yüzler reddedilir.
- `data/face_gallery/`, `models/face_recognizer_lbph.yml`, `data/face_labels.json`, `data/local_profiles.json` ve kullanıcı mührü oluşur.
- Yeni yüz modeli uygulamayı yeniden başlatmadan kullanılabilir.
- **İptal / Sıfırla** aktif kaydı güvenli biçimde sonlandırır.

## 5. QR + Yüz Doğrulama

1. Ayarlar → Doğrulama modu alanından `QR + Yüz` seçin.
2. Kayıtlı yüzü stabil biçimde gösterin.
3. Lonca mührünü göstermeden Canlı Görüş durumunu kontrol edin.
4. Aynı kullanıcıya ait mührü kameraya gösterin.
5. Başka kullanıcıya ait veya geçersiz QR deneyin.

Beklenen:

- Yüz tek başına tam yetki açmaz; durum mühür beklediğini gösterir.
- Doğru mühür tam profili ve açık büyüleri etkinleştirir.
- Eşleşmeyen mühür tam yetki vermez ve hata bildirimi üretir.

## 6. Yalnızca Yüz Doğrulama

1. Ayarlar → Doğrulama modu alanından `Yalnızca Yüz` seçin.
2. Kayıtlı yüzü stabil biçimde gösterin.
3. Ayarı kapatıp uygulamayı yeniden açarak kalıcılığı kontrol edin.

Beklenen: QR gerekmeksizin tam profil açılır ve seçim `data/settings.json` içinde korunur.

## 7. Grace Period

1. Herhangi bir modda kullanıcıyı tam doğrulayın.
2. Yüzü kameradan çıkarın.
3. Canlı Görüş ve üst bardaki amber grace durumunu izleyin.
4. 10 saniye dolmadan aynı yüzle geri dönün.
5. Testi 10 saniyeden uzun bekleyerek tekrarlayın.
6. Mümkünse grace sırasında farklı kayıtlı yüz gösterin.

Beklenen:

- Profil ve yetkiler en fazla 10 saniye korunur.
- Aynı kullanıcı zamanında dönerse QR yeniden istenmez.
- Süre dolunca Misafir yetkisine dönülür.
- Farklı stabil kullanıcı eski oturumu devam ettirmez.

## 8. Donma, Ateş ve Kalkan

1. Donma için açık avucu sabit tutun.
2. Ateş için kontrollü yatay süpürme yapıp açık avuç gösterin.
3. Kalkan için iki açık eli aynı anda gösterin.
4. Her büyüde hazırlık, cooldown, bildirim ve kamera efektini kontrol edin.
5. Misafir profille Ateş ve Kalkanı deneyin.

Beklenen:

- Donma Misafir yetkisinde çalışır.
- Ateş ve Kalkan yalnız yetkili profilde çalışır.
- Tek el Kalkanı tetiklemez; optical flow tek başına Donma/Kalkan kararı vermez.
- Cooldown aynı büyünün arka arkaya spamlenmesini engeller.

## 9. Büyü Kitabı

1. Sol navigasyondan Büyü Kitabı sayfasını açın.
2. **Önceki** ve **Sonraki** ile kapak, Donma, Ateş ve Kalkan sayfalarını gezin.
3. Misafir ve tam doğrulanmış profil durumlarını karşılaştırın.

Beklenen:

- Kitap ayrı bir Qt sayfasında gösterilir.
- Her sayfada tür, tetikleme, etki, durum ve gereken rütbe görünür.
- Açık ve kilitli büyüler aktif yetkiyle eşleşir.

## 10. Trial

1. Trial sayfasını açın ve **Trial Başlat / Yeniden Başlat** düğmesine basın.
2. Donma → Ateş → Kalkan sırasını tamamlayın.
3. Sıra dışı büyü deneyin.
4. Yetkisiz profille kilitli adımları kontrol edin.

Beklenen:

- Aktif, tamamlanan, bekleyen ve yetki yetersiz adımlar ayrışır.
- Yanlış büyü ilerlemeyi sıfırlamaz.
- Üç adım sonunda Trial tamamlanır.

## 11. Ayarlar

1. El landmark, yüz kutusu, kamera aynalama ve büyü efektleri seçeneklerini değiştirin.
2. Doğrulama modunu ve `Hassas`, `Dengeli`, `Kararlı` algılama profillerini deneyin.
3. Uygulamayı kapatıp yeniden açın.

Beklenen: Seçimler motora uygulanır, kamera aynalama yalnız sunumu etkiler ve kalıcı ayarlar yeniden yüklenir.

## 12. Sistem Durumu

1. Sistem Durumu sayfasını açın.
2. **Yenile** düğmesine basın.
3. Kamera, iki MediaPipe modeli, LBPH modeli, etiketler, local profiller, yüz galerisi, lonca mühürleri ve label/profile eşleşmesini kontrol edin.
4. Opsiyonel yerel dosyalardan birinin olmadığı temiz kurulum durumunu doğrulayın.

Beklenen: Gerekli/opsiyonel durumlar uygulamayı çökertmeden hazır, eksik veya uyarı olarak görünür.

## 13. Debug

1. Debug sayfasındaki dört sekmeyi açın.
2. Genel sekmede performans ve çözünürlük değerlerini kontrol edin.
3. Yüz/Doğrulama sekmesinde stabil etiket, skor, QR ve session state değerlerini kontrol edin.
4. El/Tracker sekmesinde el sayısı, kaynak, kalite, brightness ve blur değerlerini kontrol edin.
5. Büyü/Trial sekmesinde aktif büyü, hazırlık, cooldown ve Trial değerlerini kontrol edin.

Beklenen: Değerler koyu teknik alanlarda güncellenir; uzun değerler tooltip ile okunabilir.

## 14. Frozen EXE

1. [Paketleme](PACKAGING.md) adımlarıyla onedir build alın.
2. `tools\verify_distribution.py dist\VisionForge` çalıştırın.
3. `dist\VisionForge\VisionForge.exe` dosyasını dağıtım klasörü içinde açın.
4. Kamera, sayfalar, kayıt, ayar kalıcılığı ve Esc kapanışını tekrar kontrol edin.
5. Klasörü yazılabilir başka bir konuma taşıyıp yeniden deneyin.

Beklenen: Özel ikon görünür, bundled yüz/el modelleri bulunur ve portable kullanıcı verileri EXE yanında oluşur.

## 15. Git ve Gizlilik

```powershell
git check-ignore -v data\settings.json data\local_profiles.json data\face_labels.json models\face_recognizer_lbph.yml
git check-ignore -v data\face_gallery\sample.png data\import_faces\sample.png assets\guild_seals\sample.png
.venv\Scripts\python.exe tools\verify_distribution.py dist\VisionForge
```

Beklenen:

- Yerel yüz, profil, ayar, eğitilmiş model ve lonca mührü Git dışında kalır.
- Dağıtım doğrulaması kişisel veri, geliştirme klasörü veya kaynak dosyası bulmaz.
- Public belgelerde kişisel dosya veya yerel kullanıcı verisine bağlantı yoktur.
