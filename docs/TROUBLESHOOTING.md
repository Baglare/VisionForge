# VisionForge Sorun Giderme

## Source Uygulama Açılmıyor

1. Proje klasöründe sanal ortamı etkinleştirin.
2. `python -m pip install -r requirements.txt` çalıştırın.
3. `python tools\download_models.py` çalıştırın.
4. `python app.py` ile yeniden deneyin.

`PySide6`, `cv2` veya `mediapipe` import hatası varsa komutun doğru sanal ortam Python'uyla çalıştığını doğrulayın.

## Kamera Açılamıyor

1. Kamera kullanan diğer uygulamaları kapatın.
2. Windows Ayarları'nda masaüstü uygulamaları için kamera iznini kontrol edin.
3. Canlı Görüş sayfasındaki kamera durumuna bakın.
4. Başka fiziksel/sanal kamera varsa varsayılan kamera sırasını kontrol edin.
5. Uygulamayı yeniden başlatın.

Worker kamerayı açamazsa UI hata durumu gösterir; kayıt ve canlı görüntü çalışmaz.

## Kamera Gecikiyor veya FPS Düşük

1. Debug → Genel sayfasında kamera okuma, pipeline, Qt dönüşümü ve UI frame aralığını kontrol edin.
2. Ayarlar'dan yüz/el debug çizimlerini kapatın.
3. Büyü efektlerini geçici olarak kapatıp karşılaştırın.
4. Algılama profilini `Dengeli` veya `Kararlı` yapın.
5. Kamerayı kullanan başka uygulamaları ve yoğun CPU süreçlerini kapatın.

VisionForge 640×480 işler ve yalnız en güncel kareyi gösterir. Yavaşlama eski kare kuyruğundan değil, kamera/algılama işlem süresinden kaynaklanmalıdır.

## Model Dosyası Eksik

Source ortamında:

```powershell
python tools\download_models.py
```

Ardından Sistem Durumu sayfasında **Yenile** düğmesine basın. Gerekli statik dosyalar:

```text
models/face_detector.tflite
models/hand_landmarker.task
```

## Source ve Frozen Model Yolları Farklı

- Source uygulama statik modelleri repo içindeki `models/` klasöründen okur.
- Frozen uygulama statik modelleri PyInstaller bundle içinden okur.
- Eğitilmiş LBPH modeli source'da repo köküne, frozen uygulamada EXE yanındaki `models/` klasörüne yazılır.

Source'daki kişisel LBPH modelini build içinde aramayın; kullanıcı verileri bilinçli olarak dağıtıma alınmaz.

## Yüz Tanıma Çalışmıyor

1. Sistem Durumu sayfasında yüz tanıma modeli, etiketler, local profiller ve label/profile eşleşmesini kontrol edin.
2. `python -c "import cv2; print(hasattr(cv2, 'face'))"` komutunun `True` verdiğini doğrulayın.
3. Aynı ortamda yalnız `opencv-contrib-python` bırakın; `opencv-python` ve headless varyantlarını kaldırın.
4. Kayıt sayfasından yeni, iyi aydınlatılmış bir kayıt oluşturun.

## QR/Lonca Mührü Okunmuyor

1. Ayarlar'da doğrulama modunun `QR + Yüz` olduğunu kontrol edin.
2. Kullanıcı yüzünün stabil tanındığından emin olun.
3. Mührü kameraya düz, yeterince büyük ve yansımasız gösterin.
4. Doğru kullanıcıya ait mühür dosyasını kullandığınızı kontrol edin.
5. Canlı Görüş veya Debug → Yüz/Doğrulama durumunu izleyin.

## El veya Büyü Algılama Zayıf

1. Işığı artırın ve eli kadrajın merkezine alın.
2. Debug → El/Tracker sekmesindeki brightness, blur, kadraj ve tracking source değerlerini kontrol edin.
3. Ateş hareketini hızlı savurma yerine kontrollü yatay süpürmeyle yapın.
4. Kalkan için iki açık elin de aynı anda ve birbirini kapatmadan göründüğünü doğrulayın.
5. İlgili büyünün profil yetkisinde açık olduğunu Büyü Kitabı'ndan kontrol edin.

## `settings.json` Bozuk

1. Uygulamayı kapatın.
2. Source'da repo kökündeki, frozen uygulamada EXE yanındaki `data\settings.json` dosyasını silin.
3. Uygulamayı yeniden açın.

Varsayılan ayarlar yeni dosyaya yazılır.

## Portable EXE Açılmıyor

1. Yalnız `VisionForge.exe` dosyasını taşımadığınızdan emin olun.
2. `dist\VisionForge\` klasörünün tamamını birlikte tutun.
3. Build makinesinde dağıtım doğrulayıcısını çalıştırın:

```powershell
.venv\Scripts\python.exe tools\verify_distribution.py dist\VisionForge
```

4. Antivirüs karantinasını ve eksik Qt/MediaPipe dosyalarını kontrol edin.
5. Gerekirse build'i temiz sanal ortamda yeniden alın.

## ZIP İçinden Çalıştırma

Uygulamayı ZIP arşivinin içinden çalıştırmayın. Tüm klasörü normal, yazılabilir bir konuma çıkarın ve EXE'yi oradan açın. Aksi durumda runtime dosyaları bulunamayabilir veya kullanıcı verileri yazılamayabilir.

## Yazma İzni Olmayan Klasör

Frozen uygulama ayar, kayıt, LBPH modeli ve lonca mührünü EXE yanında oluşturur. `Program Files`, salt okunur ağ klasörü veya yönetici izni gerektiren konumlarda bu işlemler başarısız olabilir.

1. Dağıtım klasörünü kullanıcının yazabildiği bir konuma taşıyın.
2. Klasörde yeni dosya oluşturabildiğinizi kontrol edin.
3. Kayıt veya ayar işlemini yeniden deneyin.

## Windows SmartScreen Uyarısı

Mevcut build kod imzalı değildir. SmartScreen bilinmeyen yayıncı uyarısı gösterebilir. Dosyayı yalnız güvenilen, kendi ürettiğiniz build'den çalıştırın. Public dağıtım için kod imzalama release aşamasında ele alınmalıdır.

## Eski İkon Görünüyor

1. Uygulamayı görev çubuğundan kaldırıp yeniden sabitleyin.
2. Eski EXE kısayolunu silip yeni build'den kısayol oluşturun.
3. `dist\VisionForge\` klasörünü yeniden build edin.
4. Gerekirse Windows Explorer'ı veya oturumu yeniden başlatın.

Windows ikon önbelleği eski EXE ikonunu bir süre gösterebilir; spec ve uygulama aynı `assets\branding\visionforge.ico` dosyasını kullanır.

## Yerel Verileri Temizleme

Uygulamayı kapattıktan sonra yalnız temizlemek istediğiniz portable kökte şu kullanıcı çıktıları kaldırılabilir:

```text
data/face_gallery/
data/import_faces/
data/face_labels.json
data/local_profiles.json
data/settings.json
models/face_recognizer_lbph.yml
assets/guild_seals/*.png
```

Bu işlem kayıtlı kullanıcıları ve yerel tanıma verisini geri alınamaz biçimde kaldırır.
