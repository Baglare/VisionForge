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
- Kafa üstünde kutusuz biçimde kullanıcı adı, rütbe ve lonca adı görünür.
- Kafa üstünde doğrulama durumu yazısı görünmez.
- Misafir profili için lonca satırı `Loncasız` olur.
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
- Sol üst büyü panelinde hazırlık durumu metinle birlikte küçük progress bar olarak görünür.
- Hazırlık yokken progress bar çizilmez ve `Hazırlık: Yok` satırı panel dışına taşmaz.
- Hazırlık varken progress bar panel sınırları içinde kalır.
- Donma hazırlığında bar soğuk tonlu, Ateş hazırlığında sıcak tonlu, Kalkan hazırlığında mavi/altın tonlu görünür.
- Donma açık avuç sabit tutulduğunda %98-99 civarında takılı kalmadan tetiklenir.
- Debug > Büyü / Trial sayfasında `freeze_state`, `freeze_elapsed`, `freeze_progress`, `freeze_velocity`, `freeze_deadzone`, `freeze_is_stable` ve `freeze_block` alanları Donma kararını açıklar.
- Ateş için çok hızlı savurma gerekmez; küçük titreşimler tetikleme sayılmaz.
- Minimal el titreşimi `fire_candidate_active` değerini gereksiz yere True yapmamalıdır.
- Ateş sırasında el çok kısa kaybolursa hazırlık hemen sıfırlanmaz; final tetikleme için yine gerçek açık avuç görülmelidir.
- Büyü / Trial debug sayfasında `spell_uses_tracker`, `tracker_source_used`, `fire_travel_distance`, `fire_required_distance` ve `fire_seal_window_active` alanları görünür.
- `tracker_source_used` kısa süre `optical_flow` olsa bile Donma veya Kalkan tek başına tetiklenmemelidir.
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
- Kitap paneli kamera görüntüsünü tamamen kapatmayacak kadar saydam kalır.

## Trial Mode testi

Adımlar:
1. Uygulama açılır açılmaz Trial panelinin görünmediğini kontrol et.
2. `T` ile Mühürlü Kapı Trial görevini başlat.
3. Sırayla Donma, Ateş ve Kalkan büyülerini yap.
4. Yanlış büyüyü deneyerek görevin sıfırlanmadığını kontrol et.

Beklenen sonuç:
- Trial paneli sadece aktifken veya tamamlandıktan sonraki kısa sonuç süresinde görünür.
- Doğru sırada mühür ilerlemesi artar.
- Donma, Ateş ve Kalkan mühürleri ayrı göstergeler olarak görünür.
- Açılmamış mühürler soluk, açılmış mühürler parlak, sıradaki mühür hafif vurgulu görünür.
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

## Büyü Kitabı İçerik Testi

1. Uygulamayı başlat.
2. `B` ile Büyü Kitabı'nı aç.
3. Kapakta `Büyü Kitabı`, `VisionForge Lonca Arşivi` ve `Sağ ok ile aç` yazılarını kontrol et.
4. Sağ ok ile kitap sayfalarına geç.
5. Her sayfada yalnızca bir büyünün detaylarının göründüğünü doğrula.
6. Donma sayfasında tür, tetikleme, etki, durum ve gereken rütbe alanlarını kontrol et.
7. Misafir modunda Donma'nın `Açık`, Ateş ve Kalkan dahil diğer büyülerin `Kilitli` göründüğünü doğrula.
8. Baglare / S-Seviye doğrulamasında Donma, Ateş ve Kalkan'ın `Açık` göründüğünü kontrol et.
9. Kilitli büyülerde gereken rütbe bilgisinin yalnızca bilgilendirme olduğunu, yeni rütbe/XP sistemi açmadığını doğrula.
10. Sol ve sağ oklarla sayfa geçişinin bozulmadığını kontrol et.

## Türkçe Karakter UI Testi

1. Uygulamayı başlat.
2. Büyü Kitabı kapağında `Büyü Kitabı`, `VisionForge Lonca Arşivi` ve `Sağ ok ile aç` metinlerini kontrol et.
3. Kitap sayfalarında `Şimşek`, `Alan Mührü` ve `Zaman Kırığı` metinlerinin bozulmadan göründüğünü doğrula.
4. Kafa üstü etikette `S-Seviye Büyücü` metninin düzgün göründüğünü kontrol et.
5. Q menüsü, Debug paneli, Sistem Durumu ve Trial panelindeki Türkçe karakterlerin `?` karakterlerine dönüşmediğini doğrula.

## Yüz Tanıma Sağlık ve Reload Testi

1. Uygulamayı başlat.
2. Q menüsünden `8` ile Sistem Durumu panelini aç.
3. `Yüz tanıma modeli`, `Yüz etiketleri`, `Yerel profiller` ve `Label/Profile eşleşmesi` satırlarını kontrol et.
4. Model veya label eksikse uygulamanın çökmeden Misafir/demo akışıyla devam ettiğini doğrula.
5. `E` ile yeni kayıt/eğitim tamamla.
6. Uygulamayı kapatmadan kameraya dön ve yeni kullanıcının tanınabildiğini kontrol et.
7. Debug panelini açıp `D` ile Yüz / Doğrulama sayfasına geç.
8. `face_identity_score`, `face_identity_threshold`, `face_identity_match`, `stable_label`, `stability_count` ve `identity_health` alanlarının göründüğünü doğrula.
9. Yüz kadrajdan çıkınca tanıma durumunun sıfırlandığını, tekrar girince birkaç kare sonra stabil hale geldiğini kontrol et.

## Bildirim / Toast Testi

1. Uygulamayı başlat ve bildirimlerin alt orta bölgede küçük kartlar olarak göründüğünü kontrol et.
2. Donma, Ateş veya Kalkan büyüsü tetikle; ilgili büyü bildiriminin geldiğini doğrula.
3. QR + Yüz modunda tanınan kullanıcı için QR göstermeden `Lonca mührü bekleniyor` bildiriminin yalnızca durum değişince geldiğini kontrol et.
4. Doğru QR gösterildiğinde `Lonca mührü onaylandı` bildiriminin geldiğini doğrula.
5. Yanlış QR gösterildiğinde `Mühür kullanıcıyla eşleşmedi` bildiriminin geldiğini doğrula.
6. T ile Trial başlat; `Mühürlü Kapı başladı` bildirimi görünmeli.
7. Trial tamamlanınca `Kapı açıldı` bildirimi görünmeli.
8. Bildirimlerin birkaç saniye sonra kaybolduğunu ve aynı durumun her karede spam yapmadığını kontrol et.

## Demo Rehberi Testi

1. Uygulamayı başlat.
2. `G` ile Demo Rehberi'ni aç; küçük rehber paneli görünmeli.
3. Panelin altındaki küçük kısayol alanında `Q: Menü`, `E: Kayıt`, `B: Kitap`, `T: Trial`, `Esc: Çıkış` bilgisini kontrol et.
4. İlk adımda `E ile büyücü kaydı başlat` bilgisinin göründüğünü doğrula.
5. `N` ile sonraki adıma geç, `P` ile önceki adıma dön.
6. Büyü Kitabı adımında `E: Kayıt`, `B: Kitap` ve `Sağ/Sol Ok: Sayfa değiştir` ipuçlarını kontrol et.
7. `B` ile Büyü Kitabı'nı açıp sağ okla sayfaya geç; rehberin Büyü Kitabı adımını hemen kaybetmeden kısa süre gösterdiğini kontrol et.
8. Donma, Ateş ve Kalkan büyülerini tetikle; ilgili demo adımlarının en az yaklaşık 1.5 saniye görünür kaldıktan sonra ilerlediğini kontrol et.
9. `T` ile Mühürlü Kapı görevini başlat; Trial adımı algılanmalı.
10. Trial tamamlanınca rehberin final/tamamlandı durumuna geçtiğini ve `Demo tamamlandı` bildiriminin geldiğini kontrol et.
11. `G` ile rehberi kapat.
12. Q, Esc, E, B, H, R, T, D ve sağ/sol ok kısayollarının bozulmadığını kontrol et.
