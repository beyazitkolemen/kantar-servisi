# -*- coding: cp1254 -*-
import os
import re
import threading
import time

try:
    import serial
except ImportError:
    serial = None

from .config import ayar_float, ayar_int
from .errors import KantarHatasi
from .logging_utils import gunluge_yaz
from .storage import ayarlari_oku

_PORT_KILITLERI = {}
_PORT_KILITLERI_KILIDI = threading.Lock()


def _port_kilidi(seri_port):
    kilit_anahtari = os.path.normcase(os.path.normpath(seri_port))
    with _PORT_KILITLERI_KILIDI:
        if kilit_anahtari not in _PORT_KILITLERI:
            _PORT_KILITLERI[kilit_anahtari] = threading.Lock()
        return _PORT_KILITLERI[kilit_anahtari]


def _seri_portu_dogrula(seri_port):
    seri_port = str(seri_port or "").strip()
    if not seri_port or len(seri_port) > 128 or any(ord(karakter) < 32 for karakter in seri_port):
        raise KantarHatasi("Seri port adi gecersiz.", [
            "Ayarlar sayfasindan Windows tarafindan listelenen bir COM port secin.",
        ])
    return seri_port


def ham_veriyi_duzenle(ham_veri):
    if isinstance(ham_veri, bytes):
        return ham_veri.decode("cp1254", errors="ignore")
    return str(ham_veri)


def ham_veri_hex(ham_veri):
    if isinstance(ham_veri, bytes):
        return " ".join(["%02X" % byte for byte in ham_veri])
    return " ".join(["%02X" % ord(karakter) for karakter in str(ham_veri)])


def agirlik_degerini_ayikla(ham_metin, ayarlar=None):
    if ayarlar is None:
        ayarlar = ayarlari_oku()
    if not ham_metin:
        raise KantarHatasi("Kantardan veri gelmedi.", [
            "Kantar cihazinin acik oldugunu kontrol edin.",
            "Seri kablonun takili oldugunu kontrol edin.",
            "127.0.0.1/ayarlar sayfasindan seri port ve baud hizi ayarlarini kontrol edin.",
            "Gerekirse seri zaman asimi degerini artirin.",
        ])

    izinli_baslangic_bitleri = tuple(
        bit.strip()
        for bit in ayarlar.get("baslangic_bitleri", "A,@").split(",")
        if bit.strip()
    )
    agirlik_baslangic_indeksi = ayar_int(ayarlar, "agirlik_baslangic_indeksi")
    agirlik_bitis_indeksi = ayar_int(ayarlar, "agirlik_bitis_indeksi")
    baslangic_biti = ham_metin[0]
    gunluge_yaz("Baslangic biti: " + baslangic_biti)
    if baslangic_biti not in izinli_baslangic_bitleri:
        raise KantarHatasi(
            "Kantardan gelen veri beklenen baslangic bitiyle baslamiyor.",
            [
                "Cihaz protokolunde tartim baslangic biti farkliysa 127.0.0.1/ayarlar sayfasindan baslangic bitlerini guncelleyin.",
                "Gecerli bitler: %s" % ", ".join(izinli_baslangic_bitleri),
                "Seri porttan gelen ham veri uzunlugunu ve formatini kontrol edin.",
            ],
            "Gelen veri: %r" % ham_metin
        )

    agirlik_metni = ham_metin[agirlik_baslangic_indeksi:agirlik_bitis_indeksi].strip()
    gunluge_yaz("Tartim Degeri: " + agirlik_metni)
    if not agirlik_metni:
        raise KantarHatasi("Agirlik alani bos geldi.", [
            "127.0.0.1/ayarlar sayfasindan agirlik karakter araligini guncelleyin.",
            "Seri okuma boyutu ham veriyi tam okuyacak kadar buyuk olmali.",
        ], "Gelen veri: %r" % ham_metin)

    eslesmeler = re.findall(r"[-+]?\d+(?:[,.]\d+)?", agirlik_metni)
    if not eslesmeler:
        raise KantarHatasi("Agirlik alaninda sayisal deger bulunamadi.", [
            "Kantar ekraninda stabil tartim oldugunu kontrol edin.",
            "Agirlik karakter araligi yanlissa 127.0.0.1/ayarlar sayfasindan indeks ayarlarini guncelleyin.",
            "Cihaz farkli format gonderiyorsa ayiklama kuralini cihaza gore uyarlayin.",
        ], "Ayiklanan alan: %r, gelen veri: %r" % (agirlik_metni, ham_metin))

    deger = eslesmeler[0].replace(",", ".")
    if "." in deger:
        return ("%.3f" % float(deger)).rstrip("0").rstrip(".")
    return str(int(float(deger)))


def seri_baglantidan_oku(ayarlar):
    if serial is None:
        raise KantarHatasi("pyserial paketi kurulu degil.", ["Komut satirinda pip install pyserial calistirin."])
    seri_port = _seri_portu_dogrula(ayarlar.get("seri_port", "COM2"))
    seri_baud_hizi = ayar_int(ayarlar, "seri_baud_hizi")
    seri_zaman_asimi = ayar_float(ayarlar, "seri_zaman_asimi")
    seri_okuma_boyutu = ayar_int(ayarlar, "seri_okuma_boyutu")
    with _port_kilidi(seri_port):
        seri_baglanti = None
        try:
            seri_baglanti = serial.Serial(seri_port, seri_baud_hizi, timeout=seri_zaman_asimi)
            return seri_baglanti.readline(seri_okuma_boyutu)
        except KantarHatasi:
            raise
        except Exception as hata:
            raise KantarHatasi("Seri port baglantisi kurulamadi.", [
                "Ayarlar sayfasindan seri port ayarini kontrol edin. Windows icin ornek: COM2.",
                "Port baska bir program tarafindan kullaniliyor olabilir; diger kantar programlarini kapatin.",
                "USB/RS232 donusturucu surucusunun yuklu oldugunu kontrol edin.",
                "Baud hizi ayarinin cihazla ayni oldugunu kontrol edin.",
            ], str(hata))
        finally:
            if seri_baglanti is not None:
                seri_baglanti.close()


def kantar_degerini_oku(kantar_id=None):
    ayarlar = ayarlari_oku(kantar_id)
    if ayarlar.get("_kantar_yok"):
        raise KantarHatasi("Henuz kantar eklenmedi.", [
            "Yonetim panelindeki Kantar Ekle alanindan ilk kantari ekleyin.",
        ])
    ham_veri = seri_baglantidan_oku(ayarlar)
    ham_metin = ham_veriyi_duzenle(ham_veri)
    gunluge_yaz("Kantardan Gelen veri: " + ham_metin)
    return agirlik_degerini_ayikla(ham_metin, ayarlar)


def serial_ham_veri_oku(kantar_id=None, seri_port=None):
    ayarlar = ayarlari_oku(kantar_id)
    if ayarlar.get("_kantar_yok"):
        raise KantarHatasi("Henuz kantar eklenmedi.", [
            "Yonetim panelindeki Kantar Ekle alanindan ilk kantari ekleyin.",
        ])
    if seri_port:
        ayarlar["seri_port"] = seri_port
    ham_veri = seri_baglantidan_oku(ayarlar)
    ham_metin = ham_veriyi_duzenle(ham_veri)
    sonuc = {
        "ok": True,
        "kantar": ayarlar.get("_kantar_id", ""),
        "kantar_adi": ayarlar.get("_kantar_adi", ""),
        "profil": ayarlar.get("_kantar_id", ""),
        "seri_port": ayarlar.get("seri_port", "COM2"),
        "baud_hizi": ayar_int(ayarlar, "seri_baud_hizi"),
        "timeout": ayar_float(ayarlar, "seri_zaman_asimi"),
        "okuma_boyutu": ayar_int(ayarlar, "seri_okuma_boyutu"),
        "ham_veri": ham_metin,
        "ham_hex": ham_veri_hex(ham_veri),
        "ham_uzunluk": len(ham_metin),
        "zaman": time.strftime("%H:%M:%S"),
        "agirlik": None,
        "uyari": "",
    }
    try:
        sonuc["agirlik"] = agirlik_degerini_ayikla(ham_metin, ayarlar)
    except KantarHatasi as hata:
        sonuc["uyari"] = hata.kullanici_mesaji()
    return sonuc


def seri_portlari_listele():
    portlar = []
    if serial is None:
        return portlar
    try:
        from serial.tools import list_ports
        for port in list_ports.comports():
            cihaz = str(getattr(port, "device", "") or "").strip()
            if not cihaz:
                continue
            aciklama = str(getattr(port, "description", "") or cihaz).strip()
            portlar.append((cihaz, aciklama))
    except Exception as hata:
        gunluge_yaz("Seri port listesi okunamadi: %s" % hata)
        return []
    tekil = {}
    for cihaz, aciklama in portlar:
        tekil[cihaz] = aciklama
    return sorted(tekil.items(), key=lambda item: item[0].lower())


def seri_port_secenekleri(secili, portlar):
    secili = str(secili or "").strip()
    secenekler = []
    port_adlari = [cihaz for cihaz, _aciklama in portlar]
    if secili and secili not in port_adlari:
        secenekler.append({"value": secili, "label": "Kayitli port: %s" % secili, "selected": True})
    for cihaz, aciklama in portlar:
        etiket = cihaz
        if aciklama and aciklama != cihaz:
            etiket = "%s - %s" % (cihaz, aciklama)
        secenekler.append({"value": cihaz, "label": etiket, "selected": cihaz == secili})
    if not secenekler:
        secenekler.append({"value": secili, "label": secili or "Aktif port bulunamadi", "selected": True})
    return secenekler


def seri_port_bilgileri(portlar):
    bilgiler = []
    for cihaz, aciklama in portlar:
        etiket = cihaz
        if aciklama and aciklama != cihaz:
            etiket = "%s - %s" % (cihaz, aciklama)
        bilgiler.append({"cihaz": cihaz, "aciklama": aciklama, "etiket": etiket})
    return bilgiler
