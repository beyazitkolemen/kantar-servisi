from kantar_servis import web


def test_saglik_ve_yonetim_sayfalari(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_VERI_DIZINI", str(tmp_path))
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    monkeypatch.setattr(
        web,
        "son_surumu_kontrol_et",
        lambda: {
            "ok": True,
            "guncel_surum": "1.0.0",
            "son_surum": "1.0.0",
            "guncelleme_var": False,
            "kurulum_url": "https://example.test/setup.exe",
            "surumler_url": "https://example.test/releases",
            "yayin_tarihi": "",
            "mesaj": "",
        },
    )
    istemci = web.app.test_client()

    saglik = istemci.get("/saglik")
    ayarlar = istemci.get("/ayarlar")
    sistem = istemci.get("/sistem")
    css = istemci.get("/static/app.css")

    assert saglik.status_code == 200
    assert saglik.get_json()["surum"] == "1.0.0"
    assert ayarlar.status_code == 200
    assert "Ayarlar" in ayarlar.get_data(as_text=True)
    assert sistem.status_code == 200
    assert "Windows Kurulumunu Indir" in sistem.get_data(as_text=True)
    assert css.status_code == 200


def test_template_javascript_satir_sonlari_gecerli():
    serial_html = (web.TEMPLATE_KLASOR + "/serial.html")
    log_html = (web.TEMPLATE_KLASOR + "/loglar.html")

    with open(serial_html, "r", encoding="utf-8") as dosya:
        serial_icerik = dosya.read()
    with open(log_html, "r", encoding="utf-8") as dosya:
        log_icerik = dosya.read()

    assert "satirlar.join('\\\\n')" not in serial_icerik
    assert "satirlar.join('\\n')" in serial_icerik
    assert "replace(/\\n/g, ' ')" in serial_icerik
    assert "join('\\n')" in log_icerik
