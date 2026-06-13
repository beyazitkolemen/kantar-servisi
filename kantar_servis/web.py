# -*- coding: cp1254 -*-
import json
import hmac
import ipaddress
import re
import secrets
import time

try:
    from flask import Flask, Response, redirect, request, render_template
except ImportError:
    Flask = None
    Response = None
    redirect = None
    request = None
    render_template = None

try:
    from waitress import serve as waitress_serve
except ImportError:
    waitress_serve = None

from . import __version__
from .config import (
    AYAR_ALANLARI,
    AYAR_GIRIS_OZELLIKLERI,
    GITHUB_REPO_URL,
    PROFILLER,
    STATIC_KLASOR,
    TEMPLATE_KLASOR,
    log_dosya_yolu,
    profil_normalize,
    secili_profil,
    servis_hostu,
    servis_portu,
    uygulama_veri_dizini,
    yerel_servis_url,
)
from .errors import AyarDogrulamaHatasi, KantarHatasi
from .logging_utils import gunluge_yaz, log_dosya_bilgisi, loglari_oku, loglari_temizle
from .serial_bridge import kantar_degerini_oku, serial_ham_veri_oku, seri_port_bilgileri, seri_port_secenekleri, seri_portlari_listele
from .storage import ayarlari_baslat, ayarlari_kaydet, ayarlari_oku, sqlite_durumu_oku
from .updates import son_surumu_kontrol_et

CSRF_TOKEN = secrets.token_urlsafe(32)
LISDEP_ORIGIN_DESENI = re.compile(r"^https://(?:[a-z0-9-]+\.)*lisdep\.com(?::\d+)?$", re.IGNORECASE)


def create_app():
    if Flask is None:
        return None
    flask_app = Flask(
        __name__,
        template_folder=TEMPLATE_KLASOR,
        static_folder=STATIC_KLASOR,
        static_url_path="/static",
    )
    register_security(flask_app)
    register_routes(flask_app)
    return flask_app


app = None


def istek_profili():
    if request is None:
        return secili_profil()
    return profil_normalize(request.values.get("profil"), secili_profil())


def serial_port_parametresi():
    if request is None:
        return ""
    return str(request.values.get("port", "") or "").strip()


def metin_cevabi(metin, durum=200, mimetype="text/plain"):
    if Response is None:
        return metin
    return Response(metin, status=durum, mimetype=mimetype)


def html_cevabi(html, durum=200):
    return metin_cevabi(html, durum, "text/html")


def json_cevabi(veri, durum=200):
    metin = json.dumps(veri, ensure_ascii=False)
    return metin_cevabi(metin, durum, "application/json")


def istemci_yerel_mi(adres):
    if not adres:
        return True
    try:
        return ipaddress.ip_address(adres).is_loopback
    except ValueError:
        return False


def origin_izinli_mi(origin):
    origin = str(origin or "").strip()
    if not origin:
        return False
    if origin_lisdep_mi(origin):
        return True
    return bool(re.match(r"^https?://(?:127\.0\.0\.1|localhost|\[::1\])(?::\d+)?$", origin, re.IGNORECASE))


def origin_lisdep_mi(origin):
    return bool(LISDEP_ORIGIN_DESENI.match(str(origin or "").strip()))


def csrf_gecerli_mi():
    if request is None:
        return False
    token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token") or ""
    return hmac.compare_digest(str(token), CSRF_TOKEN)


def register_security(flask_app):
    @flask_app.before_request
    def yalnizca_yerel_istemci():
        if not istemci_yerel_mi(request.remote_addr):
            return json_cevabi({"ok": False, "hata": "Bu servis yalnizca yerel bilgisayardan kullanilabilir."}, 403)
        origin = request.headers.get("Origin", "")
        capraz_site = request.headers.get("Sec-Fetch-Site", "").lower() == "cross-site"
        if (origin or capraz_site) and not origin_izinli_mi(origin):
            return json_cevabi({"ok": False, "hata": "Bu web kaynaginin yerel servise erisim izni yok."}, 403)
        if capraz_site and origin_lisdep_mi(origin) and request.path not in ("/", "/api/v1/agirlik"):
            return json_cevabi({"ok": False, "hata": "Bu endpoint web entegrasyonuna acik degil."}, 403)
        return None

    @flask_app.after_request
    def guvenlik_basliklari(cevap):
        cevap.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        cevap.headers["X-Content-Type-Options"] = "nosniff"
        cevap.headers["X-Frame-Options"] = "DENY"
        cevap.headers["Referrer-Policy"] = "no-referrer"
        cevap.headers["Cache-Control"] = "no-store"

        if request.path in ("/", "/api/v1/agirlik"):
            cevap.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
            origin = request.headers.get("Origin", "")
            if origin_izinli_mi(origin):
                cevap.headers["Access-Control-Allow-Origin"] = origin
                cevap.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                cevap.headers["Access-Control-Allow-Headers"] = "Content-Type"
                if request.headers.get("Access-Control-Request-Private-Network") == "true":
                    cevap.headers["Access-Control-Allow-Private-Network"] = "true"
                cevap.headers["Vary"] = "Origin"
        else:
            cevap.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return cevap


def dosya_indirme_cevabi(metin, dosya_adi):
    if Response is None:
        return metin
    cevap = Response(metin, status=200, mimetype="text/plain; charset=utf-8")
    cevap.headers["Content-Disposition"] = "attachment; filename=%s" % dosya_adi
    return cevap


def ortak_template_context(aktif_sayfa, profil=None):
    if profil is None:
        profil = secili_profil()
    ayarlar = ayarlari_oku(profil)
    return {
        "aktif_sayfa": aktif_sayfa,
        "profil": profil,
        "profiller": PROFILLER,
        "csrf_token": CSRF_TOKEN,
        "servis_url": yerel_servis_url(ayarlar),
        "input_class": "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100",
        "label_class": "block text-sm font-semibold text-slate-700",
    }


def ayar_formu_alanlari(ayarlar, portlar):
    alanlar = []
    for anahtar, label, tip in AYAR_ALANLARI:
        deger = str(ayarlar.get(anahtar, "") or "")
        alanlar.append({
            "anahtar": anahtar,
            "label": label,
            "tip": tip,
            "deger": deger,
            "seri_port": anahtar == "seri_port",
            "global_ayar": anahtar in ("servis_host", "servis_port"),
            "ozellikler": AYAR_GIRIS_OZELLIKLERI.get(anahtar, {}),
            "secenekler": seri_port_secenekleri(deger, portlar) if anahtar == "seri_port" else [],
        })
    return alanlar


def sorun_giderme_maddeleri():
    return [
        {"baslik": "COM port listede gorunmuyor", "aciklama": "USB/RS232 donusturucuyu tekrar takin, Windows Aygit Yoneticisi'nde portu kontrol edin ve surucu kurulumunun tamamlandigindan emin olun."},
        {"baslik": "Port kullanimda hatasi", "aciklama": "Ayni COM portu kullanan diger kantar programlarini kapatin. Gerekirse servisi kapatip tekrar baslatin."},
        {"baslik": "SQLite ayari kaydedilemiyor", "aciklama": "Sistem sayfasindaki yerel veri klasorunun yazilabilir oldugunu kontrol edin ve uygulamayi yeniden baslatin."},
        {"baslik": "Ayarlar sayfasi acilmiyor", "aciklama": "Kantar servisi calisiyor mu kontrol edin. Tek servis adresi http://127.0.0.1/ayarlar seklindedir; Kantar 2 icin port degil ?profil=kantar2 parametresi kullanilir."},
        {"baslik": "Program dosyasi eksik", "aciklama": "GitHub deposundaki downloads klasorunden son Windows kurulum dosyasini indirip uygulamayi yeniden kurun. Ayarlariniz korunur."},
    ]


def ayar_formu_html(profil, ayarlar, mesaj=None, hatalar=None):
    if render_template is None:
        return "Kantar ayarlari sayfasi icin Flask render_template kullanilamadi. Flask paketini kontrol edin."
    portlar = seri_portlari_listele()
    context = ortak_template_context("ayarlar", profil)
    context.update({
        "mesaj": mesaj,
        "hatalar": hatalar or [],
        "alanlar": ayar_formu_alanlari(ayarlar, portlar),
        "portlar": seri_port_bilgileri(portlar),
        "sqlite_durumu": sqlite_durumu_oku(),
        "sorun_giderme": sorun_giderme_maddeleri(),
    })
    return render_template("kantar-ayarlar.html", **context)


def form_ayarlari_al(form):
    ayarlar = {}
    for anahtar, _label, _tip in AYAR_ALANLARI:
        deger = form.get(anahtar, "")
        if deger is None:
            deger = ""
        ayarlar[anahtar] = str(deger).strip()
    return ayarlar


def register_routes(flask_app):
    if flask_app is None:
        return

    def agirlik_oku():
        profil = istek_profili()
        try:
            return {"ok": True, "profil": profil, "agirlik": kantar_degerini_oku(profil)}, 200
        except KantarHatasi as hata:
            mesaj = hata.kullanici_mesaji()
            gunluge_yaz(mesaj)
            return {"ok": False, "profil": profil, "hata": mesaj}, 503
        except Exception as hata:
            mesaj = KantarHatasi("Beklenmeyen bir hata olustu.", [
                "Servis loglarini kontrol edin.",
                "Kantar Servisi uygulamasini yeniden baslatin.",
            ], str(hata)).kullanici_mesaji()
            gunluge_yaz(mesaj)
            return {"ok": False, "profil": profil, "hata": mesaj}, 500

    @flask_app.route("/", methods=["GET", "OPTIONS"])
    def kantar_degeri():
        if request.method == "OPTIONS":
            return metin_cevabi("", 204)
        sonuc, durum = agirlik_oku()
        return metin_cevabi(sonuc.get("agirlik") if sonuc["ok"] else sonuc["hata"], durum)

    @flask_app.route("/api/v1/agirlik", methods=["GET", "OPTIONS"])
    def agirlik_api():
        if request.method == "OPTIONS":
            return metin_cevabi("", 204)
        sonuc, durum = agirlik_oku()
        sonuc["zaman"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        return json_cevabi(sonuc, durum)

    @flask_app.route("/saglik")
    def saglik():
        return json_cevabi({
            "ok": True,
            "uygulama": "Kantar Servisi",
            "durum": "hazir",
            "surum": __version__,
            "profil": istek_profili(),
        })

    @flask_app.route("/ayarlar", methods=["GET", "POST"])
    def ayarlar_sayfasi():
        profil = istek_profili()
        mesaj = None
        if request.method == "POST":
            if not csrf_gecerli_mi():
                return html_cevabi(
                    ayar_formu_html(profil, form_ayarlari_al(request.form), hatalar=["Form guvenlik dogrulamasi basarisiz. Sayfayi yenileyip tekrar deneyin."]),
                    403,
                )
            form_ayarlari = form_ayarlari_al(request.form)
            try:
                ayarlari_kaydet(profil, form_ayarlari)
            except AyarDogrulamaHatasi as hata:
                return html_cevabi(ayar_formu_html(profil, form_ayarlari, hatalar=hata.hatalar), 400)
            mesaj = "Ayarlar kaydedildi. Servis host veya port degistiyse servisi yeniden baslatin."
        return html_cevabi(ayar_formu_html(profil, ayarlari_oku(profil), mesaj))

    @flask_app.route("/serial")
    def serial_sayfasi():
        profil = istek_profili()
        portlar = seri_portlari_listele()
        secili_port = serial_port_parametresi() or ayarlari_oku(profil).get("seri_port", "COM2")
        context = ortak_template_context("serial", profil)
        context.update({
            "portlar": seri_port_bilgileri(portlar),
            "port_secenekleri": seri_port_secenekleri(secili_port, portlar),
            "secili_port": secili_port,
        })
        return html_cevabi(render_template("serial.html", **context))

    @flask_app.route("/serial/veri")
    def serial_veri():
        profil = istek_profili()
        try:
            return json_cevabi(serial_ham_veri_oku(profil, serial_port_parametresi()))
        except KantarHatasi as hata:
            gunluge_yaz(hata.kullanici_mesaji())
            return json_cevabi({"ok": False, "hata": hata.kullanici_mesaji(), "zaman": time.strftime("%H:%M:%S")}, 500)
        except Exception as hata:
            mesaj = "Serial veri okunamadi: %s" % hata
            gunluge_yaz(mesaj)
            return json_cevabi({"ok": False, "hata": mesaj, "zaman": time.strftime("%H:%M:%S")}, 500)

    @flask_app.route("/serial/portlar")
    def serial_portlar():
        profil = istek_profili()
        secili_port = serial_port_parametresi() or ayarlari_oku(profil).get("seri_port", "COM2")
        portlar = seri_portlari_listele()
        return json_cevabi({
            "ok": True,
            "profil": profil,
            "secili_port": secili_port,
            "portlar": seri_port_bilgileri(portlar),
            "port_secenekleri": seri_port_secenekleri(secili_port, portlar),
            "zaman": time.strftime("%H:%M:%S"),
        })

    @flask_app.route("/loglar")
    def loglar_sayfasi():
        context = ortak_template_context("loglar", istek_profili())
        context.update({
            "loglar": loglari_oku(),
            "log_dosya_yolu": log_dosya_yolu(),
            "log_bilgisi": log_dosya_bilgisi(),
            "mesaj": request.values.get("mesaj", "") if request is not None else "",
        })
        return html_cevabi(render_template("loglar.html", **context))

    @flask_app.route("/loglar/veri")
    def loglar_veri():
        return json_cevabi({
            "ok": True,
            "loglar": loglari_oku(),
            "log_dosya_yolu": log_dosya_yolu(),
            "log_bilgisi": log_dosya_bilgisi(),
            "zaman": time.strftime("%H:%M:%S"),
        })

    @flask_app.route("/loglar/indir")
    def loglar_indir():
        import os

        yol = log_dosya_yolu()
        if not os.path.isfile(yol):
            return metin_cevabi("Log dosyasi bulunamadi.", 404)
        with open(yol, "r", encoding="utf-8", errors="replace") as dosya:
            return dosya_indirme_cevabi(dosya.read(), "kantar-servis.log")

    @flask_app.route("/loglar/temizle", methods=["POST"])
    def loglar_temizle():
        if not csrf_gecerli_mi():
            return json_cevabi({"ok": False, "hata": "Form guvenlik dogrulamasi basarisiz."}, 403)
        silinen = loglari_temizle()
        gunluge_yaz("Log temizleme islemi tamamlandi. Silinen dosya sayisi: %s" % silinen)
        if redirect is None:
            return json_cevabi({"ok": True, "silinen": silinen})
        return redirect("/loglar?profil=%s&mesaj=Loglar temizlendi" % istek_profili())

    @flask_app.route("/sistem")
    def sistem_sayfasi():
        context = ortak_template_context("sistem", istek_profili())
        context.update({
            "guncelleme": son_surumu_kontrol_et(zorla=request.args.get("yenile") == "1"),
            "github_repo_url": GITHUB_REPO_URL,
            "veri_dizini": uygulama_veri_dizini(),
        })
        return html_cevabi(render_template("sistem.html", **context))


app = create_app()


def calistir():
    ayarlari_baslat()
    if app is None:
        gunluge_yaz(
            "Kantar hatasi: Flask paketi kurulu degil.\n"
            "Kontrol edilecekler:\n"
            "- Komut satirinda pip install flask pyserial calistirin.\n"
            "- Betigi calistiran Python ortami ile kurulum yaptiginiz Python ortaminin ayni oldugunu kontrol edin.\n"
        )
        return 1
    ayarlar = ayarlari_oku()
    servis_host = servis_hostu(ayarlar)
    servis_port = servis_portu(ayarlar)
    try:
        if waitress_serve is not None:
            gunluge_yaz("Waitress WSGI sunucusu baslatiliyor: %s:%s" % (servis_host, servis_port))
            waitress_serve(app, host=servis_host, port=servis_port)
        else:
            gunluge_yaz("Waitress bulunamadi; Flask gelistirme sunucusu ile devam ediliyor.")
            app.run(host=servis_host, port=servis_port)
    except Exception as hata:
        gunluge_yaz(
            "Kantar hatasi: Flask servisi baslatilamadi.\n"
            "Kontrol edilecekler:\n"
            "- 127.0.0.1/ayarlar sayfasindan servis host ve port ayarlarini kontrol edin.\n"
            "- KANTAR_SERVIS_PORT baska bir program tarafindan kullaniliyor olabilir.\n"
            "- 80 portu icin yonetici yetkisi gerekebilir; gerekirse 8090 gibi bir port deneyin.\n"
            "Teknik detay: %s\n" % hata
        )
        return 1
    return 0
