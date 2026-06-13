# -*- coding: cp1254 -*-
import os

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


KOK_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_KLASOR = os.path.join(KOK_DIZIN, "templates")


def klasor_olustur(yol):
    if yol and not os.path.isdir(yol):
        os.makedirs(yol)


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


def ayar_db_yolu():
    env_yol = os.environ.get("KANTAR_AYAR_DB")
    if env_yol:
        return env_yol
    if os.name == "nt":
        return os.path.join("C:\\kantar", "kantar-ayarlar.sqlite")
    return os.path.join(KOK_DIZIN, "kantar-ayarlar.sqlite")


def log_dosya_yolu():
    env_yol = os.environ.get("KANTAR_LOG_DOSYA")
    if env_yol:
        return env_yol
    if os.name == "nt":
        return os.path.join("C:\\kantar", "kantar-servis.log")
    return os.path.join(KOK_DIZIN, "kantar-servis.log")


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
