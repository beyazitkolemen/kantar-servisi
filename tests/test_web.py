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
            "paket_yok": False,
            "kurulum_url": "https://example.test/setup.exe",
            "surumler_url": "https://example.test/downloads",
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
    assert saglik.get_json()["surum"] == "1.1.0"
    assert ayarlar.status_code == 200
    assert "Henüz kantar eklenmedi" in ayarlar.get_data(as_text=True)
    assert saglik.get_json()["kantar_sayisi"] == 0
    assert sistem.status_code == 200
    assert "Windows Kurulumunu İndir" in sistem.get_data(as_text=True)
    assert css.status_code == 200
    assert ayarlar.headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in ayarlar.headers["Content-Security-Policy"]


def test_javascript_harici_dosyalardan_yuklenir():
    serial_html = (web.TEMPLATE_KLASOR + "/serial.html")
    log_html = (web.TEMPLATE_KLASOR + "/loglar.html")
    ayarlar_html = (web.TEMPLATE_KLASOR + "/kantar-ayarlar.html")
    serial_js = web.STATIC_KLASOR + "/serial.js"
    log_js = web.STATIC_KLASOR + "/loglar.js"
    kantarlar_js = web.STATIC_KLASOR + "/kantarlar.js"

    with open(serial_html, "r", encoding="utf-8") as dosya:
        serial_icerik = dosya.read()
    with open(log_html, "r", encoding="utf-8") as dosya:
        log_icerik = dosya.read()
    with open(ayarlar_html, "r", encoding="utf-8") as dosya:
        ayarlar_icerik = dosya.read()
    with open(serial_js, "r", encoding="utf-8") as dosya:
        serial_script = dosya.read()
    with open(log_js, "r", encoding="utf-8") as dosya:
        log_script = dosya.read()
    with open(kantarlar_js, "r", encoding="utf-8") as dosya:
        kantarlar_script = dosya.read()

    assert "serial.js" in serial_icerik
    assert "loglar.js" in log_icerik
    assert "kantarlar.js" in ayarlar_icerik
    assert "<script>" not in serial_icerik
    assert "onsubmit=" not in log_icerik
    assert 'satirlar.join("\\n")' in serial_script
    assert 'replace(/\\n/g, " ")' in serial_script
    assert 'join("\\n")' in log_script
    assert "window.confirm" in kantarlar_script


def test_ayar_formu_csrf_ve_dogrulama_korumali(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    kantar_id = web.kantar_ekle("Giris Kantari")
    istemci = web.app.test_client()
    gecerli = {
        "kantar": kantar_id,
        "kantar_adi": "Giris Kantari",
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

    csrf_yok = istemci.post("/ayarlar?kantar=%s" % kantar_id, data=gecerli)
    assert csrf_yok.status_code == 403

    gecersiz = dict(gecerli, _csrf_token=web.CSRF_TOKEN, servis_port="70000")
    hata = istemci.post("/ayarlar?kantar=%s" % kantar_id, data=gecersiz)
    assert hata.status_code == 400
    assert "65535" in hata.get_data(as_text=True)

    basarili = istemci.post(
        "/ayarlar?kantar=%s" % kantar_id,
        data=dict(gecerli, _csrf_token=web.CSRF_TOKEN),
    )
    assert basarili.status_code == 200
    assert "Ayarlar kaydedildi" in basarili.get_data(as_text=True)


def test_agirlik_api_json_ve_cors_doner(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    kantar_id = web.kantar_ekle("Giris Kantari")
    monkeypatch.setattr(web, "kantar_degerini_oku", lambda kantar_id: "125")
    istemci = web.app.test_client()

    cevap = istemci.get(
        "/api/v1/agirlik?kantar=%s" % kantar_id,
        headers={
            "Origin": "https://demo.lisdep.com",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert cevap.status_code == 200
    assert cevap.get_json()["agirlik"] == "125"
    assert cevap.get_json()["kantar"] == kantar_id
    assert cevap.get_json()["kantar_adi"] == "Giris Kantari"
    assert cevap.headers["Access-Control-Allow-Origin"] == "https://demo.lisdep.com"
    assert cevap.headers["Access-Control-Allow-Private-Network"] == "true"


def test_kantar_ekleme_listeleme_ve_silme_akisi(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    monkeypatch.setenv("KANTAR_LOG_DOSYA", str(tmp_path / "servis.log"))
    istemci = web.app.test_client()

    ilk = istemci.post(
        "/kantarlar/ekle",
        data={"_csrf_token": web.CSRF_TOKEN, "kantar_adi": "Giris Kantari"},
    )
    ikinci = istemci.post(
        "/kantarlar/ekle",
        data={"_csrf_token": web.CSRF_TOKEN, "kantar_adi": "Cikis Kantari"},
    )

    assert ilk.status_code == 302
    assert ikinci.status_code == 302
    liste = istemci.get("/api/v1/kantarlar").get_json()["kantarlar"]
    assert [kantar["ad"] for kantar in liste] == ["Giris Kantari", "Cikis Kantari"]

    sil = istemci.post(
        "/kantarlar/%s/sil" % liste[0]["id"],
        data={"_csrf_token": web.CSRF_TOKEN},
    )
    assert sil.status_code == 302
    assert [kantar["ad"] for kantar in istemci.get("/api/v1/kantarlar").get_json()["kantarlar"]] == [
        "Cikis Kantari"
    ]


def test_kantar_yokken_agirlik_endpointi_acik_hata_doner(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    istemci = web.app.test_client()

    cevap = istemci.get("/api/v1/agirlik")

    assert cevap.status_code == 409
    assert "Henüz kantar eklenmedi" in cevap.get_json()["hata"]


def test_gecersiz_kantar_kimligi_baska_kantari_okumaz(monkeypatch, tmp_path):
    monkeypatch.setenv("KANTAR_AYAR_DB", str(tmp_path / "ayarlar.sqlite"))
    web.kantar_ekle("Giris Kantari")
    monkeypatch.setattr(
        web,
        "kantar_degerini_oku",
        lambda _kantar_id: (_ for _ in ()).throw(AssertionError("Okuma yapilmamali")),
    )
    istemci = web.app.test_client()

    cevap = istemci.get("/api/v1/agirlik?kantar=kantar-gecersiz")

    assert cevap.status_code == 404
    assert cevap.get_json()["kantar"] is None
    assert cevap.get_json()["hata"] == "İstenen kantar bulunamadı."

    ayarlar = istemci.get("/ayarlar?kantar=kantar-gecersiz")
    assert ayarlar.status_code == 200
    assert "İstenen kantar bulunamadı." in ayarlar.get_data(as_text=True)
    assert "Bir kantar seçin" in ayarlar.get_data(as_text=True)


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
