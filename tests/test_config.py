from kantar_servis import config


def test_veri_dizini_environment_override(monkeypatch, tmp_path):
    hedef = tmp_path / "kantar-data"
    monkeypatch.setenv("KANTAR_VERI_DIZINI", str(hedef))

    assert config.uygulama_veri_dizini() == str(hedef)
    assert config.ayar_db_yolu() == str(hedef / "kantar-ayarlar.sqlite")
    assert config.log_dosya_yolu() == str(hedef / "kantar-servis.log")


def test_yerel_servis_url_environment_port_override(monkeypatch):
    monkeypatch.setenv("KANTAR_SERVIS_HOST", "0.0.0.0")
    monkeypatch.setenv("KANTAR_SERVIS_PORT", "18080")

    assert config.yerel_servis_url({"servis_host": "127.0.0.1", "servis_port": "80"}) == "http://127.0.0.1:18080"


def test_yerel_servis_url_default_portu_gizler(monkeypatch):
    monkeypatch.delenv("KANTAR_SERVIS_HOST", raising=False)
    monkeypatch.delenv("KANTAR_SERVIS_PORT", raising=False)

    assert config.yerel_servis_url({"servis_host": "127.0.0.1", "servis_port": "80"}) == "http://127.0.0.1"
