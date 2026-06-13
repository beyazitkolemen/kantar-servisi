# -*- coding: cp1254 -*-
import ipaddress
import math
import os

from .errors import AyarDogrulamaHatasi

UYGULAMA_ADI = "Kantar Servisi"
GITHUB_REPO = "beyazitkolemen/kantar-servisi"
GITHUB_REPO_URL = "https://github.com/%s" % GITHUB_REPO
GITHUB_RELEASES_URL = "%s/releases" % GITHUB_REPO_URL
GITHUB_LATEST_INSTALLER_URL = "%s/latest/download/Kantar-Servisi-Setup.exe" % GITHUB_RELEASES_URL

PROFIL_TEKLI = "tekli"
PROFIL_KANTAR1 = "kantar1"
PROFIL_KANTAR2 = "kantar2"
PROFILLER = (PROFIL_TEKLI, PROFIL_KANTAR1, PROFIL_KANTAR2)
SERVIS_AYARLARI = ("servis_host", "servis_port")

AYAR_ALANLARI = [
    ("seri_port", "Seri Port", "text"),
    ("seri_baud_hizi", "Baud Hizi", "number"),
    ("seri_zaman_asimi", "Zaman Asimi", "text"),
    ("seri_okuma_boyutu", "Okuma Boyutu", "number"),
    ("baslangic_bitleri", "Baslangic Bitleri", "text"),
    ("agirlik_baslangic_indeksi", "Agirlik Baslangic Indeksi", "number"),
    ("agirlik_bitis_indeksi", "Agirlik Bitis Indeksi", "number"),
    ("servis_host", "Servis Host", "text"),
    ("servis_port", "Servis Port", "number"),
]

VARSAYILAN_AYARLAR = {
    PROFIL_TEKLI: {
        "seri_port": "COM2",
        "seri_baud_hizi": "9600",
        "seri_zaman_asimi": "3",
        "seri_okuma_boyutu": "8",
        "baslangic_bitleri": "A,@",
        "agirlik_baslangic_indeksi": "3",
        "agirlik_bitis_indeksi": "10",
        "servis_host": "127.0.0.1",
        "servis_port": "80",
    },
    PROFIL_KANTAR1: {
        "seri_port": "COM2",
        "seri_baud_hizi": "9600",
        "seri_zaman_asimi": "3",
        "seri_okuma_boyutu": "8",
        "baslangic_bitleri": "A,@",
        "agirlik_baslangic_indeksi": "3",
        "agirlik_bitis_indeksi": "10",
        "servis_host": "127.0.0.1",
        "servis_port": "80",
    },
    PROFIL_KANTAR2: {
        "seri_port": "COM3",
        "seri_baud_hizi": "9600",
        "seri_zaman_asimi": "3",
        "seri_okuma_boyutu": "8",
        "baslangic_bitleri": "A,@",
        "agirlik_baslangic_indeksi": "3",
        "agirlik_bitis_indeksi": "10",
        "servis_host": "127.0.0.1",
        "servis_port": "80",
    },
}


PAKET_DIZIN = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_KLASOR = os.path.join(PAKET_DIZIN, "templates")
STATIC_KLASOR = os.path.join(PAKET_DIZIN, "static")

AYAR_GIRIS_OZELLIKLERI = {
    "seri_baud_hizi": {"min": "1", "max": "4000000", "step": "1"},
    "seri_zaman_asimi": {"min": "0.1", "max": "60", "step": "0.1"},
    "seri_okuma_boyutu": {"min": "1", "max": "4096", "step": "1"},
    "agirlik_baslangic_indeksi": {"min": "0", "max": "4095", "step": "1"},
    "agirlik_bitis_indeksi": {"min": "1", "max": "4096", "step": "1"},
    "servis_port": {"min": "1", "max": "65535", "step": "1"},
}


def klasor_olustur(yol):
    if yol and not os.path.isdir(yol):
        os.makedirs(yol, exist_ok=True)


def profil_normalize(profil, varsayilan=None):
    if varsayilan is None:
        varsayilan = PROFIL_TEKLI
    if profil is None:
        return varsayilan
    profil = str(profil).strip().lower()
    if profil not in PROFILLER:
        return varsayilan
    return profil


def secili_profil():
    return profil_normalize(os.environ.get("KANTAR_AYAR_PROFILI", PROFIL_TEKLI))


def uygulama_veri_dizini():
    env_yol = os.environ.get("KANTAR_VERI_DIZINI")
    if env_yol:
        return os.path.abspath(os.path.expanduser(env_yol))
    if os.name == "nt":
        yerel = os.environ.get("LOCALAPPDATA")
        if not yerel:
            yerel = os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(yerel, UYGULAMA_ADI)
    xdg_veri = os.environ.get("XDG_DATA_HOME")
    if not xdg_veri:
        xdg_veri = os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(xdg_veri, "kantar-servisi")


def ayar_db_yolu():
    env_yol = os.environ.get("KANTAR_AYAR_DB")
    if env_yol:
        return os.path.abspath(os.path.expanduser(env_yol))
    return os.path.join(uygulama_veri_dizini(), "kantar-ayarlar.sqlite")


def log_dosya_yolu():
    env_yol = os.environ.get("KANTAR_LOG_DOSYA")
    if env_yol:
        return os.path.abspath(os.path.expanduser(env_yol))
    return os.path.join(uygulama_veri_dizini(), "kantar-servis.log")


def servis_hostu(ayarlar):
    host = str(os.environ.get("KANTAR_SERVIS_HOST") or ayarlar.get("servis_host") or "127.0.0.1").strip().lower()
    if not loopback_host_mu(host):
        return "127.0.0.1"
    return host


def servis_portu(ayarlar):
    env_port = os.environ.get("KANTAR_SERVIS_PORT")
    if env_port:
        port = guvenli_int(env_port, 80)
    else:
        port = ayar_int(ayarlar, "servis_port")
    return port if 1 <= port <= 65535 else 80


def yerel_servis_url(ayarlar=None):
    if ayarlar is None:
        from .storage import ayarlari_oku
        ayarlar = ayarlari_oku()
    host = servis_hostu(ayarlar)
    if ":" in host and not host.startswith("["):
        host = "[%s]" % host
    port = servis_portu(ayarlar)
    port_metni = "" if port == 80 else ":%s" % port
    return "http://%s%s" % (host, port_metni)


def profil_varsayilanlari(profil):
    # Varsayilanlar sadece ilk SQLite kaydini olusturmak icin kullanilir.
    # Cihaz ve servis davranisi bundan sonra /ayarlar ekranindan yonetilir.
    return dict(VARSAYILAN_AYARLAR.get(profil, VARSAYILAN_AYARLAR[PROFIL_TEKLI]))


def guvenli_int(deger, varsayilan):
    try:
        return int(deger)
    except (TypeError, ValueError):
        return int(varsayilan)


def guvenli_float(deger, varsayilan):
    try:
        return float(deger)
    except (TypeError, ValueError):
        return float(varsayilan)


def loopback_host_mu(host):
    host = str(host or "").strip().lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _tam_sayi_dogrula(ayarlar, anahtar, etiket, en_az, en_cok, hatalar):
    try:
        deger = int(str(ayarlar.get(anahtar, "")).strip())
    except (TypeError, ValueError):
        hatalar.append("%s tam sayi olmalidir." % etiket)
        return None
    if deger < en_az or deger > en_cok:
        hatalar.append("%s %s ile %s arasinda olmalidir." % (etiket, en_az, en_cok))
        return None
    return deger


def _ondalik_dogrula(ayarlar, anahtar, etiket, en_az, en_cok, hatalar):
    ham_deger = str(ayarlar.get(anahtar, "")).strip().replace(",", ".")
    try:
        deger = float(ham_deger)
    except (TypeError, ValueError):
        hatalar.append("%s sayisal bir deger olmalidir." % etiket)
        return None
    if not math.isfinite(deger) or deger < en_az or deger > en_cok:
        hatalar.append("%s %s ile %s arasinda olmalidir." % (etiket, en_az, en_cok))
        return None
    return deger


def ayarlari_dogrula(ayarlar):
    hatalar = []
    normalize = {}

    seri_port = str(ayarlar.get("seri_port", "") or "").strip()
    if not seri_port:
        hatalar.append("Seri Port bos birakilamaz.")
    elif len(seri_port) > 128 or any(ord(karakter) < 32 for karakter in seri_port):
        hatalar.append("Seri Port gecersiz karakter iceriyor veya cok uzun.")
    normalize["seri_port"] = seri_port

    baud = _tam_sayi_dogrula(ayarlar, "seri_baud_hizi", "Baud Hizi", 1, 4000000, hatalar)
    timeout = _ondalik_dogrula(ayarlar, "seri_zaman_asimi", "Zaman Asimi", 0.1, 60, hatalar)
    okuma_boyutu = _tam_sayi_dogrula(ayarlar, "seri_okuma_boyutu", "Okuma Boyutu", 1, 4096, hatalar)
    baslangic = _tam_sayi_dogrula(ayarlar, "agirlik_baslangic_indeksi", "Agirlik Baslangic Indeksi", 0, 4095, hatalar)
    bitis = _tam_sayi_dogrula(ayarlar, "agirlik_bitis_indeksi", "Agirlik Bitis Indeksi", 1, 4096, hatalar)
    port = _tam_sayi_dogrula(ayarlar, "servis_port", "Servis Port", 1, 65535, hatalar)

    bitler = []
    for bit in str(ayarlar.get("baslangic_bitleri", "") or "").split(","):
        bit = bit.strip()
        if not bit:
            continue
        if len(bit) != 1 or ord(bit) < 32:
            hatalar.append("Baslangic Bitleri tek karakterlik, virgul ile ayrilmis degerler olmalidir.")
            bitler = []
            break
        if bit not in bitler:
            bitler.append(bit)
    if not bitler and not any("Baslangic Bitleri" in hata for hata in hatalar):
        hatalar.append("En az bir Baslangic Biti girilmelidir.")

    host = str(ayarlar.get("servis_host", "") or "").strip().lower()
    if not loopback_host_mu(host):
        hatalar.append("Servis Host guvenlik nedeniyle yalnizca yerel makine adresi olabilir.")
    elif host != "localhost":
        host = str(ipaddress.ip_address(host))

    if baslangic is not None and bitis is not None and bitis <= baslangic:
        hatalar.append("Agirlik Bitis Indeksi, baslangic indeksinden buyuk olmalidir.")

    if hatalar:
        raise AyarDogrulamaHatasi(hatalar)

    normalize.update({
        "seri_baud_hizi": str(baud),
        "seri_zaman_asimi": ("%g" % timeout),
        "seri_okuma_boyutu": str(okuma_boyutu),
        "baslangic_bitleri": ",".join(bitler),
        "agirlik_baslangic_indeksi": str(baslangic),
        "agirlik_bitis_indeksi": str(bitis),
        "servis_host": host,
        "servis_port": str(port),
    })
    return normalize


def ayar_int(ayarlar, anahtar):
    profil = ayarlar.get("_profil", secili_profil())
    varsayilan = VARSAYILAN_AYARLAR.get(profil, VARSAYILAN_AYARLAR[PROFIL_TEKLI]).get(anahtar, "0")
    return guvenli_int(ayarlar.get(anahtar), varsayilan)


def ayar_float(ayarlar, anahtar):
    profil = ayarlar.get("_profil", secili_profil())
    varsayilan = VARSAYILAN_AYARLAR.get(profil, VARSAYILAN_AYARLAR[PROFIL_TEKLI]).get(anahtar, "0")
    return guvenli_float(ayarlar.get(anahtar), varsayilan)
