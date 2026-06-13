from kantar_servis import web


def test_saglik_ve_yonetim_sayfalari(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_VERI_DIZINI", str(tmp_path))
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    monkeypatch.setattr(
        web,
        "son_surumu_kontrol_et",
        lambda **_kwargs: {
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
    assert ayarlar.headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in ayarlar.headers["Content-Security-Policy"]


def test_javascript_harici_dosyalardan_yuklenir():
    serial_html = (web.TEMPLATE_KLASOR + "/serial.html")
    log_html = (web.TEMPLATE_KLASOR + "/loglar.html")
    serial_js = web.STATIC_KLASOR + "/serial.js"
    log_js = web.STATIC_KLASOR + "/loglar.js"

    with open(serial_html, "r", encoding="utf-8") as dosya:
        serial_icerik = dosya.read()
    with open(log_html, "r", encoding="utf-8") as dosya:
        log_icerik = dosya.read()
    with open(serial_js, "r", encoding="utf-8") as dosya:
        serial_script = dosya.read()
    with open(log_js, "r", encoding="utf-8") as dosya:
        log_script = dosya.read()

    assert "serial.js" in serial_icerik
    assert "loglar.js" in log_icerik
    assert "<script>" not in serial_icerik
    assert "onsubmit=" not in log_icerik
    assert 'satirlar.join("\\n")' in serial_script
    assert 'replace(/\\n/g, " ")' in serial_script
    assert 'join("\\n")' in log_script


def test_ayar_formu_csrf_ve_dogrulama_korumali(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    istemci = web.app.test_client()
    gecerli = {
        "profil": "tekli",
        "seri_port": "COM7",
        "seri_baud_hizi": "9600",
        "seri_zaman_asimi": "3",
        "seri_okuma_boyutu": "8",
        "baslangic_bitleri": "A,@",
        "agirlik_baslangic_indeksi": "3",
        "agirlik_bitis_indeksi": "10",
        "servis_host": "127.0.0.1",
        "servis_port": "8090",
    }

    csrf_yok = istemci.post("/ayarlar", data=gecerli)
    assert csrf_yok.status_code == 403

    gecersiz = dict(gecerli, _csrf_token=web.CSRF_TOKEN, servis_port="70000")
    hata = istemci.post("/ayarlar", data=gecersiz)
    assert hata.status_code == 400
    assert "65535" in hata.get_data(as_text=True)

    basarili = istemci.post("/ayarlar", data=dict(gecerli, _csrf_token=web.CSRF_TOKEN))
    assert basarili.status_code == 200
    assert "Ayarlar kaydedildi" in basarili.get_data(as_text=True)


def test_agirlik_api_json_ve_cors_doner(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    monkeypatch.setattr(web, "kantar_degerini_oku", lambda profil: "125")
    istemci = web.app.test_client()

    cevap = istemci.get(
        "/api/v1/agirlik?profil=kantar1",
        headers={
            "Origin": "https://demo.lisdep.com",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert cevap.status_code == 200
    assert cevap.get_json()["agirlik"] == "125"
    assert cevap.get_json()["profil"] == "kantar1"
    assert cevap.headers["Access-Control-Allow-Origin"] == "https://demo.lisdep.com"
    assert cevap.headers["Access-Control-Allow-Private-Network"] == "true"


def test_uzak_istemci_reddedilir():
    istemci = web.app.test_client()

    cevap = istemci.get("/saglik", environ_base={"REMOTE_ADDR": "192.168.1.20"})

    assert cevap.status_code == 403


def test_izinsiz_web_origin_reddedilir():
    istemci = web.app.test_client()

    cevap = istemci.get(
        "/saglik",
        headers={"Origin": "https://example.test", "Sec-Fetch-Site": "cross-site"},
    )

    assert cevap.status_code == 403


def test_lisdep_origini_yalnizca_agirlik_endpointlerine_erisebilir():
    istemci = web.app.test_client()

    cevap = istemci.get(
        "/loglar/veri",
        headers={"Origin": "https://demo.lisdep.com", "Sec-Fetch-Site": "cross-site"},
    )

    assert cevap.status_code == 403
