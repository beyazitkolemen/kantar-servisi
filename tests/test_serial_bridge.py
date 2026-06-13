import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from kantar_servis import serial_bridge
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


def test_negatif_agirlik_degerini_ayiklar(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "test.log"))

    assert agirlik_degerini_ayikla("A  -12.5 ", AYARLAR) == "-12.5"


def test_ayni_porttaki_eszamanli_okumalar_siraya_alinir(monkeypatch):
    durum = {"aktif": 0, "maksimum": 0}
    durum_kilidi = threading.Lock()

    class SahteSerialBaglantisi:
        def __init__(self, *_args, **_kwargs):
            with durum_kilidi:
                durum["aktif"] += 1
                durum["maksimum"] = max(durum["maksimum"], durum["aktif"])

        def readline(self, _boyut):
            time.sleep(0.03)
            return b"A  00125 "

        def close(self):
            with durum_kilidi:
                durum["aktif"] -= 1

    class SahteSerialModulu:
        Serial = SahteSerialBaglantisi

    monkeypatch.setattr(serial_bridge, "serial", SahteSerialModulu())
    ayarlar = {
        "seri_port": "COM9",
        "seri_baud_hizi": "9600",
        "seri_zaman_asimi": "1",
        "seri_okuma_boyutu": "10",
    }

    with ThreadPoolExecutor(max_workers=2) as havuz:
        sonuclar = list(havuz.map(lambda _sira: serial_bridge.seri_baglantidan_oku(ayarlar), range(2)))

    assert sonuclar == [b"A  00125 ", b"A  00125 "]
    assert durum["maksimum"] == 1
