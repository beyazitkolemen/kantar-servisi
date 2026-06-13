# -*- coding: cp1254 -*-
import os

UYGULAMA_ADI = "Kantar Servisi"
GITHUB_REPO = "beyazitkolemen/kantar-servisi"
GITHUB_REPO_URL = "https://github.com/%s" % GITHUB_REPO
GITHUB_RELEASES_URL = "%s/releases" % GITHUB_REPO_URL
GITHUB_LATEST_INSTALLER_URL = "%s/latest/download/Kantar-Servisi-Setup.exe" % GITHUB_RELEASES_URL

PROFIL_TEKLI = "tekli"
PROFIL_KANTAR1 = "kantar1"
PROFIL_KANTAR2 = "kantar2"
PROFILLER = (PROFIL_TEKLI, PROFIL_KANTAR1, PROFIL_KANTAR2)

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
    return str(os.environ.get("KANTAR_SERVIS_HOST") or ayarlar.get("servis_host") or "127.0.0.1").strip()


def servis_portu(ayarlar):
    env_port = os.environ.get("KANTAR_SERVIS_PORT")
    if env_port:
        return guvenli_int(env_port, 80)
    return ayar_int(ayarlar, "servis_port")


def yerel_servis_url(ayarlar=None):
    if ayarlar is None:
        from .storage import ayarlari_oku
        ayarlar = ayarlari_oku()
    host = servis_hostu(ayarlar)
    if host in ("0.0.0.0", "::", "[::]"):
        host = "127.0.0.1"
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


def ayar_int(ayarlar, anahtar):
    profil = ayarlar.get("_profil", secili_profil())
    varsayilan = VARSAYILAN_AYARLAR.get(profil, VARSAYILAN_AYARLAR[PROFIL_TEKLI]).get(anahtar, "0")
    return guvenli_int(ayarlar.get(anahtar), varsayilan)


def ayar_float(ayarlar, anahtar):
    profil = ayarlar.get("_profil", secili_profil())
    varsayilan = VARSAYILAN_AYARLAR.get(profil, VARSAYILAN_AYARLAR[PROFIL_TEKLI]).get(anahtar, "0")
    return guvenli_float(ayarlar.get(anahtar), varsayilan)
