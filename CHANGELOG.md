# Degisiklik Kaydi

## Yayinlanmamis

- Ayar alanlarina sunucu tarafli dogrulama ve anlasilir hata mesajlari eklendi.
- Servis host ve port ayarlari tum kantar profilleri icin ortak hale getirildi.
- HTTP paneli yalnizca yerel istemcilere acildi; CSRF, CSP ve diger guvenlik basliklari eklendi.
- LISDEP entegrasyonu icin `/api/v1/agirlik` JSON endpointi ve sinirli CORS destegi eklendi.
- Ayni COM portuna gelen eszamanli okumalar siraya alindi.
- Negatif agirlik degerleri desteklendi.
- Log yazma ve rotasyon islemleri eszamanli istekler icin guvenli hale getirildi.
- GitHub surum kontrolune onbellek ve elle yenileme eklendi.
- Serial ve log ekranlarindaki JavaScript kodlari harici statik dosyalara tasindi.
- Test kapsami ayar, guvenlik, API, onbellek ve eszamanlilik senaryolariyla genisletildi.

## 1.0.0

- Windows sistem tepsisi uygulamasi eklendi.
- Python ve `.bat` gerektirmeyen PyInstaller paketi eklendi.
- Kullanici bazli Inno Setup kurulum dosyasi eklendi.
- GitHub Actions ile otomatik Windows Release akisi eklendi.
- GitHub surum kontrolu ve sabit son kurulum indirme adresi eklendi.
- Ayar ve log dosyalari `%LOCALAPPDATA%` altina tasindi.
- Web arayuzu icin cevrimdisi CSS paketi eklendi.
