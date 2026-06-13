# Kantar Servisi

Kantar Servisi, Windows bilgisayardaki seri porttan kantar verisini okuyup yerel HTTP adresi uzerinden sunan masaustu uygulamasidir. Python kurulumu veya `.bat` dosyasi gerektirmez.

## Windows Kurulumu

Desteklenen sistem: Windows 10/11 x64.

1. [Son Windows kurulum dosyasini indirin](https://github.com/beyazitkolemen/kantar-servisi/releases/latest/download/Kantar-Servisi-Setup.exe).
2. `Kantar-Servisi-Setup.exe` dosyasini calistirin.
3. Baslat menusundeki **Kantar Servisi** kisayolunu acin.
4. Sistem tepsisi simgesinden yonetim panelini, log klasorunu ve servis yeniden baslatma islemini yonetin.

Ilk GitHub Release yayinlanmadan sabit indirme baglantisi `404` doner. Release olustugunda ayni baglanti her zaman son kararli kurulum dosyasini indirir.

## Adresler

Varsayilan servis adresi `http://127.0.0.1`:

| Islem | Adres |
| --- | --- |
| Tekli kantar | `http://127.0.0.1/` |
| Kantar 1 | `http://127.0.0.1/?profil=kantar1` |
| Kantar 2 | `http://127.0.0.1/?profil=kantar2` |
| JSON agirlik API | `http://127.0.0.1/api/v1/agirlik?profil=kantar1` |
| Ayarlar | `http://127.0.0.1/ayarlar` |
| Serial izleme | `http://127.0.0.1/serial` |
| Loglar | `http://127.0.0.1/loglar` |
| Surum ve guncelleme | `http://127.0.0.1/sistem` |
| Saglik kontrolu | `http://127.0.0.1/saglik` |

Duz metin `/` endpointi mevcut entegrasyonlarla uyumluluk icin korunur. Yeni entegrasyonlarda durum kodu, profil, agirlik ve hata alanlarini birlikte sunan `/api/v1/agirlik` endpointi tercih edilmelidir.

Basarili JSON yaniti:

```json
{
  "ok": true,
  "profil": "kantar1",
  "agirlik": "125",
  "zaman": "2026-06-13T14:30:00"
}
```

## Guvenlik Modeli

- HTTP sunucusu yalnizca yerel makine adreslerine baglanir.
- Yonetim panelindeki ayar kaydetme ve log temizleme islemleri CSRF korumalidir.
- Tarayici guvenlik basliklari ve katı Content Security Policy etkindir.
- Agirlik endpointlerine CORS erisimi yalnizca `https://*.lisdep.com` ve yerel gelistirme originleri icin verilir.
- Servis host ayari guvenlik nedeniyle bir loopback adresi olmalidir.

Servisin yerel agdaki baska bilgisayarlara acilmasi desteklenmez. Bu ihtiyac icin kimlik dogrulamali ayri bir ag gecidi kullanilmalidir.

## Yerel Veriler

Ayarlar ve loglar uygulama kurulum klasorunden ayri tutulur:

```text
%LOCALAPPDATA%\Kantar Servisi\
├── kantar-ayarlar.sqlite
└── kantar-servis.log
```

Eski `C:\kantar\kantar-ayarlar.sqlite` dosyasi varsa ilk calistirmada otomatik olarak yeni konuma kopyalanir. Guncelleme ve kaldirma islemleri kullanici ayarlarini silmez.

Seri port, baud hizi ve veri ayiklama ayarlari profil bazindadir. Servis host ve port ayarlari ise calisan HTTP sunucusu tek oldugu icin tum profillerde ortaktir.

Ortam degiskenleri:

| Degisken | Amac |
| --- | --- |
| `KANTAR_VERI_DIZINI` | Ayar ve log ana klasorunu degistirir |
| `KANTAR_AYAR_DB` | SQLite dosyasini dogrudan belirler |
| `KANTAR_LOG_DOSYA` | Log dosyasini dogrudan belirler |
| `KANTAR_SERVIS_HOST` | Kayitli host ayarini gecici olarak ezer |
| `KANTAR_SERVIS_PORT` | Kayitli port ayarini gecici olarak ezer |
| `KANTAR_AYAR_PROFILI` | Varsayilan kantar profilini belirler |

## Gelistirme

Python 3.9 veya daha yeni bir surum ve Node.js 20 gerekir.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
npm ci
npm run build:css
python -m pytest
python -m kantar_servis
```

Kaynak koddan yalnizca HTTP servisini calistirmak icin:

```powershell
python -m kantar_servis --server
```

## GitHub Release Akisi

`.github/workflows/release.yml`, `v*` etiketi push edildiginde Windows kurulumunu otomatik olusturur.

1. `kantar_servis/__init__.py` icindeki `__version__` degerini guncelleyin.
2. Degisiklikleri `main` dalina alin.
3. Ayni surumle etiket olusturup push edin:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

Workflow su dosyalari GitHub Release varligi olarak yayinlar:

- `Kantar-Servisi-Setup.exe`
- `Kantar-Servisi-Portable.zip`
- `SHA256SUMS.txt`

Etiket ile uygulama surumu eslesmezse release islemi durur. CI hem Linux hem Windows uzerinde testleri, CSS uretimini ve Python paketini dogrular.

GitHub Actions calisma izinleri veya hesap faturalandirmasi devre disiysa otomatik paketleme baslamaz. Bu durumda once depo Actions erisimi duzeltilmeli, ardindan ayni etiketin workflow'u yeniden calistirilmalidir.

## Sorun Giderme

- Servis acilmiyorsa `%LOCALAPPDATA%\Kantar Servisi\kantar-servis.log` dosyasini kontrol edin.
- Port 80 baska bir program tarafindan kullaniliyorsa panelden 8090 gibi bos bir yerel port secin ve sistem tepsisi menusunden servisi yeniden baslatin.
- COM port gorunmuyorsa USB/RS232 surucusunu ve Windows Aygit Yoneticisi'ni kontrol edin.
- GitHub surum kontrolu gecici ag hatalarini kisa sure onbellege alir; Sistem ekranindaki **Surumu Yeniden Kontrol Et** baglantisi onbellegi atlar.

## Kod Imzalama

Windows imzalama sertifikasi varsa depo ayarlarinda su Actions secret degerlerini tanimlayin:

- `WINDOWS_CERTIFICATE_BASE64`: PFX dosyasinin Base64 icerigi
- `WINDOWS_CERTIFICATE_PASSWORD`: PFX parolasi

Secret degerleri yoksa paket uretilir ancak Windows SmartScreen imzalanmamis uygulama uyarisi gosterebilir.
