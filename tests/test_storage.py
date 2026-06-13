import pytest

from kantar_servis import storage
from kantar_servis.config import VARSAYILAN_AYARLAR
from kantar_servis.errors import AyarDogrulamaHatasi


def test_eski_ayar_veritabanini_yeni_konuma_tasir(monkeypatch, tmp_path):
    kaynak = tmp_path / "legacy.sqlite"
    hedef = tmp_path / "new" / "kantar-ayarlar.sqlite"
    kaynak.write_bytes(b"legacy-settings")
    monkeypatch.setenv("KANTAR_AYAR_DB", str(hedef))
    monkeypatch.setattr(storage, "eski_ayar_db_yolu", lambda: str(kaynak))

    assert storage.eski_ayarlari_tasi() is True
    assert hedef.read_bytes() == b"legacy-settings"
    assert storage.eski_ayarlari_tasi() is False


def test_servis_ayarlari_profiller_arasinda_ortaktir(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    ayarlar = dict(VARSAYILAN_AYARLAR["tekli"])
    ayarlar.update({"seri_port": "COM7", "servis_port": "8090"})

    storage.ayarlari_kaydet("tekli", ayarlar)

    tekli = storage.ayarlari_oku("tekli")
    kantar2 = storage.ayarlari_oku("kantar2")
    assert tekli["seri_port"] == "COM7"
    assert kantar2["seri_port"] == "COM3"
    assert tekli["servis_port"] == "8090"
    assert kantar2["servis_port"] == "8090"


def test_gecersiz_ayar_veritabanina_yazilmaz(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    ayarlar = dict(VARSAYILAN_AYARLAR["tekli"])
    ayarlar["seri_baud_hizi"] = "0"

    with pytest.raises(AyarDogrulamaHatasi):
        storage.ayarlari_kaydet("tekli", ayarlar)

    assert storage.ayarlari_oku("tekli")["seri_baud_hizi"] == "9600"
