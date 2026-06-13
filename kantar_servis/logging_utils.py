# -*- coding: cp1254 -*-
import os
import sys
import time

from .config import klasor_olustur, log_dosya_yolu

LOG_MAKSIMUM_BYTE = 1024 * 1024
LOG_YEDEK_SAYISI = 5


def _log_yedek_yolu(yol, sira):
    return "%s.%s" % (yol, sira)


def log_dosyasini_dondur(yol=None):
    if yol is None:
        yol = log_dosya_yolu()
    try:
        if not os.path.isfile(yol) or os.path.getsize(yol) < LOG_MAKSIMUM_BYTE:
            return False
        son_yedek = _log_yedek_yolu(yol, LOG_YEDEK_SAYISI)
        if os.path.exists(son_yedek):
            os.remove(son_yedek)
        for sira in range(LOG_YEDEK_SAYISI - 1, 0, -1):
            kaynak = _log_yedek_yolu(yol, sira)
            hedef = _log_yedek_yolu(yol, sira + 1)
            if os.path.exists(kaynak):
                os.rename(kaynak, hedef)
        os.rename(yol, _log_yedek_yolu(yol, 1))
        return True
    except Exception:
        return False


def gunluge_yaz(mesaj):
    zaman = time.strftime("%Y-%m-%d %H:%M:%S")
    satir = "[%s] %s" % (zaman, mesaj)
    print(satir, file=sys.stderr)
    try:
        yol = log_dosya_yolu()
        klasor_olustur(os.path.dirname(yol))
        log_dosyasini_dondur(yol)
        with open(yol, "a", encoding="utf-8") as dosya:
            dosya.write(satir + "\n")
    except Exception:
        pass


def loglari_oku(limit=300):
    yol = log_dosya_yolu()
    if not os.path.isfile(yol):
        return []
    try:
        with open(yol, "r", encoding="utf-8", errors="replace") as dosya:
            satirlar = dosya.readlines()[-limit:]
        return [satir.rstrip("\n") for satir in satirlar]
    except Exception as hata:
        return ["Log dosyasi okunamadi: %s" % hata]


def log_dosya_bilgisi():
    yol = log_dosya_yolu()
    yedekler = []
    for sira in range(1, LOG_YEDEK_SAYISI + 1):
        yedek_yol = _log_yedek_yolu(yol, sira)
        if os.path.isfile(yedek_yol):
            yedekler.append({
                "ad": os.path.basename(yedek_yol),
                "yol": yedek_yol,
                "boyut": os.path.getsize(yedek_yol),
            })
    bilgi = {
        "yol": yol,
        "var": os.path.isfile(yol),
        "boyut": 0,
        "boyut_kb": "0.0",
        "son_guncelleme": "-",
        "maksimum_mb": int(LOG_MAKSIMUM_BYTE / 1024 / 1024),
        "yedekler": yedekler,
    }
    if bilgi["var"]:
        bilgi["boyut"] = os.path.getsize(yol)
        bilgi["boyut_kb"] = "%.1f" % (float(bilgi["boyut"]) / 1024.0)
        bilgi["son_guncelleme"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(yol)))
    return bilgi


def loglari_temizle():
    yol = log_dosya_yolu()
    silinen = 0
    for aday in [yol] + [_log_yedek_yolu(yol, sira) for sira in range(1, LOG_YEDEK_SAYISI + 1)]:
        try:
            if os.path.isfile(aday):
                os.remove(aday)
                silinen += 1
        except Exception:
            pass
    return silinen
