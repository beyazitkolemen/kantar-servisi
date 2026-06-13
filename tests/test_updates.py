import io
import json
import urllib.error

from kantar_servis import updates


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def setup_function():
    updates.guncelleme_onbellegini_temizle()


def test_surum_karsilastirma():
    assert updates.daha_yeni_surum_var("1.0.0", "v1.1.0") is True
    assert updates.daha_yeni_surum_var("1.2.0", "v1.1.9") is False
    assert updates.daha_yeni_surum_var("dev", "v1.1.0") is False


def test_github_manifest_bilgisi(monkeypatch):
    veri = {
        "version": "1.2.0",
        "published_at": "2026-06-13",
        "installer": "Kantar-Servisi-Setup.exe",
        "sha256": "a" * 64,
    }
    monkeypatch.setattr(
        updates.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(json.dumps(veri).encode("utf-8")),
    )

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is True
    assert sonuc["son_surum"] == "1.2.0"
    assert sonuc["guncelleme_var"] is True
    assert sonuc["kurulum_url"].endswith("/main/downloads/Kantar-Servisi-Setup.exe")
    assert sonuc["sha256"] == "a" * 64


def test_github_hatasi_kurulum_baglantisini_korur(monkeypatch):
    def hata_ver(_request, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(updates.urllib.request, "urlopen", hata_ver)

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is False
    assert sonuc["guncelleme_var"] is False
    assert sonuc["kurulum_url"].endswith("/main/downloads/Kantar-Servisi-Setup.exe")


def test_henuz_paket_yoksa_anlasilir_durum_doner(monkeypatch):
    def paket_yok(_request, timeout):
        raise urllib.error.HTTPError("https://example.test", 404, "Not Found", {}, None)

    monkeypatch.setattr(updates.urllib.request, "urlopen", paket_yok)

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is False
    assert sonuc["paket_yok"] is True
    assert "yerel Windows paketi" in sonuc["mesaj"]


def test_github_manifest_sonucu_onbellekten_doner(monkeypatch):
    cagri_sayisi = {"deger": 0}
    veri = {
        "version": "1.0.0",
        "installer": "Kantar-Servisi-Setup.exe",
        "sha256": "b" * 64,
    }

    def cevap_ver(_request, timeout):
        cagri_sayisi["deger"] += 1
        return FakeResponse(json.dumps(veri).encode("utf-8"))

    monkeypatch.setattr(updates.urllib.request, "urlopen", cevap_ver)

    updates.son_surumu_kontrol_et()
    updates.son_surumu_kontrol_et()
    updates.son_surumu_kontrol_et(zorla=True)

    assert cagri_sayisi["deger"] == 2


def test_bozuk_manifest_sistem_sayfasini_dusurmez(monkeypatch):
    veri = {
        "version": "1.0.0",
        "installer": "baska-dosya.exe",
        "sha256": "gecersiz",
    }
    monkeypatch.setattr(
        updates.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(json.dumps(veri).encode("utf-8")),
    )

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is False
    assert sonuc["kurulum_url"].endswith("/main/downloads/Kantar-Servisi-Setup.exe")


def test_manifest_keyfi_indirme_adresi_belirleyemez(monkeypatch):
    veri = {
        "version": "1.1.0",
        "installer": "Kantar-Servisi-Setup.exe",
        "installer_url": "https://example.test/zararli.exe",
        "sha256": "c" * 64,
    }
    monkeypatch.setattr(
        updates.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(json.dumps(veri).encode("utf-8")),
    )

    sonuc = updates.son_surumu_kontrol_et()

    assert "raw.githubusercontent.com/beyazitkolemen/kantar-servisi" in sonuc["kurulum_url"]
    assert "example.test" not in sonuc["kurulum_url"]
