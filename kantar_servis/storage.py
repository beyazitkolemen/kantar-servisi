# -*- coding: cp1254 -*-
import os
import shutil
import sqlite3

from .config import AYAR_ALANLARI, klasor_olustur, ayar_db_yolu, profil_normalize, secili_profil, profil_varsayilanlari


def eski_ayar_db_yolu():
    if os.name != "nt":
        return None
    return os.path.join("C:\\kantar", "kantar-ayarlar.sqlite")


def eski_ayarlari_tasi():
    hedef = ayar_db_yolu()
    kaynak = eski_ayar_db_yolu()
    if not kaynak or os.path.isfile(hedef) or not os.path.isfile(kaynak):
        return False
    if os.path.normcase(os.path.abspath(kaynak)) == os.path.normcase(os.path.abspath(hedef)):
        return False
    klasor_olustur(os.path.dirname(hedef))
    shutil.copy2(kaynak, hedef)
    return True


def baglanti_ac():
    eski_ayarlari_tasi()
    db_yolu = ayar_db_yolu()
    klasor_olustur(os.path.dirname(db_yolu))
    baglanti = sqlite3.connect(db_yolu, timeout=10)
    baglanti.execute("PRAGMA busy_timeout = 10000")
    baglanti.execute(
        "CREATE TABLE IF NOT EXISTS kantar_ayarlar ("
        "profil TEXT NOT NULL, "
        "anahtar TEXT NOT NULL, "
        "deger TEXT NOT NULL, "
        "PRIMARY KEY (profil, anahtar)"
        ")"
    )
    return baglanti


def ayarlari_baslat():
    baglanti = baglanti_ac()
    try:
        from .config import PROFILLER
        for profil in PROFILLER:
            varsayilanlar = profil_varsayilanlari(profil)
            for anahtar, deger in varsayilanlar.items():
                baglanti.execute(
                    "INSERT OR IGNORE INTO kantar_ayarlar (profil, anahtar, deger) VALUES (?, ?, ?)",
                    (profil, anahtar, str(deger))
                )
        baglanti.commit()
    finally:
        baglanti.close()


def ayarlari_oku(profil=None):
    profil = profil_normalize(profil, secili_profil())
    ayarlari_baslat()
    ayarlar = profil_varsayilanlari(profil)
    ayarlar["_profil"] = profil
    baglanti = baglanti_ac()
    try:
        imlec = baglanti.execute("SELECT anahtar, deger FROM kantar_ayarlar WHERE profil = ?", (profil,))
        for anahtar, deger in imlec.fetchall():
            ayarlar[anahtar] = deger
    finally:
        baglanti.close()
    return ayarlar


def ayarlari_kaydet(profil, ayarlar):
    profil = profil_normalize(profil, secili_profil())
    ayarlari_baslat()
    baglanti = baglanti_ac()
    try:
        for anahtar, _label, _tip in AYAR_ALANLARI:
            baglanti.execute(
                "INSERT OR REPLACE INTO kantar_ayarlar (profil, anahtar, deger) VALUES (?, ?, ?)",
                (profil, anahtar, str(ayarlar.get(anahtar, "")))
            )
        baglanti.commit()
    finally:
        baglanti.close()


def sqlite_durumu_oku():
    yol = ayar_db_yolu()
    try:
        ayarlari_baslat()
        yazilabilir = os.access(os.path.dirname(yol) or ".", os.W_OK)
        return {
            "ok": True,
            "baslik": "Hazir",
            "yol": yol,
            "mesaj": "" if yazilabilir else "SQLite klasoru yazilabilir gorunmuyor. Kantar baslaticisini yonetici olarak calistirmayi deneyin.",
        }
    except Exception as hata:
        return {
            "ok": False,
            "baslik": "Kontrol gerekli",
            "yol": yol,
            "mesaj": "SQLite ayar dosyasi olusturulamadi veya okunamadi: %s" % hata,
        }
