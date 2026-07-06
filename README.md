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

Panelde örnek `baglare` profili, rütbe, açık büyüler ve kamera modu durumu gösterilir. Güncel sürümde `Q` ayar menüsünü açar, çıkış yalnızca `Esc` ile yapılır.

## Üçüncü Aşama: Yüz Algılama

Bu aşamada uygulama MediaPipe Tasks Face Detector ile kamera görüntüsünde yüz olup olmadığını algılar. Eski `mp.solutions.face_detection` API'si kullanılmaz.

Yüz algılama model dosyası şu konuma elle yerleştirilmelidir:

```text
models/face_detector.tflite
```

Model dosyası yoksa uygulama çökmez; kamera modu çalışır, panelde yüz algılamanın pasif olduğu gösterilir ve terminalde kısa bir uyarı yazılır.

Model dosyası varsa yüz algılama sonucu birkaç karelik kararlılık filtresinden geçirilir. Böylece tek karelik yanlış pozitif sonuçlar profil durumunu aktif etmez ve ekranda rastgele yanıp sönen kutu çizilmez.

## Dördüncü Aşama: El Algılama

Bu aşamada uygulama MediaPipe Tasks Hand Landmarker ile kamera görüntüsünde el landmark noktalarını algılar. Eski `mp.solutions.hands` API'si kullanılmaz.

El algılama model dosyası şu konuma elle yerleştirilmelidir:

```text
models/hand_landmarker.task
```

Model dosyası yoksa uygulama çökmez; kamera modu, profil paneli ve yüz algılama çalışmaya devam eder, el algılama pasif kalır.

Model dosyası varsa kamera görüntüsünde el üzerinde 21 landmark noktası ve sade bağlantı çizgileri gösterilir. Panelde `El Durumu: El algılandı`, el yoksa `El Durumu: El bekleniyor` bilgisi görünür.

## Beşinci Aşama: Donma Büyüsü

Bu aşamada ilk basit büyü sistemi eklenmiştir. Kullanıcı açık avucunu kameraya gösterip yaklaşık `0.8` saniye sabit tuttuğunda `Donma` büyüsü tetiklenir.

Büyü aktifken panelde `Aktif Büyü: Donma` bilgisi görünür ve kamera görüntüsünün üzerinde kısa süreli mavi/soğuk tonlu Donma efekti gösterilir. Büyü tetiklendikten sonra yaklaşık `2` saniyelik bekleme süresi uygulanır.

Bu aşama yalnızca ilk MVP büyü davranışını içerir; hareket zinciri, farklı büyüler veya kişi tanıma eklenmemiştir.

## Altıncı Aşama: Ateş Büyüsü

Bu aşamada ilk hareket zinciri büyüsü eklenmiştir. Kullanıcı elini kadraj içinde kontrollü şekilde yatay süpürüp ardından açık avuç gösterdiğinde `Ateş` büyüsü tetiklenir.

Donma büyüsü açık ve sabit avuç ile çalışmaya devam eder. Ateş büyüsü ise hızlı savurma yerine yatay mesafe kat eden kontrollü süpürme ve ardından açık avuç mührü ister. Aktif büyü veya bekleme süresi varken yeni büyü başlatılmaz.

Ateş aktifken panelde `Aktif Büyü: Ateş` bilgisi görünür ve kamera görüntüsünde kısa süreli kırmızı/turuncu parlama efekti gösterilir.

## Yedinci Aşama: Kalkan Büyüsü

Bu aşamada iki el algılamaya dayalı `Kalkan` büyüsü eklenmiştir. Kullanıcı iki açık avucunu kameraya yaklaşık `0.8` saniye gösterdiğinde Kalkan tetiklenir.

Mevcut büyü tetiklemeleri:

- `Donma`: Açık avuç kısa süre sabit tutulur.
- `Ateş`: El kadraj içinde kontrollü yatay süpürülür, ardından açık avuç gösterilir.
- `Kalkan`: İki açık el kısa süre birlikte gösterilir.

Aktif büyü veya bekleme süresi varken yeni büyü başlatılmaz. Kalkan aktifken panelde `Aktif Büyü: Kalkan` görünür ve kamera görüntüsünde kısa süreli koruma halkası efekti gösterilir.

## Sekizinci Aşama: Büyü Defteri ve Arayüz

Bu aşamada kamera üzerindeki arayüz toparlanmıştır. Sol üstte kompakt lonca/profil kartı, altında aktif büyü ve cooldown alanı, sağ tarafta ise Büyü Defteri paneli gösterilir.

Büyü Defteri açık büyüleri ve kilitli büyüleri profil verisinden okur. Açık büyüler:

- `Donma`: Avucu açık tut
- `Ateş`: Yatay süpür + avuç göster
- `Kalkan`: İki açık el göster

Kilitli büyüler: `Şimşek`, `Alan Mührü`, `Zaman Kırığı`.

Klavye kısayolları:

- `B`: Büyü Defteri panelini açar/kapatır.
- `H`: El landmark/debug çizimini açar/kapatır.
- `Q`: Ayar menüsünü açar/kapatır.
- `Esc`: Uygulamayı kapatır.

## Dokuzuncu Aşama: Büyücü Kaydı ve Lonca Mührü

Bu aşamada uygulama içinden yerel kullanıcı kaydı, yüz örneği toplama, LBPH yüz tanıma eğitimi ve QR tabanlı lonca mührü doğrulaması eklenmiştir.

Bu sistem profesyonel güvenlik sistemi değildir. Portfolyo amaçlı, yerelde çalışan, kamera tabanlı bir doğrulama prototipidir.

Normal kullanıcı akışı:

1. `python app.py` ile uygulamayı aç.
2. `E` ile yeni büyücü kaydını başlat.
3. Kullanıcı adını gir.
4. Kayıt kaynağı olarak canlı kamera kaydını veya görsel import seçeneğini seç.
5. Canlı kamera seçildiyse kameraya bakarak yüz örneklerinin alınmasını bekle.
6. Görsel import seçildiyse fotoğrafları seçilen klasörden işlettir; fallback klasör `data/import_faces/<username>/` konumudur.
7. Oluşturulan QR/lonca mührünü sakla.
8. Sonraki girişte yüz + kendi lonca mührün ile tam doğrulan.

Canlı kamera kaydı rehberli aşamalarla ilerler:

- Düz bak
- Hafif sağa dön
- Hafif sola dön
- Biraz yaklaş
- Biraz uzaklaş

Her aşamada yeterli sayıda kaliteli yüz örneği alınmadan sonraki aşamaya geçilmez. Kayıt sırasında yüz çok küçükse, yüz kadraj kenarına yakınsa, algılama skoru düşükse veya görüntü bulanıksa örnek kaydedilmez.

Kaliteli kayıt için:

- İyi ışık kullan.
- Yüzünü kameraya yakın ama kadrajı taşırmadan tut.
- Yüzünü mümkün olduğunca merkezde tut.
- Her aşamada kısa süre sabit bekle.
- Ani hareket ve bulanık görüntüden kaçın.

Fotoğraf import kullanacaksan görselleri şu klasöre koyabilir veya dosya seçiciyle klasör seçebilirsin:

```text
data/import_faces/<username>/
```

Import için iyi fotoğraf önerileri:

- Yüz net olmalı.
- Işık yeterli olmalı.
- Farklı açılardan birkaç fotoğraf kullanılmalı.
- Çok kalabalık fotoğraflar tercih edilmemeli.
- Yüz fotoğrafta çok küçük olmamalı.

Import sırasında kötü fotoğraflar eğitim verisine alınmaz; kabul/red sayısı ve red sebepleri kısa rapor olarak gösterilir. Canlı kayıt, fotoğraf import ve yüz tanıma tahmini aynı yüz ön işleme mantığını kullanır.

Doğrulama davranışı:

- Yüz yoksa profil beklemede kalır.
- Tanınmayan yüz `Misafir Büyücü` olur ve yalnızca `Donma` kullanabilir.
- Yüz tanınır ama lonca mührü okunmazsa tam yetki verilmez.
- Yüz ve doğru lonca mührü birlikte doğrulanırsa kullanıcının tam profili açılır.
- Başka kullanıcıya ait mühür gösterilirse tam yetki verilmez.

Klavye kısayolları:

- `E`: Yeni büyücü kaydı / yüz eğitimi başlatır.
- `R`: Doğrulama oturumunu sıfırlar.
- `T`: Mühürlü Kapı Trial görevini başlatır veya baştan başlatır.
- `Q`: Ayar menüsünü açar/kapatır.
- `B`: Büyü Kitabı panelini açar/kapatır.
- `H`: El landmark/debug çizimini açar/kapatır.
- `Esc`: Uygulamayı kapatır.

Yerel yüz verileri ve kullanıcı QR dosyaları şu konumlarda saklanır:

```text
data/face_gallery/
data/import_faces/
models/face_recognizer_lbph.yml
data/face_labels.json
data/local_profiles.json
assets/guild_seals/
```

Bu verileri silerek yerel yüz eğitimini ve kullanıcı kayıtlarını temizleyebilirsin. `data/import_faces/` klasörü görsel import için kişisel fotoğraf kaynağı olarak kullanılabilir. Otomatik üretilen kullanıcı QR dosyaları, import fotoğrafları ve yüz eğitim verileri Git dışında tutulur.

## Arayüz ve Kontrol Sistemi

Genel ayar menüsü `Q` tuşu ile açılıp kapanır. Çıkış artık yalnızca `Esc` ile yapılır.

Ayar menüsündeki seçenekler:

- `1`: El landmark/debug çizimini açar/kapatır.
- `2`: Yüz kutusu/debug çizimini açar/kapatır.
- `3`: Doğrulama modunu `QR + Yüz` ve `Yalnızca Yüz` arasında değiştirir.
- `4`: Büyü Kitabı panelini açar/kapatır.
- `5`: Debug Sayfası'nı açar/kapatır.
- `6`: Büyü efektlerini açar/kapatır.
- `7`: Kamera aynalamayı açar/kapatır.
- `8`: Sistem Durumu panelini açar/kapatır.
- `0`: Doğrulama oturumunu sıfırlar.

Varsayılan doğrulama modu `QR + Yüz` şeklindedir. Bu modda tam yetki için hem kayıtlı yüzün tanınması hem de doğru lonca mührünün kamerada okunması gerekir. Menüden `3` ile `Yalnızca Yüz` moduna geçildiğinde kayıtlı yüz tanınırsa QR göstermeden tam profil açılır.

Kayıt tamamlandığında QR/lonca mührü şu konuma üretilir:

```text
assets/guild_seals/<username>_seal.png
```

Kullanıcı bu QR dosyasını telefonda açıp kameraya gösterebilir. Varsayılan doğrulama modu `QR + Yüz` olduğu için tam yetki almak isteyen kullanıcı kayıtlı yüzüyle birlikte kendi QR/lonca mührünü kameraya göstermelidir. Menüden `3` ile `Yalnızca Yüz` moduna geçilirse QR gerekmeden kayıtlı yüzle tam profil açılabilir. Otomatik üretilen QR dosyaları Git'e eklenmez.

Büyü Kitabı paneli kapak ve iki sayfalı kitap görünümüyle çalışır. Sağ/sol ok tuşları sayfa çiftlerini değiştirir. Her sayfada bir büyü anlatılır; açık büyülerde tür, tetikleme ve etki bilgisi, kilitli büyülerde kilit durumu gösterilir.

Kamera aynalama ayarı yalnızca ekranda gösterilen görüntüye uygulanır. Yüz algılama, yüz tanıma, QR okuma ve el algılama ham kamera karesiyle çalışır; çizimler ekrandaki aynalama durumuna göre dönüştürülür.

Yüz tanıma modeli, eğitim sırasında yüz örneklerinin aynalanmış kopyalarını da kullanır. Doğrulama sırasında normal ve aynalı yüz kırpımı ayrı ayrı denenir; daha iyi LBPH skoru veren tahmin kullanılır.

## Kalıcı Ayarlar ve Sistem Durumu

Uygulama arayüz ayarlarını yerel olarak şu dosyada saklar:

```text
data/settings.json
```

Dosya yoksa uygulama varsayılan ayarlarla oluşturur. Q menüsünden el/yüz debug çizimi, doğrulama modu, Büyü Kitabı, Debug Sayfası, büyü efektleri ve kamera aynalama ayarları değiştirildiğinde bu dosya güncellenir. Uygulama tekrar açıldığında son ayarlar korunur.

Algılama profili `9` tuşuyla `Hassas`, `Dengeli` ve `Kararlı` arasında değiştirilir. Varsayılan profil `Dengeli` değeridir. `Hassas` daha kolay algılama, `Kararlı` daha seçici algılama hedefler.

Ateş büyüsü hızlı bir savurma gerektirmez; elin kadraj içinde soldan sağa veya sağdan sola kontrollü yatay süpürülmesi yeterlidir. Loş ışık veya bulanık görüntü el takibini zayıflatabilir; daha iyi ışık ve daha kontrollü el hareketi önerilir. Debug paneli açıkken Ateş hazırlık durumu ve el takip kalite uyarıları görülebilir.

Sistem Durumu paneli Q menüsünde `8` ile açılıp kapatılır. Panel şu kaynakları kontrol eder:

- `models/face_detector.tflite`
- `models/hand_landmarker.task`
- `models/face_recognizer_lbph.yml`
- `data/face_labels.json`
- `data/local_profiles.json`
- `assets/guild_seals/`

Yüz tanıma modeli, yüz etiketleri, yerel profiller veya QR/lonca mühürleri eksikse bu normal olabilir; `E` ile kayıt oluşturulduktan sonra yerel dosyalar üretilir. Kayıtlı büyücü yoksa ekranda `Kayıtlı büyücü yok. E ile kayıt başlat.` yönlendirmesi görünür.

`data/settings.json` yerel kullanıcı ayarıdır ve Git'e eklenmez. Kayıtlı kullanıcı verileri, yüz örnekleri ve QR/lonca mührü dosyaları da yerel tutulur.

## Trial Mode: Mühürlü Kapı

Bu aşamada mevcut büyü sistemi üzerine küçük bir görev modu eklenmiştir. `T` tuşu ile `Mühürlü Kapı` görevi başlatılır veya baştan başlatılır.

Görev sırası:

1. `Donma`
2. `Ateş`
3. `Kalkan`

Doğru sıradaki büyü yapıldığında mühür ilerlemesi artar. Yanlış büyü yapılırsa görev sıfırlanmaz; ekranda `Yanlış büyü` mesajı gösterilir. Üç büyü doğru sırayla tamamlanırsa `Kapı Açıldı` ve `Trial tamamlandı` durumu görünür.

Trial Mode mevcut yetki sistemine uyar. Misafir kullanıcı yalnızca `Donma` kullanabildiği için ilk adımı geçebilir, ancak `Ateş` aşamasında daha yüksek yetki gerektiği gösterilir. Tam görev için `Donma`, `Ateş` ve `Kalkan` büyülerine erişimi olan doğrulanmış kullanıcı gerekir.

## Demo Hazırlığı

Güncel kısayollar:

- `Q`: Ayar menüsünü açar/kapatır.
- `Esc`: Uygulamayı kapatır.
- `E`: Kayıt/eğitim akışını başlatır.
- `B`: Büyü Kitabı'nı açar/kapatır.
- `H`: El debug çizimini açar/kapatır.
- `R`: Doğrulama oturumunu sıfırlar.
- `T`: Mühürlü Kapı Trial görevini başlatır veya yeniden başlatır.
- `1-9` ve `0`: Q menüsü açıkken ayarları değiştirir.
- `Sağ/Sol ok`: Büyü Kitabı sayfalarını değiştirir.

Model ve yerel kullanıcı dosyaları Git'e dahil edilmez. MediaPipe modelleri `models/face_detector.tflite` ve `models/hand_landmarker.task` konumuna elle yerleştirilmelidir. Kayıt/eğitim sonrası oluşan yüz galerisi, LBPH modeli, yerel profil, ayarlar ve QR/lonca mühürleri yerel dosyalardır.

Kısa demo senaryosu:

1. `python app.py` ile uygulamayı aç.
2. Gerekirse `E` ile kayıt oluştur.
3. `Q` menüsünden `QR + Yüz` veya `Yalnızca Yüz` doğrulama modunu seç.
4. Büyü Kitabı'nı göster.
5. Donma, Ateş ve Kalkan büyülerini tetikle.
6. `T` ile Mühürlü Kapı Trial görevini başlat.
7. Donma -> Ateş -> Kalkan sırasıyla kapıyı aç.

Manuel demo kontrol listesi için `docs/MANUAL_TESTS.md` dosyasını kullan.

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
