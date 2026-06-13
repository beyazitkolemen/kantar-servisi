import io
import json
import threading
import time
import urllib.error

from kantar_servis import desktop


class FakeResponse(io.BytesIO):
    def __init__(self, veri, status=200):
        super().__init__(veri)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class FakeProcess:
    def __init__(self, kod=None):
        self.kod = kod
        self.terminate_cagrildi = False
        self.kill_cagrildi = False

    def poll(self):
        return self.kod

    def terminate(self):
        self.terminate_cagrildi = True
        self.kod = 0

    def wait(self, timeout=None):
        return self.kod

    def kill(self):
        self.kill_cagrildi = True
        self.kod = -9


class FakeIcon:
    def __init__(self):
        self.title = ""
        self.bildirimler = []
        self.menu_guncelleme = 0
        self.durdu = False

    def update_menu(self):
        self.menu_guncelleme += 1

    def notify(self, mesaj, baslik=None):
        self.bildirimler.append((baslik, mesaj))

    def stop(self):
        self.durdu = True


def test_servis_saglik_bilgisi_beklenen_uygulamayi_dogrular(monkeypatch):
    veri = {
        "ok": True,
        "uygulama": "Kantar Servisi",
        "durum": "hazir",
        "surum": "1.0.0",
    }
    monkeypatch.setattr(
        desktop.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(json.dumps(veri).encode("utf-8")),
    )

    sonuc = desktop.servis_saglik_bilgisi("http://127.0.0.1:18080")

    assert sonuc["surum"] == "1.0.0"


def test_servis_saglik_bilgisi_yanlis_uygulama_ve_ag_hatasini_reddeder(monkeypatch):
    yanlis = {"ok": True, "uygulama": "Baska Uygulama", "durum": "hazir"}
    monkeypatch.setattr(
        desktop.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(json.dumps(yanlis).encode("utf-8")),
    )
    assert desktop.servis_saglik_bilgisi("http://127.0.0.1") is None

    def ag_hatasi(_request, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(desktop.urllib.request, "urlopen", ag_hatasi)
    assert desktop.servis_saglik_bilgisi("http://127.0.0.1") is None


def test_tanilama_raporu_sistem_ve_kantar_bilgilerini_yazar(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_VERI_DIZINI", str(tmp_path))
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    monkeypatch.setattr(desktop, "servis_saglik_bilgisi", lambda _url: {"ok": True})
    monkeypatch.setattr(desktop, "seri_portlari_listele", lambda: [("COM7", "USB Serial")])
    monkeypatch.setattr(
        desktop,
        "kantarlari_listele",
        lambda: [{"id": "kantar-" + ("a" * 32), "ad": "Giris Kantari", "sira": 1}],
    )
    monkeypatch.setattr(
        desktop,
        "ayarlari_oku",
        lambda *_args: {
            "servis_host": "127.0.0.1",
            "servis_port": "80",
            "seri_port": "COM7",
            "seri_baud_hizi": "9600",
            "seri_zaman_asimi": "3",
            "seri_okuma_boyutu": "8",
            "baslangic_bitleri": "A,@",
            "agirlik_baslangic_indeksi": "3",
            "agirlik_bitis_indeksi": "10",
        },
    )

    rapor_yolu = desktop.tanilama_raporu_olustur()
    icerik = (tmp_path / "kantar-servisi-tanilama.txt").read_text(encoding="utf-8")

    assert rapor_yolu == str(tmp_path / "kantar-servisi-tanilama.txt")
    assert "Kantar Servisi Tanilama Raporu" in icerik
    assert "Servis sagligi: Hazir" in icerik
    assert "COM7 | USB Serial" in icerik
    assert "[Giris Kantari | kantar-" in icerik


def test_sunucu_baslatma_ve_durdurma_durumu_gunceller(monkeypatch):
    surec = FakeProcess()
    monkeypatch.setattr(desktop, "ayarlari_baslat", lambda: None)
    monkeypatch.setattr(desktop.subprocess, "Popen", lambda *_args, **_kwargs: surec)
    monkeypatch.setattr(desktop, "gunluge_yaz", lambda _mesaj: None)
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)
    monkeypatch.setattr(uygulama, "servis_hazir_mi", lambda timeout=20: True)

    assert uygulama.sunucuyu_baslat() is True
    assert uygulama.durum == desktop.DURUM_CALISIYOR
    assert uygulama.sunucu is surec

    uygulama.sunucuyu_durdur()

    assert surec.terminate_cagrildi is True
    assert uygulama.sunucu is None
    assert uygulama.durum == desktop.DURUM_DURDU


def test_sunucu_baslatma_hatasi_kullanici_durumuna_yansir(monkeypatch):
    monkeypatch.setattr(desktop, "ayarlari_baslat", lambda: None)
    monkeypatch.setattr(
        desktop.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("baslatilamadi")),
    )
    monkeypatch.setattr(desktop, "gunluge_yaz", lambda _mesaj: None)
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)

    assert uygulama.sunucuyu_baslat() is False
    assert uygulama.durum == desktop.DURUM_HATA
    assert uygulama.sunucu is None


def test_yeniden_baslatma_tepsi_callbackini_bloklamaz(monkeypatch):
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)
    uygulama.ikon = FakeIcon()
    tamamlandi = threading.Event()
    devam_et = threading.Event()
    cagrilar = []
    monkeypatch.setattr(uygulama, "sunucuyu_durdur", lambda: cagrilar.append("durdur"))

    def baslat():
        cagrilar.append("baslat")
        devam_et.wait(1)
        tamamlandi.set()
        return True

    monkeypatch.setattr(uygulama, "sunucuyu_baslat", baslat)
    baslangic = time.monotonic()

    uygulama.sunucuyu_yeniden_baslat()
    uygulama.sunucuyu_yeniden_baslat()

    assert time.monotonic() - baslangic < 0.2
    devam_et.set()
    assert tamamlandi.wait(1)
    assert cagrilar == ["durdur", "baslat"]
    assert any("yeniden baslatildi" in mesaj for _baslik, mesaj in uygulama.ikon.bildirimler)


def test_gozetim_beklenmedik_kapanmada_servisi_yeniden_baslatir(monkeypatch):
    monkeypatch.setattr(desktop, "SERVIS_GOZETIM_ARALIGI", 0.01)
    monkeypatch.setattr(desktop, "SERVIS_OTOMATIK_BASLATMA_BEKLEMESI", 0)
    monkeypatch.setattr(desktop, "gunluge_yaz", lambda _mesaj: None)
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)
    uygulama.ikon = FakeIcon()
    uygulama.sunucu = FakeProcess(kod=7)
    yeniden_basladi = threading.Event()

    def baslat():
        yeniden_basladi.set()
        uygulama._kapanis.set()
        return True

    monkeypatch.setattr(uygulama, "sunucuyu_baslat", baslat)
    uygulama.gozetimi_baslat()

    assert yeniden_basladi.wait(1)
    uygulama._gozetim_thread.join(timeout=1)
    assert any("beklenmedik" in mesaj for _baslik, mesaj in uygulama.ikon.bildirimler)


def test_kapanis_sinyalinden_sonra_yeni_servis_baslatilmaz(monkeypatch):
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)
    uygulama._kapanis.set()
    cagrildi = []
    monkeypatch.setattr(desktop.subprocess, "Popen", lambda *_args, **_kwargs: cagrildi.append(True))

    assert uygulama.sunucuyu_baslat() is False
    assert cagrildi == []


def test_sayfa_yalnizca_saglikli_serviste_acilir(monkeypatch):
    uygulama = desktop.MasaustuUygulamasi(object(), tarayici_ac=False)
    monkeypatch.setattr(uygulama, "servis_url", lambda: "http://127.0.0.1:18080")
    acilan = []
    monkeypatch.setattr(desktop.webbrowser, "open_new_tab", lambda url: acilan.append(url))
    monkeypatch.setattr(desktop, "servis_saglik_bilgisi", lambda _url: {"ok": True})

    assert uygulama.serial_ekranini_ac() is True
    assert acilan == ["http://127.0.0.1:18080/serial"]


def test_health_check_cli_cikis_kodu_doner(monkeypatch):
    monkeypatch.setattr(desktop, "ayarlari_oku", lambda: {"servis_host": "127.0.0.1", "servis_port": "80"})
    monkeypatch.setattr(desktop, "yerel_servis_url", lambda _ayarlar: "http://127.0.0.1")
    monkeypatch.setattr(desktop, "servis_saglik_bilgisi", lambda _url, timeout=2: {"ok": True})
    assert desktop.main(["--health-check"]) == 0

    monkeypatch.setattr(desktop, "servis_saglik_bilgisi", lambda _url, timeout=2: None)
    assert desktop.main(["--health-check"]) == 1
