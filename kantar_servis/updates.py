# -*- coding: utf-8 -*-
import json
import re
import urllib.error
import urllib.request

from . import __version__
from .config import GITHUB_LATEST_INSTALLER_URL, GITHUB_RELEASES_URL, GITHUB_REPO

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/%s/releases/latest" % GITHUB_REPO
SURUM_DESENI = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


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


def _kurulum_adresi(release):
    for asset in release.get("assets") or []:
        if asset.get("name") == "Kantar-Servisi-Setup.exe":
            return asset.get("browser_download_url") or GITHUB_LATEST_INSTALLER_URL
    return GITHUB_LATEST_INSTALLER_URL


def son_surumu_kontrol_et(timeout=4):
    istek = urllib.request.Request(
        GITHUB_LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Kantar-Servisi/%s" % __version__,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(istek, timeout=timeout) as cevap:
            release = json.loads(cevap.read().decode("utf-8"))
    except urllib.error.HTTPError as hata:
        release_yok = hata.code == 404
        return {
            "ok": False,
            "guncel_surum": __version__,
            "son_surum": None,
            "guncelleme_var": False,
            "release_yok": release_yok,
            "kurulum_url": GITHUB_LATEST_INSTALLER_URL,
            "surumler_url": GITHUB_RELEASES_URL,
            "mesaj": (
                "Henuz GitHub uzerinde kararli bir surum yayinlanmadi."
                if release_yok
                else "GitHub surum bilgisi alinamadi: %s" % hata
            ),
        }
    except (urllib.error.URLError, OSError, ValueError) as hata:
        return {
            "ok": False,
            "guncel_surum": __version__,
            "son_surum": None,
            "guncelleme_var": False,
            "release_yok": False,
            "kurulum_url": GITHUB_LATEST_INSTALLER_URL,
            "surumler_url": GITHUB_RELEASES_URL,
            "mesaj": "GitHub surum bilgisi alinamadi: %s" % hata,
        }

    son_surum = str(release.get("tag_name") or "").lstrip("v")
    return {
        "ok": True,
        "guncel_surum": __version__,
        "son_surum": son_surum,
        "guncelleme_var": daha_yeni_surum_var(__version__, son_surum),
        "release_yok": False,
        "kurulum_url": _kurulum_adresi(release),
        "surumler_url": release.get("html_url") or GITHUB_RELEASES_URL,
        "yayin_tarihi": release.get("published_at") or "",
        "mesaj": "",
    }
