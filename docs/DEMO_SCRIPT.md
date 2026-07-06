# VisionForge Demo Video Senaryosu

Bu senaryo portfolyo videosu veya canlı sunum için kısa ve kontrollü bir akış önerir. Amaç bütün sistemi tek seferde anlatmak değil, VisionForge'un ana değerini net göstermektir.

## 1. Açılış

Adım:
1. Proje klasörünü ve uygulama penceresini göster.
2. `python app.py` ile uygulamayı başlat.
3. Kamera görüntüsünün geldiğini göster.

Anlatım:
- VisionForge, kamera üzerinden yüz ve el algılayan, kullanıcıyı yerel doğrulama ile tanıyan ve el hareketlerini büyü komutlarına çeviren masaüstü görüntü işleme prototipidir.

Beklenen ekran:
- Kamera görüntüsü.
- Kafa üstünde kullanıcı adı, rütbe ve lonca bilgisi.
- Küçük büyü durumu paneli.

## 2. Sistem Durumu ve Ayarlar

Adım:
1. `Q` ile ayar menüsünü aç.
2. `8` ile Sistem Durumu panelini göster.
3. Model ve yerel veri durumlarını kısa göster.

Anlatım:
- Uygulama eksik model veya yerel profil dosyalarında çökmeden durum gösterir.
- Debug ve sistem durumu panelleri demo sırasında sorun ayıklamak için kullanılır.

Beklenen ekran:
- Face Detector, Hand Landmarker, yüz tanıma modeli, yüz etiketleri ve QR/lonca mührü durumları.

## 3. Kullanıcı Kaydı veya Hazır Kayıt

Adım:
1. Hazır kayıt varsa bunu belirt.
2. Kayıt akışını göstermek istersen `E` ile başlat.
3. Rehberli kayıt adımlarını kısaca göster: düz bak, sağa dön, sola dön, yaklaş, uzaklaş.

Anlatım:
- Kayıt sırasında yüz örnekleri yerel olarak saklanır.
- Kötü, bulanık veya çok küçük yüz örnekleri eğitim verisine alınmaz.
- Eğitimden sonra yerel LBPH modeli ve kullanıcıya özel QR/lonca mührü oluşur.

Beklenen ekran:
- Kayıt aşaması, örnek sayısı, kalite durumu ve yönlendirme mesajları.

## 4. Yüz Tanıma

Adım:
1. Kameraya kayıtlı kullanıcı olarak bak.
2. Kafa üstü profil etiketini göster.
3. Debug panel açıksa Yüz / Doğrulama sayfasında stabil yüz tanıma bilgisini göster.

Anlatım:
- Yüz tanıma tek karelik karar yerine birkaç karelik kararlılık ile değerlendirilir.
- Profil ve model dosyaları tutarsızsa uygulama kullanıcıyı çökmeden bilgilendirir.

Beklenen ekran:
- Kayıtlı kullanıcı adı, rütbe ve lonca adı.
- Misafir modunda `Misafir`, `Misafir Büyücü`, `Loncasız`.

## 5. QR + Yüz veya Yalnızca Yüz Doğrulama

Adım:
1. Varsayılan `QR + Yüz` modunu anlat.
2. QR/lonca mührünü telefonda veya görsel olarak kameraya göster.
3. İstersen `Q > 3` ile `Yalnızca Yüz` moduna geçildiğini göster.

Anlatım:
- QR + Yüz modunda tam yetki için hem stabil yüz tanıma hem doğru lonca mührü gerekir.
- Yalnızca Yüz modunda kayıtlı yüz tanınırsa QR gerekmeden profil açılır.
- Bu prototip profesyonel güvenlik sistemi değildir.

Beklenen ekran:
- QR onay bildirimi.
- Aktif profilin açık büyüleri.

## 6. Büyü Kitabı

Adım:
1. `B` ile Büyü Kitabı'nı aç.
2. Kapak sayfasını göster.
3. Sağ/sol oklarla sayfalar arasında gez.

Anlatım:
- Büyü Kitabı aktif profile göre açık ve kilitli büyüleri gösterir.
- Gereken rütbe bilgisi şu an bilgilendiricidir; gerçek seviye sistemi eklenmemiştir.

Beklenen ekran:
- Her sayfada bir büyü.
- Tür, tetikleme, etki, durum ve gereken rütbe alanları.

## 7. Donma Büyüsü

Adım:
1. Avucunu kameraya açık göster.
2. Kısa süre sabit tut.

Anlatım:
- Donma, açık avuç ve kısa süreli sabit duruş ile tetiklenir.
- Hazırlık progress bar ile görünür.

Beklenen ekran:
- Donma hazırlık barı.
- `Donma büyüsü` bildirimi.
- Kısa soğuk efekt.

## 8. Ateş Büyüsü

Adım:
1. Elini kadraj içinde kontrollü yatay süpür.
2. Ardından açık avuç göster.

Anlatım:
- Ateş artık hızlı savurma yerine kontrollü yatay süpürmeye daha uygun çalışır.
- Kısa el kayıpları hareket devamlılığı için tolere edilir, fakat final tetikleme için gerçek açık avuç gerekir.

Beklenen ekran:
- Ateş hazırlık durumu.
- `Ateş büyüsü` bildirimi.
- Kısa sıcak efekt.

## 9. Kalkan Büyüsü

Adım:
1. İki açık elini kameraya göster.
2. Kısa süre pozunu koru.

Anlatım:
- Kalkan için iki gerçek el landmarkı gerekir.
- Optical flow tek başına Kalkan tetiklemez.

Beklenen ekran:
- Kalkan hazırlık durumu.
- `Kalkan büyüsü` bildirimi.
- Koruma halkası efekti.

## 10. Trial Mode

Adım:
1. `T` ile Mühürlü Kapı görevini başlat.
2. Sırayla Donma, Ateş ve Kalkan yap.

Anlatım:
- Trial Mode mevcut büyüleri küçük bir görev akışına bağlar.
- Yanlış büyü görevi sıfırlamaz; sadece uyarı verir.
- Tam görev için kullanıcının ilgili büyülere yetkisi olmalıdır.

Beklenen ekran:
- Trial paneli sadece görev aktifken görünür.
- Mühür ilerlemesi 0/3, 1/3, 2/3, 3/3 olarak artar.
- Tamamlanınca `Kapı Açıldı` mesajı görünür.

## 11. Demo Rehberi

Adım:
1. `G` ile Demo Rehberi'ni aç.
2. `N` ve `P` ile adımlar arasında geç.
3. Rehber panelindeki kısayol satırını göster.

Anlatım:
- Demo Rehberi portfolyo sunumu sırasında sıradaki adımı hatırlatır.
- Otomatik geçişler kullanıcının okuyabileceği kadar kısa süre bekler.

Beklenen ekran:
- Demo Rehberi paneli.
- Adım başlığı, kısa açıklama ve kısayol ipuçları.

## 12. Kapanış

Adım:
1. Genel akışı özetle.
2. `Esc` ile uygulamayı kapat.

Anlatım:
- VisionForge bir kamera + yerel doğrulama + hareket tabanlı komut prototipidir.
- Proje, görüntü işleme, uygulama mimarisi, kullanıcı geri bildirimi ve demo tasarımı konularını bir araya getirir.

Beklenen ekran:
- Kamera penceresi temiz kapanır.
