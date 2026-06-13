import sqlite3

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


def test_yeni_veritabani_bos_kantar_listesiyle_baslar(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))

    assert storage.kantarlari_listele() == []
    assert storage.ayarlari_oku()["_kantar_yok"] is True


def test_birden_fazla_kantar_eklenebilir_ve_silinebilir(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))

    giris = storage.kantar_ekle("Giris Kantari")
    cikis = storage.kantar_ekle("Cikis Kantari")

    assert [kantar["ad"] for kantar in storage.kantarlari_listele()] == [
        "Giris Kantari",
        "Cikis Kantari",
    ]
    assert storage.ayarlari_oku(giris)["_kantar_adi"] == "Giris Kantari"
    assert storage.ayarlari_oku(cikis)["_kantar_adi"] == "Cikis Kantari"
    assert storage.kantar_sil(giris) is True
    assert [kantar["id"] for kantar in storage.kantarlari_listele()] == [cikis]


def test_gecersiz_acik_secim_ilk_kantara_dusmez(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    storage.kantar_ekle("Giris Kantari")

    assert storage.kantar_sec("kantar-gecersiz") is None
    assert storage.ayarlari_oku("kantar-gecersiz")["_kantar_yok"] is True


def test_kantar_adlari_benzersizdir(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    storage.kantar_ekle("Giris Kantari")

    with pytest.raises(ValueError, match="zaten var"):
        storage.kantar_ekle("giris kantari")


def test_cakisan_ad_ayar_kaydini_kismen_uygulamaz(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    giris = storage.kantar_ekle("Giris")
    storage.kantar_ekle("Cikis")
    ayarlar = dict(VARSAYILAN_AYARLAR, seri_port="COM7")

    with pytest.raises(ValueError, match="zaten var"):
        storage.ayarlari_kaydet(giris, ayarlar, "Cikis")

    assert storage.ayarlari_oku(giris)["_kantar_adi"] == "Giris"
    assert storage.ayarlari_oku(giris)["seri_port"] == "COM2"


def test_servis_ayarlari_kantarlar_arasinda_ortaktir(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    giris = storage.kantar_ekle("Giris")
    cikis = storage.kantar_ekle("Cikis")
    ayarlar = dict(VARSAYILAN_AYARLAR)
    ayarlar.update({"seri_port": "COM7", "servis_port": "8090"})

    storage.ayarlari_kaydet(giris, ayarlar)

    giris_ayarlari = storage.ayarlari_oku(giris)
    cikis_ayarlari = storage.ayarlari_oku(cikis)
    assert giris_ayarlari["seri_port"] == "COM7"
    assert cikis_ayarlari["seri_port"] == "COM2"
    assert giris_ayarlari["servis_port"] == "8090"
    assert cikis_ayarlari["servis_port"] == "8090"


def test_gecersiz_ayar_veritabanina_yazilmaz(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    kantar_id = storage.kantar_ekle("Kantar")
    ayarlar = dict(VARSAYILAN_AYARLAR)
    ayarlar["seri_baud_hizi"] = "0"

    with pytest.raises(AyarDogrulamaHatasi):
        storage.ayarlari_kaydet(kantar_id, ayarlar, "Yeni Kantar Adi")

    assert storage.ayarlari_oku(kantar_id)["seri_baud_hizi"] == "9600"
    assert storage.ayarlari_oku(kantar_id)["_kantar_adi"] == "Kantar"


def test_ozellestirilmis_eski_profil_dinamik_kantara_tasinir(monkeypatch, tmp_path):
    db_yolu = tmp_path / "ayarlar.sqlite"
    monkeypatch.setenv("KANTAR_AYAR_DB", str(db_yolu))
    baglanti = sqlite3.connect(str(db_yolu))
    baglanti.execute(
        "CREATE TABLE kantar_ayarlar (profil TEXT, anahtar TEXT, deger TEXT, PRIMARY KEY (profil, anahtar))"
    )
    for anahtar, deger in storage.ESKI_VARSAYILANLAR["kantar1"].items():
        baglanti.execute(
            "INSERT INTO kantar_ayarlar VALUES (?, ?, ?)",
            ("kantar1", anahtar, "COM8" if anahtar == "seri_port" else deger),
        )
    for anahtar, deger in storage.ESKI_VARSAYILANLAR["kantar2"].items():
        baglanti.execute("INSERT INTO kantar_ayarlar VALUES (?, ?, ?)", ("kantar2", anahtar, deger))
    baglanti.commit()
    baglanti.close()

    kantarlar = storage.kantarlari_listele()

    assert [kantar["ad"] for kantar in kantarlar] == ["Kantar 1"]
    assert storage.ayarlari_oku(kantarlar[0]["id"])["seri_port"] == "COM8"
    assert storage.kantar_sec("kantar1")["id"] == kantarlar[0]["id"]

    monkeypatch.setenv("KANTAR_AYAR_PROFILI", "kantar1")
    assert storage.kantar_sec()["id"] == kantarlar[0]["id"]
