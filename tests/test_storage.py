from kantar_servis import storage


def test_eski_ayar_veritabanini_yeni_konuma_tasir(monkeypatch, tmp_path):
    kaynak = tmp_path / "legacy.sqlite"
    hedef = tmp_path / "new" / "kantar-ayarlar.sqlite"
    kaynak.write_bytes(b"legacy-settings")
    monkeypatch.setenv("KANTAR_AYAR_DB", str(hedef))
    monkeypatch.setattr(storage, "eski_ayar_db_yolu", lambda: str(kaynak))

    assert storage.eski_ayarlari_tasi() is True
    assert hedef.read_bytes() == b"legacy-settings"
    assert storage.eski_ayarlari_tasi() is False
