# -*- coding: utf-8 -*-
import os
import shutil
import sqlite3
import time
import uuid

from .config import (
    AYAR_ALANLARI,
    SERVIS_AYARLARI,
    VARSAYILAN_KANTAR_AYARLARI,
    VARSAYILAN_SERVIS_AYARLARI,
    ayar_db_yolu,
    ayarlari_dogrula,
    kantar_kimligi_normalize,
    kantar_varsayilan_ayarlari,
    klasor_olustur,
    secili_kantar_kimligi,
    secili_kantar_secimi,
)

SERVIS_PROFILI = "__servis__"
ESKI_PROFILLER = ("tekli", "kantar1", "kantar2")
ESKI_VARSAYILANLAR = {
    "tekli": dict(VARSAYILAN_KANTAR_AYARLARI, seri_port="COM2"),
    "kantar1": dict(VARSAYILAN_KANTAR_AYARLARI, seri_port="COM2"),
    "kantar2": dict(VARSAYILAN_KANTAR_AYARLARI, seri_port="COM3"),
}
MIGRATION_ANAHTARI = "dinamik_kantarlar_v1"


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
    baglanti.row_factory = sqlite3.Row
    try:
        baglanti.execute("PRAGMA busy_timeout = 10000")
        baglanti.execute("PRAGMA journal_mode = WAL")
        baglanti.execute("PRAGMA foreign_keys = ON")
        baglanti.execute(
            "CREATE TABLE IF NOT EXISTS kantar_ayarlar ("
            "profil TEXT NOT NULL, "
            "anahtar TEXT NOT NULL, "
            "deger TEXT NOT NULL, "
            "PRIMARY KEY (profil, anahtar)"
            ")"
        )
        baglanti.execute(
            "CREATE TABLE IF NOT EXISTS kantarlar ("
            "id TEXT PRIMARY KEY, "
            "ad TEXT NOT NULL COLLATE NOCASE UNIQUE, "
            "sira INTEGER NOT NULL, "
            "olusturma_zamani TEXT NOT NULL"
            ")"
        )
        baglanti.execute(
            "CREATE TABLE IF NOT EXISTS uygulama_meta ("
            "anahtar TEXT PRIMARY KEY, "
            "deger TEXT NOT NULL"
            ")"
        )
        baglanti.execute(
            "CREATE TABLE IF NOT EXISTS kantar_aliaslari ("
            "alias TEXT PRIMARY KEY, "
            "kantar_id TEXT NOT NULL, "
            "FOREIGN KEY (kantar_id) REFERENCES kantarlar(id) ON DELETE CASCADE"
            ")"
        )
        return baglanti
    except Exception:
        baglanti.close()
        raise


def _kantar_adi_dogrula(ad):
    ad = " ".join(str(ad or "").strip().split())
    if not ad:
        raise ValueError("Kantar adi bos birakilamaz.")
    if len(ad) > 80 or any(ord(karakter) < 32 for karakter in ad):
        raise ValueError("Kantar adi en fazla 80 karakter olabilir.")
    return ad


def _kantar_kimligi_uret():
    return "kantar-%s" % uuid.uuid4().hex


def _kantar_ekle_baglanti(baglanti, ad, ayarlar=None):
    ad = _kantar_adi_dogrula(ad)
    kantar_id = _kantar_kimligi_uret()
    sira = baglanti.execute("SELECT COALESCE(MAX(sira), 0) + 1 FROM kantarlar").fetchone()[0]
    baglanti.execute(
        "INSERT INTO kantarlar (id, ad, sira, olusturma_zamani) VALUES (?, ?, ?, ?)",
        (kantar_id, ad, sira, time.strftime("%Y-%m-%dT%H:%M:%S")),
    )
    kaynak = dict(VARSAYILAN_KANTAR_AYARLARI)
    if ayarlar:
        kaynak.update({anahtar: ayarlar[anahtar] for anahtar in VARSAYILAN_KANTAR_AYARLARI if anahtar in ayarlar})
    for anahtar, deger in kaynak.items():
        baglanti.execute(
            "INSERT INTO kantar_ayarlar (profil, anahtar, deger) VALUES (?, ?, ?)",
            (kantar_id, anahtar, str(deger)),
        )
    return kantar_id


def _eski_profilleri_tasi(baglanti):
    tamamlandi = baglanti.execute(
        "SELECT 1 FROM uygulama_meta WHERE anahtar = ?",
        (MIGRATION_ANAHTARI,),
    ).fetchone()
    if tamamlandi:
        return
    mevcut_kantar = baglanti.execute("SELECT 1 FROM kantarlar LIMIT 1").fetchone()
    if not mevcut_kantar:
        for profil in ESKI_PROFILLER:
            satirlar = baglanti.execute(
                "SELECT anahtar, deger FROM kantar_ayarlar WHERE profil = ?",
                (profil,),
            ).fetchall()
            kayitli = {satir["anahtar"]: satir["deger"] for satir in satirlar}
            varsayilan = ESKI_VARSAYILANLAR[profil]
            ozellestirilmis = any(
                kayitli.get(anahtar, varsayilan[anahtar]) != varsayilan[anahtar]
                for anahtar in VARSAYILAN_KANTAR_AYARLARI
            )
            if ozellestirilmis:
                ad = {"tekli": "Kantar", "kantar1": "Kantar 1", "kantar2": "Kantar 2"}[profil]
                kantar_id = _kantar_ekle_baglanti(baglanti, ad, kayitli)
                baglanti.execute(
                    "INSERT OR REPLACE INTO kantar_aliaslari (alias, kantar_id) VALUES (?, ?)",
                    (profil, kantar_id),
                )
    baglanti.execute(
        "INSERT OR REPLACE INTO uygulama_meta (anahtar, deger) VALUES (?, ?)",
        (MIGRATION_ANAHTARI, "1"),
    )


def ayarlari_baslat():
    baglanti = baglanti_ac()
    try:
        for anahtar, deger in VARSAYILAN_SERVIS_AYARLARI.items():
            mevcut = baglanti.execute(
                "SELECT 1 FROM kantar_ayarlar WHERE profil = ? AND anahtar = ?",
                (SERVIS_PROFILI, anahtar),
            ).fetchone()
            if mevcut:
                continue
            eski = baglanti.execute(
                "SELECT deger FROM kantar_ayarlar "
                "WHERE profil IN ('tekli', 'kantar1', 'kantar2') AND anahtar = ? "
                "ORDER BY CASE profil WHEN 'tekli' THEN 0 WHEN 'kantar1' THEN 1 ELSE 2 END LIMIT 1",
                (anahtar,),
            ).fetchone()
            baglanti.execute(
                "INSERT INTO kantar_ayarlar (profil, anahtar, deger) VALUES (?, ?, ?)",
                (SERVIS_PROFILI, anahtar, str(eski["deger"] if eski else deger)),
            )
        _eski_profilleri_tasi(baglanti)
        baglanti.commit()
    finally:
        baglanti.close()


def kantarlari_listele():
    ayarlari_baslat()
    baglanti = baglanti_ac()
    try:
        return [
            {"id": satir["id"], "ad": satir["ad"], "sira": satir["sira"]}
            for satir in baglanti.execute(
                "SELECT id, ad, sira FROM kantarlar ORDER BY sira, ad"
            ).fetchall()
        ]
    finally:
        baglanti.close()


def kantar_sec(kantar_id=None):
    ayarlari_baslat()
    ham_istenen = str(kantar_id or "").strip().lower()
    acik_secim = bool(ham_istenen)
    istenen = kantar_kimligi_normalize(ham_istenen)
    if not acik_secim:
        ham_istenen = secili_kantar_secimi()
        istenen = secili_kantar_kimligi()
    baglanti = baglanti_ac()
    try:
        if istenen:
            satir = baglanti.execute(
                "SELECT id, ad, sira FROM kantarlar WHERE id = ?",
                (istenen,),
            ).fetchone()
            if satir:
                return {"id": satir["id"], "ad": satir["ad"], "sira": satir["sira"]}
        if ham_istenen:
            satir = baglanti.execute(
                "SELECT k.id, k.ad, k.sira FROM kantar_aliaslari a "
                "JOIN kantarlar k ON k.id = a.kantar_id WHERE a.alias = ?",
                (ham_istenen,),
            ).fetchone()
            if satir:
                return {"id": satir["id"], "ad": satir["ad"], "sira": satir["sira"]}
        if acik_secim:
            return None
        satir = baglanti.execute(
            "SELECT id, ad, sira FROM kantarlar ORDER BY sira, ad LIMIT 1"
        ).fetchone()
        return {"id": satir["id"], "ad": satir["ad"], "sira": satir["sira"]} if satir else None
    finally:
        baglanti.close()


def kantar_ekle(ad):
    ayarlari_baslat()
    baglanti = baglanti_ac()
    try:
        kantar_id = _kantar_ekle_baglanti(baglanti, ad)
        baglanti.commit()
        return kantar_id
    except sqlite3.IntegrityError:
        raise ValueError("Ayni ada sahip bir kantar zaten var.")
    finally:
        baglanti.close()


def kantar_sil(kantar_id):
    kantar_id = kantar_kimligi_normalize(kantar_id)
    if not kantar_id:
        return False
    ayarlari_baslat()
    baglanti = baglanti_ac()
    try:
        silinen = baglanti.execute("DELETE FROM kantarlar WHERE id = ?", (kantar_id,)).rowcount
        if silinen:
            baglanti.execute("DELETE FROM kantar_ayarlar WHERE profil = ?", (kantar_id,))
            baglanti.commit()
        return bool(silinen)
    finally:
        baglanti.close()


def ayarlari_oku(kantar_id=None):
    ayarlari_baslat()
    kantar = kantar_sec(kantar_id)
    ayarlar = kantar_varsayilan_ayarlari()
    ayarlar["_kantar_id"] = kantar["id"] if kantar else ""
    ayarlar["_kantar_adi"] = kantar["ad"] if kantar else ""
    ayarlar["_kantar_yok"] = kantar is None
    baglanti = baglanti_ac()
    try:
        if kantar:
            for satir in baglanti.execute(
                "SELECT anahtar, deger FROM kantar_ayarlar WHERE profil = ?",
                (kantar["id"],),
            ).fetchall():
                ayarlar[satir["anahtar"]] = satir["deger"]
        for satir in baglanti.execute(
            "SELECT anahtar, deger FROM kantar_ayarlar WHERE profil = ?",
            (SERVIS_PROFILI,),
        ).fetchall():
            ayarlar[satir["anahtar"]] = satir["deger"]
    finally:
        baglanti.close()
    return ayarlar


def ayarlari_kaydet(kantar_id, ayarlar, kantar_adi=None):
    kantar = kantar_sec(kantar_id)
    if not kantar or kantar["id"] != kantar_kimligi_normalize(kantar_id):
        raise ValueError("Ayarları kaydedilecek kantar bulunamadi.")
    normalize = ayarlari_dogrula(ayarlar)
    normalize_ad = _kantar_adi_dogrula(kantar_adi) if kantar_adi is not None else None
    ayarlari_baslat()
    baglanti = baglanti_ac()
    try:
        if normalize_ad is not None:
            baglanti.execute(
                "UPDATE kantarlar SET ad = ? WHERE id = ?",
                (normalize_ad, kantar["id"]),
            )
        for anahtar, _label, _tip in AYAR_ALANLARI:
            hedef = SERVIS_PROFILI if anahtar in SERVIS_AYARLARI else kantar["id"]
            baglanti.execute(
                "INSERT OR REPLACE INTO kantar_ayarlar (profil, anahtar, deger) VALUES (?, ?, ?)",
                (hedef, anahtar, normalize[anahtar]),
            )
        baglanti.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Ayni ada sahip bir kantar zaten var.")
    finally:
        baglanti.close()
    normalize["_kantar_id"] = kantar["id"]
    normalize["_kantar_adi"] = normalize_ad if normalize_ad is not None else kantar["ad"]
    return normalize


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
