# -*- coding: utf-8 -*-
import json
import re
import threading
import time
import urllib.error
import urllib.request

from . import __version__
from .config import (
    GITHUB_DOWNLOADS_URL,
    GITHUB_LATEST_INSTALLER_URL,
    GITHUB_UPDATE_MANIFEST_URL,
)

SURUM_DESENI = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
SHA256_DESENI = re.compile(r"^[0-9a-f]{64}$")
GUNCELLEME_ONBELLEK_SANIYE = 15 * 60
GUNCELLEME_HATA_ONBELLEK_SANIYE = 60
MAKSIMUM_CEVAP_BYTE = 16 * 1024
_ONBELLEK_KILIDI = threading.Lock()
_ONBELLEK = {"zaman": 0.0, "sonuc": None}


def surum_parcala(surum):
    eslesme = SURUM_DESENI.match(str(surum or "").strip())
    if not eslesme:
        return None
    return tuple(int(parca) for parca in eslesme.groups())


def daha_yeni_surum_var(guncel_surum, son_surum):
    guncel = surum_parcala(guncel_surum)
    son = surum_parcala(son_surum)
    if guncel is None or son is None:
        return False
    return son > guncel


def guncelleme_onbellegini_temizle():
    with _ONBELLEK_KILIDI:
        _ONBELLEK["zaman"] = 0.0
        _ONBELLEK["sonuc"] = None


def _hata_sonucu(mesaj, paket_yok=False):
    return {
        "ok": False,
        "guncel_surum": __version__,
        "son_surum": None,
        "guncelleme_var": False,
        "paket_yok": paket_yok,
        "kurulum_url": GITHUB_LATEST_INSTALLER_URL,
        "surumler_url": GITHUB_DOWNLOADS_URL,
        "sha256": "",
        "mesaj": mesaj,
    }


def _github_manifestini_oku(timeout):
    istek = urllib.request.Request(
        GITHUB_UPDATE_MANIFEST_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "Kantar-Servisi/%s" % __version__,
        },
    )
    try:
        with urllib.request.urlopen(istek, timeout=timeout) as cevap:
            ham_cevap = cevap.read(MAKSIMUM_CEVAP_BYTE + 1)
            if len(ham_cevap) > MAKSIMUM_CEVAP_BYTE:
                raise ValueError("Guncelleme manifesti beklenen boyutu asti.")
            manifest = json.loads(ham_cevap.decode("utf-8"))
    except urllib.error.HTTPError as hata:
        if hata.code == 404:
            return _hata_sonucu("GitHub deposunda henuz yerel Windows paketi bulunmuyor.", paket_yok=True)
        return _hata_sonucu("GitHub guncelleme bilgisi alinamadi: %s" % hata)
    except (urllib.error.URLError, OSError, ValueError) as hata:
        return _hata_sonucu("GitHub guncelleme bilgisi alinamadi: %s" % hata)

    if not isinstance(manifest, dict):
        raise ValueError("GitHub guncelleme manifesti gecersiz.")
    son_surum = str(manifest.get("version") or "").lstrip("v")
    if surum_parcala(son_surum) is None:
        return _hata_sonucu("GitHub guncelleme manifestindeki surum gecersiz.")
    if manifest.get("installer") != "Kantar-Servisi-Setup.exe":
        return _hata_sonucu("GitHub guncelleme manifestindeki kurulum dosyasi gecersiz.")
    sha256 = str(manifest.get("sha256") or "").strip().lower()
    if not SHA256_DESENI.match(sha256):
        return _hata_sonucu("GitHub guncelleme manifestindeki SHA256 degeri gecersiz.")
    return {
        "ok": True,
        "guncel_surum": __version__,
        "son_surum": son_surum,
        "guncelleme_var": daha_yeni_surum_var(__version__, son_surum),
        "paket_yok": False,
        "kurulum_url": GITHUB_LATEST_INSTALLER_URL,
        "surumler_url": GITHUB_DOWNLOADS_URL,
        "yayin_tarihi": manifest.get("published_at") or "",
        "sha256": sha256,
        "mesaj": "",
    }


def son_surumu_kontrol_et(timeout=4, zorla=False):
    simdi = time.monotonic()
    with _ONBELLEK_KILIDI:
        sonuc = _ONBELLEK["sonuc"]
        if sonuc is not None and not zorla:
            sure = GUNCELLEME_ONBELLEK_SANIYE if sonuc.get("ok") else GUNCELLEME_HATA_ONBELLEK_SANIYE
            if simdi - _ONBELLEK["zaman"] < sure:
                return dict(sonuc)

    try:
        sonuc = _github_manifestini_oku(timeout)
    except (OSError, TypeError, ValueError) as hata:
        sonuc = _hata_sonucu("GitHub guncelleme bilgisi alinamadi: %s" % hata)

    with _ONBELLEK_KILIDI:
        _ONBELLEK["zaman"] = time.monotonic()
        _ONBELLEK["sonuc"] = dict(sonuc)
    return sonuc
