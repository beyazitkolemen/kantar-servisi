import io
import json
import urllib.error

from kantar_servis import updates


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def test_surum_karsilastirma():
    assert updates.daha_yeni_surum_var("1.0.0", "v1.1.0") is True
    assert updates.daha_yeni_surum_var("1.2.0", "v1.1.9") is False
    assert updates.daha_yeni_surum_var("dev", "v1.1.0") is False


def test_github_surum_bilgisi(monkeypatch):
    veri = {
        "tag_name": "v1.2.0",
        "html_url": "https://github.com/beyazitkolemen/kantar-servisi/releases/tag/v1.2.0",
        "published_at": "2026-06-13T12:00:00Z",
        "assets": [
            {
                "name": "Kantar-Servisi-Setup.exe",
                "browser_download_url": "https://example.test/Kantar-Servisi-Setup.exe",
            }
        ],
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
    assert sonuc["kurulum_url"] == "https://example.test/Kantar-Servisi-Setup.exe"


def test_github_hatasi_kurulum_baglantisini_korur(monkeypatch):
    def hata_ver(_request, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(updates.urllib.request, "urlopen", hata_ver)

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is False
    assert sonuc["guncelleme_var"] is False
    assert sonuc["kurulum_url"].endswith("/releases/latest/download/Kantar-Servisi-Setup.exe")


def test_henuz_release_yoksa_anlasilir_durum_doner(monkeypatch):
    def release_yok(_request, timeout):
        raise urllib.error.HTTPError("https://example.test", 404, "Not Found", {}, None)

    monkeypatch.setattr(updates.urllib.request, "urlopen", release_yok)

    sonuc = updates.son_surumu_kontrol_et()

    assert sonuc["ok"] is False
    assert sonuc["release_yok"] is True
    assert "Henuz GitHub" in sonuc["mesaj"]
