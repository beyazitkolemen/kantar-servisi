# Degisiklik Kaydi

## Yayinlanmamis

## 1.1.0 - 2026-06-13

- Sabit tekli/Kantar 1/Kantar 2 profilleri kaldirildi; yeni kurulum bos kantar listesiyle baslar hale getirildi.
- Yonetim panelinden ad verilerek sinirsiz sayida kantar ekleme, secme, yeniden adlandirma ve silme akisi eklendi.
- Her kantara kalici benzersiz kimlik verildi; agirlik API'sine kantar adi ve dinamik kantar listesi endpointi eklendi.
- Eski ozellestirilmis profil ayarlari ilk calistirmada dinamik kantarlara otomatik tasinir hale getirildi.
- Ayar alanlarina sunucu tarafli dogrulama ve anlasilir hata mesajlari eklendi.
- Servis host ve port ayarlari tum kantar profilleri icin ortak hale getirildi.
- HTTP paneli yalnizca yerel istemcilere acildi; CSRF, CSP ve diger guvenlik basliklari eklendi.
- LISDEP entegrasyonu icin `/api/v1/agirlik` JSON endpointi ve sinirli CORS destegi eklendi.
- Ayni COM portuna gelen eszamanli okumalar siraya alindi.
- Negatif agirlik degerleri desteklendi.
- Log yazma ve rotasyon islemleri eszamanli istekler icin guvenli hale getirildi.
- GitHub paket manifesti kontrolune onbellek ve elle yenileme eklendi.
- Serial ve log ekranlarindaki JavaScript kodlari harici statik dosyalara tasindi.
- Test kapsami ayar, guvenlik, API, onbellek ve eszamanlilik senaryolariyla genisletildi.
- Windows sistem tepsisine canli servis durumu ve ayri panel kisayollari eklendi.
- Asenkron servis yeniden baslatma ve beklenmedik kapanmada otomatik toparlanma eklendi.
- Surum, dosya yollari, COM portlari ve profil ayarlarini iceren tanilama raporu eklendi.
- NSIS kurulumu markali gorseller, App Paths kaydi ve profesyonel Baslat menusu kisayollariyla gelistirildi.
- Paketlenmis EXE ile sessiz kurulum/kaldirma akisini dogrulayan kapsamli Windows smoke testleri eklendi.
- GitHub Actions ve Releases bagimliligi kaldirildi; Windows kurulumu yerelde uretilip `downloads/` klasorunde dogrudan depoya eklenir hale getirildi.
- Apple Silicon, macOS ve Linux uzerinde gercek Windows x64 EXE uretebilen Docker, MinGW ve NSIS tabanli yerel build zinciri eklendi.

## 1.0.0

- Windows sistem tepsisi uygulamasi eklendi.
- Python ve `.bat` gerektirmeyen Windows paketi eklendi.
- Kullanici bazli Windows kurulum dosyasi eklendi.
- GitHub uzerindeki hazir kurulum dosyasi icin sabit indirme adresi eklendi.
- Ayar ve log dosyalari `%LOCALAPPDATA%` altina tasindi.
- Web arayuzu icin cevrimdisi CSS paketi eklendi.
