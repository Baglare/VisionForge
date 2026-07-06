# VisionForge Portfolyo Notları

Bu belge VisionForge'u CV, GitHub, LinkedIn veya demo videosunda nasıl konumlandırabileceğini özetler.

## CV'de Nasıl Anlatılır?

Kısa madde:
- Python ve OpenCV tabanlı, kamera üzerinden yüz/el algılama, yerel yüz tanıma, QR destekli doğrulama ve el hareketlerinden komut üretimi yapan interaktif görüntü işleme prototipi geliştirdim.

Daha teknik madde:
- MediaPipe Tasks, OpenCV, LBPH yüz tanıma, QRCodeDetector, gerçek zamanlı UI overlay, el hareketi state machine'i ve yerel profil yönetimi kullanarak lonca temalı masaüstü demo uygulaması geliştirdim.

## LinkedIn / GitHub Açıklaması

Önerilen kısa açıklama:

VisionForge, kamera görüntüsünden yüz ve el algılayan; kullanıcıyı yerel yüz tanıma ve lonca mührü QR doğrulamasıyla ayıran; Donma, Ateş ve Kalkan gibi el hareketlerini interaktif büyü komutlarına dönüştüren Python tabanlı bir görüntü işleme prototipidir.

## Teknik Kazanımlar

Öne çıkarılabilecek başlıklar:
- Gerçek zamanlı kamera akışı yönetimi
- MediaPipe Tasks ile yüz ve el algılama
- OpenCV LBPH ile yerel yüz tanıma
- QR tabanlı ikinci doğrulama katmanı
- El hareketlerinden state machine tabanlı komut üretimi
- Kısa süreli el kaybını tolere eden HandStateTracker yaklaşımı
- Kullanıcı dostu kayıt/eğitim akışı
- Debug, sistem durumu ve manuel test dokümantasyonu

## Görüntü İşleme Tarafında Ne Öğrenildi?

VisionForge, görüntü işleme sistemlerinde yalnızca algılayıcıyı çalıştırmanın yeterli olmadığını gösterir. Kamera aynalama, düşük ışık, hareket bulanıklığı, el kadrajdan çıkması, yanlış pozitif algılar ve yüz tanıma skor kararlılığı gibi pratik problemler ayrıca ele alınmıştır.

Öne çıkan deneyimler:
- Ham kamera karesi ile ekrana çizilen kareyi ayrı tutma
- Yüz kırpımında tutarlı ön işleme kullanma
- Tek karelik kararlar yerine kısa pencere ve stabilite kullanma
- Debug skorlarını kullanıcı arayüzünden ayrı tutma

## Yazılım Mimarisi Tarafında Ne Öğrenildi?

Proje küçük başlamasına rağmen modüllere ayrılmıştır:
- Kamera yönetimi
- Dedektörler
- Profil ve yetki yönetimi
- SpellEngine
- TrialEngine
- DemoGuide
- UI/effects katmanı
- Ayar ve sistem durumu yönetimi

Bu yapı sayesinde yeni ekranlar ve dokümantasyon eklenirken büyü, doğrulama ve kayıt mantığı birbirinden ayrılabilmiştir.

## Yapay Zeka / Codex ile Geliştirme Süreci Nasıl Anlatılmalı?

Doğru anlatım:
- Proje iteratif olarak geliştirildi.
- Her aşamada küçük hedefler belirlendi.
- Codex kod iskeleti, refactor ve dokümantasyon süreçlerinde yardımcı oldu.
- Kararlar ve kapsam geliştirici tarafından yönlendirildi.
- Test, hata ayıklama ve davranış doğrulama gerçek çalışma çıktılarıyla yapıldı.

Kaçınılması gereken anlatım:
- Sistemi yapay zeka kendi başına tasarladı gibi göstermek.
- Profesyonel güvenlik ürünü iddiası vermek.
- Kamera ve yüz tanıma doğruluğunu abartmak.

## Neden Sıradan Webcam Demosundan Daha Güçlü?

VisionForge yalnızca kameradan görüntü göstermez. Birden fazla katmanı birleştirir:
- Yüz var/yok algılama
- Kayıtlı kullanıcı tanıma
- QR/lonca mührüyle ikinci doğrulama
- Aktif profile göre büyü yetkisi
- El hareketlerinden Donma, Ateş ve Kalkan komutları
- Mühürlü Kapı Trial Mode
- Demo Rehberi, sistem durumu, debug paneli ve toast bildirimleri

Bu nedenle proje hem görüntü işleme hem de kullanıcı deneyimi tarafında daha kapsamlı bir portfolyo örneğidir.

## Kısa Demo Mesajı

Demo sırasında kullanılabilecek kapanış cümlesi:

VisionForge, gerçek zamanlı görüntü işleme tekniklerini oyunlaştırılmış bir masaüstü deneyimine dönüştüren yerel çalışan bir prototip. Projede güvenlik ürünü iddiası yok; amaç yüz/el algılama, yerel doğrulama, hareket yorumlama ve kullanıcı arayüzü akışlarını tek bir portfolyo demosunda birleştirmek.
