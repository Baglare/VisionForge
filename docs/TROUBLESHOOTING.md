# VisionForge Sorun Giderme

Bu belge demo öncesi sık karşılaşılan sorunları hızlıca ayırmak için hazırlanmıştır.

## Kamera açılmıyor

Olası nedenler:
- Kamera başka bir uygulama tarafından kullanılıyor olabilir.
- Varsayılan kamera kapalı veya sistem tarafından engellenmiş olabilir.
- Sanal ortam yanlış Python kurulumu ile açılmış olabilir.

Çözüm:
1. Kamera kullanan diğer uygulamaları kapat.
2. Windows kamera izinlerini kontrol et.
3. Proje klasöründe doğru sanal ortamı etkinleştir.
4. `python app.py` komutunu yeniden çalıştır.

## Model dosyası eksik

Gerekli dosyalar:
- `models/face_detector.tflite`
- `models/hand_landmarker.task`

Yerel eğitimden sonra oluşan dosyalar:
- `models/face_recognizer_lbph.yml`
- `data/face_labels.json`
- `data/local_profiles.json`

Çözüm:
1. Sistem Durumu panelini `Q > 8` ile aç.
2. Gerekli MediaPipe modellerini otomatik indirmek için şu komutu çalıştır:

```powershell
python tools/download_models.py
```

3. Script başarısız olursa dosyaları manuel olarak ilgili `models/` konumuna koy.
4. Yüz tanıma modeli eksikse `E` ile kayıt oluştur.

## Türkçe karakterler bozuk görünürse

Belirti:
- `Büyü Kitabı`, `Şimşek`, `Alan Mührü`, `S-Seviye Büyücü` gibi metinler `?` karakterleriyle görünür.

Çözüm:
1. Pillow bağımlılığının kurulu olduğunu kontrol et.
2. Windows fontlarından `segoeui.ttf`, `arial.ttf` veya `calibri.ttf` erişilebilir olmalı.
3. Sorun devam ederse sanal ortamı yeniden kurup `pip install -r requirements.txt` çalıştır.

## Yüz tanıma çalışmıyor

Olası nedenler:
- `opencv-contrib-python` yerine `opencv-python` kurulu olabilir.
- `cv2.face` modülü yoktur.
- `face_recognizer_lbph.yml` ve `face_labels.json` uyumsuzdur.
- Label dosyasında görünen kullanıcı profil dosyalarında yoktur.

Çözüm:
1. `python -c "import cv2; print(hasattr(cv2, 'face'))"` komutunun True verdiğini kontrol et.
2. `Q > 8` Sistem Durumu panelinde model, label ve profil uyumunu kontrol et.
3. Gerekirse `E` ile yeniden kayıt yap.
4. OpenCV paket çakışması varsa aynı ortamda yalnızca `opencv-contrib-python` bırak.

## QR okunmuyor

Olası nedenler:
- QR görüntüsü çok küçük veya bulanık olabilir.
- Ekran parlaklığı düşük olabilir.
- QR kameraya açılı veya yansımalı gösteriliyor olabilir.

Çözüm:
1. QR dosyasını telefonda tam ekran aç.
2. Telefon parlaklığını artır.
3. QR'ı kameraya daha düz ve daha yakın göster.
4. QR dosyasının `assets/guild_seals/<username>_seal.png` konumunda oluştuğunu kontrol et.

## El algılama zayıf

Olası nedenler:
- Ortam ışığı düşük olabilir.
- El kadraj kenarında kalıyor olabilir.
- Hareket bulanıklığı oluşuyor olabilir.
- `models/hand_landmarker.task` eksik olabilir.

Çözüm:
1. Işığı artır.
2. Eli kadrajın merkezine al.
3. Hareketi biraz yavaşlat.
4. Debug panelinde `D` ile El / Tracker sayfasına geçip kalite uyarılarını kontrol et.

## Ateş büyüsü tetiklenmiyor

Beklenen hareket:
- Eli kadraj içinde kontrollü yatay süpür.
- Ardından açık avuç göster.

Çözüm:
1. Çok hızlı savurma yerine daha kontrollü yatay hareket yap.
2. Elini kadraj dışına çıkarmamaya çalış.
3. Tam doğrulanmış kullanıcı olduğundan veya Ateş yetkisinin açık olduğundan emin ol.
4. Debug panelinde Büyü / Trial sayfasında `fire_state`, `fire_travel_distance` ve `fire_required_distance` değerlerini kontrol et.

## Kalkan için iki el algılanmıyor

Beklenen hareket:
- İki açık el aynı anda kamerada görünmeli.

Çözüm:
1. İki eli de kadraj içine al.
2. Elleri yüzün veya birbirinin üstüne bindirme.
3. `Q > 1` ile el debug çizimini aç.
4. Debug panelinde El / Tracker sayfasında `raw_hand_count` değerinin 2 olduğunu kontrol et.

## Loş ışık veya motion blur problemi

Belirti:
- El veya yüz takibi sık kaybolur.
- Debug panelinde `Işık düşük` veya `Görüntü bulanık` uyarısı görünür.

Çözüm:
1. Ortam ışığını artır.
2. Kameraya biraz daha yaklaş.
3. Eli daha yavaş hareket ettir.
4. Kamera lensini temizle.

## opencv-python ve opencv-contrib-python çakışması

Belirti:
- `cv2.face` yoktur.
- OpenCV modülleri eksik veya beklenmedik davranır.

Çözüm:
1. Aynı sanal ortamda birden fazla OpenCV paketi bırakma.
2. `opencv-python` ve headless varyantlarını kaldır.
3. `opencv-contrib-python` paketini requirements ile kur.

Not:
- Proje LBPH yüz tanıma için `opencv-contrib-python` ister.

## settings.json bozulursa

Belirti:
- Ayarlar yüklenemeyebilir veya uygulama varsayılan davranışa dönebilir.

Çözüm:
1. Uygulamayı kapat.
2. `data/settings.json` dosyasını sil.
3. Uygulamayı yeniden başlat.

Beklenen sonuç:
- Dosya varsayılan ayarlarla yeniden oluşturulur.

## Yerel veri temizliği

Kullanıcı verilerini temizlemek için şu yerel çıktılar silinebilir:
- `data/face_gallery/`
- `data/import_faces/`
- `models/face_recognizer_lbph.yml`
- `data/face_labels.json`
- `data/local_profiles.json`
- `assets/guild_seals/*.png`

Not:
- Bu dosyalar Git dışında tutulur.
- `assets/guild_seals/.gitkeep` klasörün repoda kalması için tutulur.
