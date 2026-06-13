# -*- coding: utf-8 -*-
import argparse
import json
import os
import platform
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from . import __version__
from .config import (
    GITHUB_DOWNLOADS_URL,
    UYGULAMA_ADI,
    ayar_db_yolu,
    log_dosya_yolu,
    uygulama_veri_dizini,
    yerel_servis_url,
)
from .logging_utils import gunluge_yaz
from .serial_bridge import seri_portlari_listele
from .storage import ayarlari_baslat, ayarlari_oku, kantarlari_listele

MUTEX_ADI = "Local\\KantarServisi"
ERROR_ALREADY_EXISTS = 183
CREATE_NO_WINDOW = 0x08000000
SERVIS_BASLATMA_ZAMAN_ASIMI = 20
SERVIS_GOZETIM_ARALIGI = 3
SERVIS_OTOMATIK_BASLATMA_BEKLEMESI = 2
DURUM_BASLATILIYOR = "Baslatiliyor"
DURUM_CALISIYOR = "Calisiyor"
DURUM_YENIDEN_BASLATILIYOR = "Yeniden baslatiliyor"
DURUM_DURDU = "Durduruldu"
DURUM_HATA = "Kontrol gerekli"


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


def servis_saglik_bilgisi(servis_url, timeout=1):
    saglik_url = servis_url.rstrip("/") + "/saglik"
    istek = urllib.request.Request(
        saglik_url,
        headers={"Accept": "application/json", "Cache-Control": "no-store"},
    )
    try:
        with urllib.request.urlopen(istek, timeout=timeout) as cevap:
            ham_veri = cevap.read(65537)
            if cevap.status != 200 or len(ham_veri) > 65536:
                return None
            veri = json.loads(ham_veri.decode("utf-8"))
    except (urllib.error.URLError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(veri, dict):
        return None
    if veri.get("ok") is not True or veri.get("uygulama") != UYGULAMA_ADI or veri.get("durum") != "hazir":
        return None
    return veri


def tanilama_raporu_olustur():
    ayarlari_baslat()
    veri_dizini = uygulama_veri_dizini()
    os.makedirs(veri_dizini, exist_ok=True)
    rapor_yolu = os.path.join(veri_dizini, "kantar-servisi-tanilama.txt")
    servis_url = yerel_servis_url(ayarlari_oku())
    saglik = servis_saglik_bilgisi(servis_url)
    portlar = seri_portlari_listele()
    satirlar = [
        "%s Tanilama Raporu" % UYGULAMA_ADI,
        "=" * 48,
        "Olusturma zamani: %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
        "Uygulama surumu: %s" % __version__,
        "Isletim sistemi: %s" % platform.platform(),
        "Python: %s" % platform.python_version(),
        "Paketlenmis uygulama: %s" % ("Evet" if getattr(sys, "frozen", False) else "Hayir"),
        "Calistirilabilir dosya: %s" % sys.executable,
        "Servis adresi: %s" % servis_url,
        "Servis sagligi: %s" % ("Hazir" if saglik else "Erisilemiyor"),
        "Veri dizini: %s" % veri_dizini,
        "Ayar veritabani: %s" % ayar_db_yolu(),
        "Log dosyasi: %s" % log_dosya_yolu(),
        "",
        "Seri Portlar",
        "-" * 48,
    ]
    if portlar:
        satirlar.extend("%s | %s" % (cihaz, aciklama) for cihaz, aciklama in portlar)
    else:
        satirlar.append("Seri port bulunamadi.")

    satirlar.extend(["", "Kantar Ayarlari", "-" * 48])
    kantarlar = kantarlari_listele()
    if not kantarlar:
        satirlar.append("Henuz kantar eklenmedi.")
    for kantar in kantarlar:
        ayarlar = ayarlari_oku(kantar["id"])
        satirlar.append("[%s | %s]" % (kantar["ad"], kantar["id"]))
        for anahtar in (
            "seri_port",
            "seri_baud_hizi",
            "seri_zaman_asimi",
            "seri_okuma_boyutu",
            "baslangic_bitleri",
            "agirlik_baslangic_indeksi",
            "agirlik_bitis_indeksi",
        ):
            satirlar.append("%s=%s" % (anahtar, ayarlar.get(anahtar, "")))
        satirlar.append("")
    with open(rapor_yolu, "w", encoding="utf-8") as dosya:
        dosya.write("\n".join(satirlar).rstrip() + "\n")
    return rapor_yolu


def yerel_dosyayi_ac(yol):
    if os.name == "nt":
        os.startfile(yol)
    else:
        webbrowser.open(Path(yol).resolve().as_uri())


class MasaustuUygulamasi:
    def __init__(self, kilit, tarayici_ac=True):
        self.kilit = kilit
        self.tarayici_ac = tarayici_ac
        self.sunucu = None
        self.ikon = None
        self.durum = DURUM_BASLATILIYOR
        self._yasam_dongusu_kilidi = threading.RLock()
        self._kapanis = threading.Event()
        self._yeniden_baslatiliyor = threading.Event()
        self._gozetim_thread = None

    def servis_url(self):
        return yerel_servis_url(ayarlari_oku())

    def durum_metni(self, _menu_item=None):
        return "Servis durumu: %s" % self.durum

    def durum_guncelle(self, durum):
        self.durum = durum
        if self.ikon is not None:
            try:
                self.ikon.title = "%s v%s - %s" % (UYGULAMA_ADI, __version__, durum)
                self.ikon.update_menu()
            except Exception:
                pass

    def bildirim_goster(self, mesaj, baslik=UYGULAMA_ADI):
        if self.ikon is None:
            return
        try:
            self.ikon.notify(mesaj, baslik)
        except Exception:
            pass

    def servis_hazir_mi(self, timeout=SERVIS_BASLATMA_ZAMAN_ASIMI):
        son = time.monotonic() + timeout
        servis_url = self.servis_url()
        while time.monotonic() < son:
            if self.sunucu is not None and self.sunucu.poll() is not None:
                return False
            if servis_saglik_bilgisi(servis_url) is not None:
                return True
            time.sleep(0.25)
        return False

    def sunucuyu_baslat(self):
        with self._yasam_dongusu_kilidi:
            if self._kapanis.is_set():
                return False
            if self.sunucu is not None and self.sunucu.poll() is None:
                return True
            self.durum_guncelle(DURUM_BASLATILIYOR)
            ayarlari_baslat()
            olusturma_bayraklari = CREATE_NO_WINDOW if os.name == "nt" else 0
            popen_ayarlari = {
                "cwd": os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else None,
                "creationflags": olusturma_bayraklari,
            }
            if getattr(sys, "frozen", False):
                popen_ayarlari["stdin"] = subprocess.DEVNULL
                popen_ayarlari["stdout"] = subprocess.DEVNULL
                popen_ayarlari["stderr"] = subprocess.DEVNULL
            try:
                self.sunucu = subprocess.Popen(sunucu_komutu(), **popen_ayarlari)
            except (OSError, subprocess.SubprocessError) as hata:
                self.sunucu = None
                self.durum_guncelle(DURUM_HATA)
                gunluge_yaz("Masaustu uygulamasi servis surecini baslatamadi: %s" % hata)
                return False
            if self.servis_hazir_mi():
                self.durum_guncelle(DURUM_CALISIYOR)
                gunluge_yaz("Masaustu uygulamasi servisi hazir: %s" % self.servis_url())
                return True
            kod = self.sunucu.poll()
            self.sunucuyu_durdur()
            self.durum_guncelle(DURUM_HATA)
            gunluge_yaz("Masaustu uygulamasi servisi baslatamadi. Cikis kodu: %s" % kod)
            return False

    def sunucuyu_durdur(self):
        with self._yasam_dongusu_kilidi:
            if self.sunucu is None or self.sunucu.poll() is not None:
                self.sunucu = None
                if not self._yeniden_baslatiliyor.is_set():
                    self.durum_guncelle(DURUM_DURDU)
                return
            self.sunucu.terminate()
            try:
                self.sunucu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sunucu.kill()
                self.sunucu.wait(timeout=2)
            self.sunucu = None
            if not self._yeniden_baslatiliyor.is_set():
                self.durum_guncelle(DURUM_DURDU)

    def sayfayi_ac(self, yol):
        if servis_saglik_bilgisi(self.servis_url()) is None:
            mesaj_goster(
                UYGULAMA_ADI,
                "Yerel servis su anda erisilebilir degil. Sistem tepsisi menusunden servisi yeniden baslatin.",
                hata=True,
            )
            return False
        webbrowser.open_new_tab(self.servis_url() + yol)
        return True

    def paneli_ac(self, _ikon=None, _menu=None):
        return self.sayfayi_ac("/ayarlar")

    def serial_ekranini_ac(self, _ikon=None, _menu=None):
        return self.sayfayi_ac("/serial")

    def log_ekranini_ac(self, _ikon=None, _menu=None):
        return self.sayfayi_ac("/loglar")

    def sistem_ekranini_ac(self, _ikon=None, _menu=None):
        return self.sayfayi_ac("/sistem")

    def log_klasorunu_ac(self, _ikon=None, _menu=None):
        klasor = os.path.dirname(log_dosya_yolu())
        os.makedirs(klasor, exist_ok=True)
        yerel_dosyayi_ac(klasor)

    def indirmeleri_ac(self, _ikon=None, _menu=None):
        webbrowser.open_new_tab(GITHUB_DOWNLOADS_URL)

    def tanilama_raporunu_ac(self, _ikon=None, _menu=None):
        try:
            rapor_yolu = tanilama_raporu_olustur()
            yerel_dosyayi_ac(rapor_yolu)
        except Exception as hata:
            gunluge_yaz("Tanilama raporu olusturulamadi: %s" % hata)
            mesaj_goster(UYGULAMA_ADI, "Tanilama raporu olusturulamadi. Log dosyasini kontrol edin.", hata=True)

    def sunucuyu_yeniden_baslat(self, _ikon=None, _menu=None):
        if self._kapanis.is_set() or self._yeniden_baslatiliyor.is_set():
            return
        self._yeniden_baslatiliyor.set()

        def yeniden_baslat():
            self.durum_guncelle(DURUM_YENIDEN_BASLATILIYOR)
            try:
                self.sunucuyu_durdur()
                if self._kapanis.is_set():
                    return
                if self.sunucuyu_baslat():
                    self.bildirim_goster("Yerel kantar servisi yeniden baslatildi.")
                else:
                    self.bildirim_goster("Servis yeniden baslatilamadi. Loglari kontrol edin.")
                    mesaj_goster(
                        UYGULAMA_ADI,
                        "Servis yeniden baslatilamadi. Port ayarini ve log dosyasini kontrol edin.",
                        hata=True,
                    )
            finally:
                self._yeniden_baslatiliyor.clear()

        threading.Thread(target=yeniden_baslat, name="KantarServisiYenidenBaslat", daemon=True).start()

    def gozetimi_baslat(self):
        if self._gozetim_thread is not None and self._gozetim_thread.is_alive():
            return

        def gozet():
            while not self._kapanis.wait(SERVIS_GOZETIM_ARALIGI):
                if self._yeniden_baslatiliyor.is_set():
                    continue
                with self._yasam_dongusu_kilidi:
                    surec = self.sunucu
                    durdu = surec is not None and surec.poll() is not None
                    cikis_kodu = surec.poll() if durdu else None
                    if durdu:
                        self.sunucu = None
                if not durdu:
                    continue
                self.durum_guncelle(DURUM_HATA)
                gunluge_yaz("Servis beklenmedik sekilde durdu. Cikis kodu: %s" % cikis_kodu)
                self.bildirim_goster("Yerel servis beklenmedik sekilde durdu; yeniden baslatiliyor.")
                if self._kapanis.wait(SERVIS_OTOMATIK_BASLATMA_BEKLEMESI):
                    return
                if self.sunucuyu_baslat():
                    self.bildirim_goster("Yerel kantar servisi otomatik olarak yeniden baslatildi.")
                else:
                    self.bildirim_goster("Yerel servis otomatik baslatilamadi. Loglari kontrol edin.")

        self._gozetim_thread = threading.Thread(target=gozet, name="KantarServisiGozetim", daemon=True)
        self._gozetim_thread.start()

    def cikis(self, ikon=None, _menu=None):
        self._kapanis.set()
        self.sunucuyu_durdur()
        tek_ornek_kilidini_birak(self.kilit)
        self.kilit = None
        hedef_ikon = ikon or self.ikon
        if hedef_ikon is not None:
            try:
                hedef_ikon.stop()
            except Exception:
                pass

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
            pystray.MenuItem(self.durum_metni, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Yonetim Panelini Ac", self.paneli_ac, default=True),
            pystray.MenuItem("Serial Izleme", self.serial_ekranini_ac),
            pystray.MenuItem("Loglari Goruntule", self.log_ekranini_ac),
            pystray.MenuItem("Sistem ve Guncelleme", self.sistem_ekranini_ac),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Servisi Yeniden Baslat", self.sunucuyu_yeniden_baslat),
            pystray.MenuItem("Log Klasorunu Ac", self.log_klasorunu_ac),
            pystray.MenuItem("Tanilama Raporu Olustur", self.tanilama_raporunu_ac),
            pystray.MenuItem("GitHub Indirme Dosyalari", self.indirmeleri_ac),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cikis", self.cikis),
        )
        self.ikon = pystray.Icon(
            "KantarServisi",
            tray_ikonu_olustur(),
            "Kantar Servisi v%s" % __version__,
            menu,
        )
        self.durum_guncelle(DURUM_CALISIYOR)
        self.gozetimi_baslat()
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
    parser.add_argument("--open-panel", action="store_true", help="Calisan servisin yonetim panelini acar.")
    parser.add_argument("--open-logs", action="store_true", help="Yerel log klasorunu acar.")
    parser.add_argument("--diagnostics", action="store_true", help="Tanilama raporu olusturur ve acar.")
    parser.add_argument("--health-check", action="store_true", help="Calisan yerel servisin sagligini denetler.")
    parser.add_argument("--version", action="store_true", help="Surum bilgisini gosterir.")
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0
    if args.open_logs:
        klasor = os.path.dirname(log_dosya_yolu())
        os.makedirs(klasor, exist_ok=True)
        yerel_dosyayi_ac(klasor)
        return 0
    if args.diagnostics:
        rapor_yolu = tanilama_raporu_olustur()
        yerel_dosyayi_ac(rapor_yolu)
        return 0
    if args.health_check:
        return 0 if servis_saglik_bilgisi(yerel_servis_url(ayarlari_oku()), timeout=2) else 1
    if args.server or os.name != "nt":
        from .web import calistir
        return calistir()

    ayarlari_baslat()
    kilit = tek_ornek_kilidi_al()
    if kilit is None:
        uygulama = MasaustuUygulamasi(None)
        return 0 if uygulama.paneli_ac() else 1
    if args.open_panel:
        return MasaustuUygulamasi(kilit, tarayici_ac=True).calistir()
    return MasaustuUygulamasi(kilit, tarayici_ac=not args.minimized).calistir()


if __name__ == "__main__":
    sys.exit(main())
