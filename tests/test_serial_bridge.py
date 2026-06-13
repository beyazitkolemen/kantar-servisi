import pytest

from kantar_servis.errors import KantarHatasi
from kantar_servis.serial_bridge import agirlik_degerini_ayikla


AYARLAR = {
    "_profil": "tekli",
    "baslangic_bitleri": "A,@",
    "agirlik_baslangic_indeksi": "3",
    "agirlik_bitis_indeksi": "10",
}


def test_agirlik_degerini_ayiklar(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "test.log"))

    assert agirlik_degerini_ayikla("A  00125 ", AYARLAR) == "125"


def test_gecersiz_baslangic_biti_hata_verir(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "test.log"))

    with pytest.raises(KantarHatasi, match="beklenen baslangic"):
        agirlik_degerini_ayikla("X  00125 ", AYARLAR)
