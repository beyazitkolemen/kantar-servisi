# Kantar Servisi

Kantar Servisi, Windows bilgisayardaki seri porttan kantar verisini okuyup yerel HTTP adresi uzerinden sunan masaustu uygulamasidir. Python kurulumu veya `.bat` dosyasi gerektirmez.

## Windows Kurulumu

Desteklenen sistem: Windows 10/11 x64.

1. [Hazir Windows kurulum dosyasini indirin](https://raw.githubusercontent.com/beyazitkolemen/kantar-servisi/main/downloads/Kantar-Servisi-Setup.exe).
2. `Kantar-Servisi-Setup.exe` dosyasini calistirin.
3. Baslat menusundeki **Kantar Servisi** kisayolunu acin.
4. Sistem tepsisi simgesinden yonetim panelini, log klasorunu ve servis yeniden baslatma islemini yonetin.

Kurulum dosyasi GitHub Actions veya GitHub Releases tarafinda uretilmez. Yerelde derlenip test edildikten sonra `downloads/Kantar-Servisi-Setup.exe` olarak dogrudan depoya eklenir.

## Windows Masaustu Deneyimi

Uygulama Python konsolu veya `.bat` dosyasi gostermeden Windows sistem tepsisinde calisir.

- Tepsi menusunde canli servis durumu gorunur.
- Yonetim paneli, serial izleme, loglar ve sistem ekrani ayri kisayollardan acilir.
- Servis beklenmedik sekilde kapanirsa masaustu uygulamasi durumu bildirir ve bir kez otomatik yeniden baslatmayi dener.
- **Servisi Yeniden Baslat** islemi arka planda calisir; tepsi menusu donmaz.
- **Tanilama Raporu Olustur** secenegi surum, servis sagligi, dosya yollari, COM portlari ve profil ayarlarini tek metin dosyasinda toplar.
- Ayni kullanici oturumunda yalnizca bir Kantar Servisi tepsi uygulamasi calisir. Ikinci acilis mevcut servisin panelini acar.
- Windows acilisinda calistirma ve masaustu kisayolu kurulum ekranindan secilebilir.

Baslat menusu ayrica yonetim paneli, log klasoru, tanilama raporu ve kaldirma kisayollarini icerir. Kurulum kullanici bazlidir ve yonetici yetkisi istemez.

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

Masaustu/otomasyon komutlari:

```powershell
KantarServisi.exe --open-panel
KantarServisi.exe --open-logs
KantarServisi.exe --diagnostics
KantarServisi.exe --health-check
```

`--health-check`, servis hazirsa `0`, erisilemiyorsa `1` cikis kodu verir.

## Yerel Windows Build

Windows kurulum dosyasi GitHub tarafinda olusturulmaz. Docker calisan macOS, Linux veya Windows gelistirme makinesinde su komut kullanilir:

```powershell
python scripts/build_windows_local.py
```

Komut sirasiyla CSS dosyasini, uygulama ikonlarini, SHA256 ile dogrulanan resmi Windows Python 3.12 calisma zamanini, sabitlenmis Windows bagimliliklarini, x64 `KantarServisi.exe` baslaticisini ve NSIS kurulumunu uretir. Hedef bilgisayarda Python, Docker veya `.bat` dosyasi gerekmez.

Olusan ve Git ile birlikte gonderilmesi gereken dosyalar:

- `downloads/Kantar-Servisi-Setup.exe`
- `downloads/latest.json`
- `downloads/SHA256SUMS.txt`

`latest.json`, uygulamanin Sistem ekraninda kullandigi surum ve SHA256 bilgisidir. Build islemi kurulum dosyasinin gercek Windows PE formati tasidigini ve GitHub'in 100 MiB tek dosya sinirini asmadigini otomatik denetler.

Yeni bir surum yayinlama adimlari:

1. `kantar_servis/__init__.py` icindeki `__version__` degerini guncelleyin.
2. `python -m pytest` komutunu calistirin.
3. `python scripts/build_windows_local.py` komutuyla Windows paketini yerelde olusturun.
4. `downloads/` altindaki EXE, manifest ve checksum dosyalarini kaynak kodla ayni commit icinde GitHub'a gonderin.

Gercek bir Windows makinede kurulum, servis, HTTP guvenligi ve kaldirma akisini yeniden denetlemek icin:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows_installer_smoke_test.ps1 -Installer downloads\Kantar-Servisi-Setup.exe
```

Depoda `.github/workflows` bulunmaz ve GitHub Actions kullanilmaz.

## Sorun Giderme

- Servis acilmiyorsa `%LOCALAPPDATA%\Kantar Servisi\kantar-servis.log` dosyasini kontrol edin.
- Sistem tepsisi menusunden **Tanilama Raporu Olustur** secenegini kullanarak destek raporu olusturun.
- Port 80 baska bir program tarafindan kullaniliyorsa panelden 8090 gibi bos bir yerel port secin ve sistem tepsisi menusunden servisi yeniden baslatin.
- COM port gorunmuyorsa USB/RS232 surucusunu ve Windows Aygit Yoneticisi'ni kontrol edin.
- GitHub paket manifesti kontrolu gecici ag hatalarini kisa sure onbellege alir; Sistem ekranindaki **Surumu Yeniden Kontrol Et** baglantisi onbellegi atlar.

## Kod Imzalama

Mevcut kurulum dosyasi sertifika ile imzalanmadiysa Windows SmartScreen ilk calistirmada bilinmeyen yayinci uyarisi gosterebilir. Kod imzalama sertifikasi kullanilacaksa imzalama islemi yerel build sonrasinda, EXE GitHub'a gonderilmeden once yapilmalidir.
