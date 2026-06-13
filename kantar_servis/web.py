# -*- coding: cp1254 -*-
import json
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

from .config import AYAR_ALANLARI, PROFILLER, TEMPLATE_KLASOR, ayar_int, profil_normalize, secili_profil
from .errors import KantarHatasi
from .logging_utils import gunluge_yaz, log_dosya_bilgisi, loglari_oku, loglari_temizle
from .config import log_dosya_yolu
from .serial_bridge import kantar_degerini_oku, serial_ham_veri_oku, seri_port_bilgileri, seri_port_secenekleri, seri_portlari_listele
from .storage import ayarlari_baslat, ayarlari_kaydet, ayarlari_oku, sqlite_durumu_oku

def create_app():
    if Flask is None:
        return None
    flask_app = Flask(__name__, template_folder=TEMPLATE_KLASOR)
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


def dosya_indirme_cevabi(metin, dosya_adi):
    if Response is None:
        return metin
    cevap = Response(metin, status=200, mimetype="text/plain; charset=utf-8")
    cevap.headers["Content-Disposition"] = "attachment; filename=%s" % dosya_adi
    return cevap


def ortak_template_context(aktif_sayfa, profil=None):
    if profil is None:
        profil = secili_profil()
    return {
        "aktif_sayfa": aktif_sayfa,
        "profil": profil,
        "profiller": PROFILLER,
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
            "secenekler": seri_port_secenekleri(deger, portlar) if anahtar == "seri_port" else [],
        })
    return alanlar


def sorun_giderme_maddeleri():
    return [
        {"baslik": "COM port listede gorunmuyor", "aciklama": "USB/RS232 donusturucuyu tekrar takin, Windows Aygit Yoneticisi'nde portu kontrol edin ve surucu kurulumunun tamamlandigindan emin olun."},
        {"baslik": "Port kullanimda hatasi", "aciklama": "Ayni COM portu kullanan diger kantar programlarini kapatin. Gerekirse servisi kapatip tekrar baslatin."},
        {"baslik": "SQLite ayari kaydedilemiyor", "aciklama": "C:\\kantar klasorunun yazilabilir oldugunu kontrol edin. Hizli kurulum veya calistir.bat dosyasini yonetici olarak calistirin."},
        {"baslik": "Ayarlar sayfasi acilmiyor", "aciklama": "Kantar servisi calisiyor mu kontrol edin. Tek servis adresi http://127.0.0.1/ayarlar seklindedir; Kantar 2 icin port degil ?profil=kantar2 parametresi kullanilir."},
        {"baslik": "Template dosyasi bulunamadi", "aciklama": "C:\\kantar\\templates\\kantar-ayarlar.html dosyasinin var oldugunu kontrol edin. Eksikse hizli kurulumu tekrar calistirin."},
    ]


def ayar_formu_html(profil, ayarlar, mesaj=None):
    if render_template is None:
        return "Kantar ayarlari sayfasi icin Flask render_template kullanilamadi. Flask paketini kontrol edin."
    portlar = seri_portlari_listele()
    context = ortak_template_context("ayarlar", profil)
    context.update({
        "mesaj": mesaj,
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

    @flask_app.route("/")
    def kantar_degeri():
        try:
            return metin_cevabi(kantar_degerini_oku(istek_profili()))
        except KantarHatasi as hata:
            mesaj = hata.kullanici_mesaji()
            gunluge_yaz(mesaj)
            return metin_cevabi(mesaj, 500)
        except Exception as hata:
            mesaj = KantarHatasi("Beklenmeyen bir hata olustu.", [
                "Python servis ekranindaki hata kaydini kontrol edin.",
                "Flask servisini yeniden baslatip tekrar deneyin.",
            ], str(hata)).kullanici_mesaji()
            gunluge_yaz(mesaj)
            return metin_cevabi(mesaj, 500)

    @flask_app.route("/ayarlar", methods=["GET", "POST"])
    def ayarlar_sayfasi():
        profil = istek_profili()
        mesaj = None
        if request.method == "POST":
            ayarlari_kaydet(profil, form_ayarlari_al(request.form))
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
        silinen = loglari_temizle()
        gunluge_yaz("Log temizleme islemi tamamlandi. Silinen dosya sayisi: %s" % silinen)
        if redirect is None:
            return json_cevabi({"ok": True, "silinen": silinen})
        return redirect("/loglar?profil=%s&mesaj=Loglar temizlendi" % istek_profili())


app = create_app()


def calistir():
    ayarlari_baslat()
    if app is None:
        import sys
        sys.stderr.write(
            "Kantar hatasi: Flask paketi kurulu degil.\n"
            "Kontrol edilecekler:\n"
            "- Komut satirinda pip install flask pyserial calistirin.\n"
            "- Betigi calistiran Python ortami ile kurulum yaptiginiz Python ortaminin ayni oldugunu kontrol edin.\n"
        )
        sys.exit(1)
    ayarlar = ayarlari_oku()
    servis_host = ayarlar.get("servis_host", "127.0.0.1")
    servis_port = ayar_int(ayarlar, "servis_port")
    try:
        if waitress_serve is not None:
            gunluge_yaz("Waitress WSGI sunucusu baslatiliyor: %s:%s" % (servis_host, servis_port))
            waitress_serve(app, host=servis_host, port=servis_port)
        else:
            gunluge_yaz("Waitress bulunamadi; Flask gelistirme sunucusu ile devam ediliyor.")
            app.run(host=servis_host, port=servis_port)
    except Exception as hata:
        import sys
        sys.stderr.write(
            "Kantar hatasi: Flask servisi baslatilamadi.\n"
            "Kontrol edilecekler:\n"
            "- 127.0.0.1/ayarlar sayfasindan servis host ve port ayarlarini kontrol edin.\n"
            "- KANTAR_SERVIS_PORT baska bir program tarafindan kullaniliyor olabilir.\n"
            "- 80 portu icin yonetici yetkisi gerekebilir; gerekirse 8090 gibi bir port deneyin.\n"
            "Teknik detay: %s\n" % hata
        )
        sys.exit(1)
