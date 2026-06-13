# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

from . import __version__
from .config import GITHUB_RELEASES_URL, log_dosya_yolu, yerel_servis_url
from .logging_utils import gunluge_yaz
from .storage import ayarlari_baslat, ayarlari_oku

MUTEX_ADI = "Local\\KantarServisi"
ERROR_ALREADY_EXISTS = 183
CREATE_NO_WINDOW = 0x08000000


def mesaj_goster(baslik, mesaj, hata=False):
    if os.name == "nt":
        import ctypes
        ikon = 0x10 if hata else 0x40
        ctypes.windll.user32.MessageBoxW(None, str(mesaj), str(baslik), ikon)
        return
    print("%s: %s" % (baslik, mesaj), file=sys.stderr)


def tek_ornek_kilidi_al():
    if os.name != "nt":
        return object()
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_ADI)
    if not handle:
        return None
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle


def tek_ornek_kilidini_birak(handle):
    if os.name != "nt" or not handle:
        return
    import ctypes
    ctypes.windll.kernel32.CloseHandle(handle)


def sunucu_komutu():
    if getattr(sys, "frozen", False):
        return [sys.executable, "--server"]
    return [sys.executable, "-m", "kantar_servis", "--server"]


def tray_ikonu_olustur():
    from PIL import Image, ImageDraw

    resim = Image.new("RGBA", (64, 64), (15, 23, 42, 0))
    cizim = ImageDraw.Draw(resim)
    cizim.rounded_rectangle((4, 4, 60, 60), radius=13, fill=(37, 99, 235, 255))
    cizim.rounded_rectangle((13, 14, 51, 27), radius=4, fill=(239, 246, 255, 255))
    cizim.rectangle((18, 32, 46, 48), fill=(255, 255, 255, 255))
    cizim.rectangle((23, 36, 27, 44), fill=(37, 99, 235, 255))
    cizim.rectangle((30, 33, 34, 44), fill=(37, 99, 235, 255))
    cizim.rectangle((37, 38, 41, 44), fill=(37, 99, 235, 255))
    return resim


class MasaustuUygulamasi:
    def __init__(self, kilit, tarayici_ac=True):
        self.kilit = kilit
        self.tarayici_ac = tarayici_ac
        self.sunucu = None
        self.ikon = None

    def servis_url(self):
        return yerel_servis_url(ayarlari_oku())

    def servis_hazir_mi(self, timeout=20):
        son = time.time() + timeout
        saglik_url = self.servis_url() + "/saglik"
        while time.time() < son:
            if self.sunucu is not None and self.sunucu.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(saglik_url, timeout=1) as cevap:
                    if cevap.status == 200:
                        return True
            except (urllib.error.URLError, OSError):
                time.sleep(0.25)
        return False

    def sunucuyu_baslat(self):
        ayarlari_baslat()
        olusturma_bayraklari = CREATE_NO_WINDOW if os.name == "nt" else 0
        self.sunucu = subprocess.Popen(
            sunucu_komutu(),
            cwd=os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else None,
            creationflags=olusturma_bayraklari,
        )
        if self.servis_hazir_mi():
            gunluge_yaz("Masaustu uygulamasi servisi hazir: %s" % self.servis_url())
            return True
        kod = self.sunucu.poll()
        self.sunucuyu_durdur()
        gunluge_yaz("Masaustu uygulamasi servisi baslatamadi. Cikis kodu: %s" % kod)
        return False

    def sunucuyu_durdur(self):
        if self.sunucu is None or self.sunucu.poll() is not None:
            self.sunucu = None
            return
        self.sunucu.terminate()
        try:
            self.sunucu.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.sunucu.kill()
            self.sunucu.wait(timeout=2)
        self.sunucu = None

    def paneli_ac(self, _ikon=None, _menu=None):
        webbrowser.open(self.servis_url() + "/ayarlar")

    def log_klasorunu_ac(self, _ikon=None, _menu=None):
        klasor = os.path.dirname(log_dosya_yolu())
        os.makedirs(klasor, exist_ok=True)
        if os.name == "nt":
            os.startfile(klasor)
        else:
            webbrowser.open("file://" + klasor)

    def surumleri_ac(self, _ikon=None, _menu=None):
        webbrowser.open(GITHUB_RELEASES_URL)

    def sunucuyu_yeniden_baslat(self, _ikon=None, _menu=None):
        self.sunucuyu_durdur()
        if not self.sunucuyu_baslat():
            mesaj_goster(
                "Kantar Servisi",
                "Servis yeniden baslatilamadi. Port ayarini ve log dosyasini kontrol edin.",
                hata=True,
            )

    def cikis(self, ikon=None, _menu=None):
        self.sunucuyu_durdur()
        tek_ornek_kilidini_birak(self.kilit)
        self.kilit = None
        if ikon is not None:
            ikon.stop()

    def calistir(self):
        try:
            import pystray
        except ImportError:
            mesaj_goster("Kantar Servisi", "Sistem tepsisi bileseni yuklu degil.", hata=True)
            self.cikis()
            return 1

        if not self.sunucuyu_baslat():
            mesaj_goster(
                "Kantar Servisi baslatilamadi",
                "Servis portu baska bir program tarafindan kullaniliyor olabilir. "
                "Log dosyasini kontrol edin: %s" % log_dosya_yolu(),
                hata=True,
            )
            self.cikis()
            return 1

        menu = pystray.Menu(
            pystray.MenuItem("Yonetim Panelini Ac", self.paneli_ac, default=True),
            pystray.MenuItem("Servisi Yeniden Baslat", self.sunucuyu_yeniden_baslat),
            pystray.MenuItem("Log Klasorunu Ac", self.log_klasorunu_ac),
            pystray.MenuItem("GitHub Surumleri", self.surumleri_ac),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cikis", self.cikis),
        )
        self.ikon = pystray.Icon(
            "KantarServisi",
            tray_ikonu_olustur(),
            "Kantar Servisi v%s" % __version__,
            menu,
        )
        if self.tarayici_ac:
            self.paneli_ac()
        try:
            self.ikon.run()
        finally:
            self.cikis()
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="Kantar Servisi")
    parser.add_argument("--server", action="store_true", help="Yalnizca HTTP servisini calistirir.")
    parser.add_argument("--minimized", action="store_true", help="Paneli otomatik acmadan sistem tepsisinde baslatir.")
    parser.add_argument("--version", action="store_true", help="Surum bilgisini gosterir.")
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if args.server or os.name != "nt":
        from .web import calistir
        calistir()
        return 0

    ayarlari_baslat()
    kilit = tek_ornek_kilidi_al()
    if kilit is None:
        webbrowser.open(yerel_servis_url(ayarlari_oku()) + "/ayarlar")
        return 0
    return MasaustuUygulamasi(kilit, tarayici_ac=not args.minimized).calistir()


if __name__ == "__main__":
    sys.exit(main())
