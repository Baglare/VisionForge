# VisionForge 60–90 Saniyelik Demo Senaryosu

Bu akış güncel PySide6 masaüstü arayüzünü kısa ve tekrarlanabilir biçimde gösterir. Hazırlıkta kamera, modeller, profil ve lonca mührü önceden doğrulanmalıdır.

## 1. Açılış — 5 sn

`python app.py` veya mevcut onedir build içindeki `VisionForge.exe` ile uygulamayı açın.

Anlatım: “VisionForge, yüz ve el algılamayı yerel doğrulama ve hareket komutlarıyla birleştiren PySide6 masaüstü prototipidir.”

## 2. Canlı Görüş — 7 sn

Canlı Görüş'te 640×480 kamera görüntüsünü, üst profil alanını ve sağdaki oturum/büyü/Trial kartlarını gösterin. Görüntünün pencereye oranı korunarak yerleştiğini belirtin.

## 3. Sistem Durumu — 6 sn

Sistem Durumu sayfasına geçip **Yenile** düğmesine basın. Kamera, MediaPipe modelleri ve yerel tanıma kaynaklarını kısaca gösterin.

## 4. Kayıt veya Hazır Profil — 7 sn

Hazır profil kullanılıyorsa Kayıt sayfasındaki native akışı kısaca gösterip kayıt başlatmayın. Yeni kayıt gösterilecekse kullanıcı adı, yöntem, aşama ve kalite/progress alanlarını özetleyin.

Anlatım: “Yüz örnekleri, LBPH modeli ve lonca mührü cihazda tutulur.”

## 5. Yüz + QR — 8 sn

Ayarlar'da `QR + Yüz` modunu gösterin. Kayıtlı yüzü tanıtın, ardından aynı profile ait lonca mührünü kameraya gösterin. Üst doğrulama rozeti ve açılan yetkileri vurgulayın.

Not: Bunun profesyonel güvenlik veya production biyometrik sistem olmadığını açıkça belirtin.

## 6. Grace Period — 6 sn

Tam doğrulamadan sonra kısa süre kadrajdan çıkın. Amber kalan süre göstergesini gösterip 10 saniye dolmadan geri dönün.

Anlatım: “Aynı kullanıcı kısa kamera kaybında oturumu yeniden QR göstermeden sürdürebilir.”

## 7. Büyü Kitabı — 7 sn

Büyü Kitabı sayfasına geçin. **Önceki/Sonraki** ile açık ve kilitli büyüleri, tetikleme bilgisini ve gereken rütbeyi gösterin.

## 8. Üç Büyü — 12–18 sn

Canlı Görüş'e dönüp sırasıyla:

1. Donma: açık avucu sabit tutun.
2. Ateş: kontrollü yatay süpürüp açık avuç gösterin.
3. Kalkan: iki açık eli gösterin.

Hazırlık, cooldown, bildirim ve kamera efektlerini kısa tutun.

## 9. Trial — 8–12 sn

Trial sayfasında görevi başlatın. Donma → Ateş → Kalkan sırasındaki adım kartlarının tamamlanmasını ve sonuç durumunu gösterin.

## 10. Debug / Performans — 6 sn

Debug → Genel sekmesinde FPS, 640×480 çözünürlük, pipeline ve UI frame aralığını gösterin. Gerekirse El/Tracker veya Yüz/Doğrulama sekmesine tek geçiş yapın.

## 11. Kapanış — 4 sn

Canlı Görüş'e dönün ve `Esc` ile uygulamayı kapatın.

Kapanış cümlesi: “Kamera işleme ayrı worker thread'inde, kullanıcı verileri ise source veya portable EXE kökünde yerel olarak tutulur.”
