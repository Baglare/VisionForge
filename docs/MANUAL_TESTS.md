# VisionForge Manuel Test Listesi

Bu doküman demo öncesi elde çalıştırılacak kısa kontrol listesidir. Testler gerçek kamera, yerel model dosyaları ve mevcut kullanıcı kaydı durumuna göre uygulanır.

## Kurulum testi

Adımlar:
1. Proje klasöründe sanal ortamı etkinleştir.
2. `pip install -r requirements.txt` komutunu çalıştır.
3. `python -m py_compile app.py camera.py effects.py guild_profile.py spell_engine.py trial_engine.py settings_manager.py system_status.py` komutunu çalıştır.

Beklenen sonuç:
- Bağımlılıklar yüklenir.
- Python sözdizimi hatası alınmaz.

## Kamera testi

Adımlar:
1. `python app.py` ile uygulamayı başlat.
2. Kamera penceresinin açıldığını kontrol et.
3. `Esc` tuşuna bas.

Beklenen sonuç:
- Kamera görüntüsü gelir.
- Uygulama `Esc` ile temiz kapanır.
- `q` veya `Q` çıkış yapmaz, ayar menüsünü açar/kapatır.

## Yüz/el algılama testi

Adımlar:
1. `models/face_detector.tflite` ve `models/hand_landmarker.task` dosyalarının yerinde olduğundan emin ol.
2. Uygulamayı aç.
3. `Q` menüsünden `2` ile yüz kutusu çizimini aç.
4. `Q` menüsünden `1` ile el landmark çizimini aç.
5. `Q` menüsünden `5` ile Debug Sayfası'nı aç.
6. `D` ile El / Tracker sayfasına geç.
7. Kameraya yüzünü ve elini göster.

Beklenen sonuç:
- Yüz algılanırsa yüz kutusu doğru konumda görünür.
- El algılanırsa landmark çizimi elde görünür.
- El görünürken `raw_hand_detected` True ve `tracking_source` mediapipe görünür.
- El kısa süre kaybolursa `tracking_source` kısa süre optical_flow olabilir, uzun kayıpta lost olur.
- Loş ışık, bulanıklık veya kadraj kenarı sorunları `quality_warnings` içinde görünür.
- Model eksikse uygulama çökmez, ilgili algılama pasif kalır.

## Kayıt/eğitim testi

Adımlar:
1. Uygulamayı aç.
2. `E` ile kayıt akışını başlat.
3. Kullanıcı adını gir.
4. Canlı kamera veya görsel import seçeneğini kullan.
5. Canlı kayıt seçildiyse aşamaları sırayla takip et: düz bak, hafif sağa dön, hafif sola dön, biraz yaklaş, biraz uzaklaş.
6. Kayıt ekranında aşama adı, aşama içi örnek sayısı, toplam örnek sayısı ve kalite durumunu kontrol et.
7. Eğitim tamamlanana kadar yönlendirmeleri takip et.

Beklenen sonuç:
- Kötü örneklerde yüz bulunamadı, yüz çok küçük, kamera ortasına gel veya görüntü bulanık gibi kısa mesajlar görünür.
- Kaliteli örnek alınmadan aşama ilerlemez.
- Yüz örnekleri `data/face_gallery/` altında oluşur.
- Örnek dosya adları aşama bilgisini içerir.
- Görsel import seçilirse kötü fotoğraflar reddedilir ve kabul/red raporu görünür.
- LBPH modeli `models/face_recognizer_lbph.yml` olarak kaydedilir.
- Etiketler `data/face_labels.json` içine yazılır.
- Yerel profil `data/local_profiles.json` içine eklenir.
- QR/lonca mührü `assets/guild_seals/<username>_seal.png` olarak üretilir.

## QR + Yüz doğrulama testi

Adımlar:
1. `Q` menüsünden `3` ile doğrulama modunu `QR + Yüz` yap.
2. Kayıtlı kullanıcı yüzünü kameraya göster.
3. QR/lonca mührünü göstermeden durumu kontrol et.
4. Kullanıcıya ait QR/lonca mührünü kameraya göster.

Beklenen sonuç:
- QR yokken tam yetki açılmaz.
- Doğru QR okununca tam profil açılır.
- Yanlış QR gösterilirse tam yetki verilmez.

## Yalnızca Yüz doğrulama testi

Adımlar:
1. `Q` menüsünden `3` ile doğrulama modunu `Yalnızca Yüz` yap.
2. Kayıtlı kullanıcı yüzünü kameraya göster.

Beklenen sonuç:
- Kayıtlı yüz tanınınca QR gerekmeden tam profil açılır.
- Profilin açık büyüleri kullanılabilir hale gelir.

## Misafir yetki testi

Adımlar:
1. Tanınmayan bir yüz ile kameraya bak.
2. Büyü Kitabı ve Debug panelindeki aktif yetkiyi kontrol et.
3. Donma, Ateş ve Kalkan hareketlerini dene.

Beklenen sonuç:
- Profil Misafir olarak kalır.
- Yalnızca Donma açık olur.
- Ateş ve Kalkan kilitli kalır.

## Donma/Ateş/Kalkan testi

Adımlar:
1. Donma için avucu açık ve kısa süre sabit tut.
2. Ateş için elini kadraj içinde kontrollü şekilde yatay süpür ve ardından açık avuç göster.
3. Kalkan için iki açık el göster.
4. Debug panelinde `D` ile El / Tracker ve Büyü / Trial sayfalarını kontrol et.

Beklenen sonuç:
- Yetki varsa ilgili büyü tetiklenir.
- Cooldown büyü spamlenmesini engeller.
- Yetki yoksa kilitli büyü efekti başlamaz.
- Ateş için çok hızlı savurma gerekmez; küçük titreşimler tetikleme sayılmaz.
- Loş ışıkta veya bulanık görüntüde debug panelinde el takip kalite uyarısı görünebilir.
- Kalkan için iki el görünürken `raw_hand_count` 2 olmalı ve `shield_two_hand_score` yükselmelidir.
- Tek el görünürken Kalkan tetiklenmemelidir.

## Büyü Kitabı testi

Adımlar:
1. `B` ile Büyü Kitabı panelini aç/kapat.
2. Sağ ve sol ok tuşlarıyla sayfa değiştir.
3. Misafir ve doğrulanmış kullanıcı durumlarını ayrı ayrı kontrol et.

Beklenen sonuç:
- Kitap kapak sayfasıyla açılır.
- Her sayfada bir büyü bilgisi görünür.
- Açık/kilitli büyüler aktif yetkiye göre değişir.

## Trial Mode testi

Adımlar:
1. Uygulama açılır açılmaz Trial panelinin görünmediğini kontrol et.
2. `T` ile Mühürlü Kapı Trial görevini başlat.
3. Sırayla Donma, Ateş ve Kalkan büyülerini yap.
4. Yanlış büyüyü deneyerek görevin sıfırlanmadığını kontrol et.

Beklenen sonuç:
- Trial paneli sadece aktifken veya tamamlandıktan sonraki kısa sonuç süresinde görünür.
- Doğru sırada mühür ilerlemesi artar.
- Yanlış büyü görevi sıfırlamaz.
- Tamamlanınca `Kapı Açıldı` / `Trial tamamlandı` görünür ve panel kısa süre sonra kaybolur.

## Ayarlar ve Sistem Durumu testi

Adımlar:
1. `Q` ile ayar menüsünü aç.
2. `1-9` seçeneklerini sırayla değiştir.
3. Uygulamayı kapatıp yeniden aç.
4. `8` ile Sistem Durumu panelini aç.
5. `9` ile Algılama Profilini `Hassas`, `Dengeli`, `Kararlı` arasında değiştir.
6. Debug Sayfasını açıp `D` ile Genel, Yüz / Doğrulama, El / Tracker ve Büyü / Trial sayfalarını gez.

Beklenen sonuç:
- Kalıcı ayarlar `data/settings.json` içine yazılır.
- Uygulama yeniden açıldığında son ayarlar korunur.
- Sistem Durumu paneli model, profil ve QR dosya durumlarını anlaşılır şekilde gösterir.
- Debug paneli tek uzun liste yerine sayfalara bölünür.
- El / Tracker sayfasında raw el sayısı, takip kaynağı, kalite uyarıları, brightness ve blur bilgisi görünür.
- `0` doğrulama oturumunu sıfırlar.
