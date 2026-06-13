# -*- coding: cp1254 -*-
# Python 3 uyumlu LISDEP kantar servisi giris noktasi.
# Asil uygulama kodu kantar_servis paketindeki modullere ayrilmistir.

from kantar_servis.config import (  # noqa: F401
    AYAR_ALANLARI,
    PROFIL_KANTAR1,
    PROFIL_KANTAR2,
    PROFIL_TEKLI,
    PROFILLER,
    TEMPLATE_KLASOR,
    VARSAYILAN_AYARLAR,
    ayar_db_yolu,
    ayar_float,
    ayar_int,
    log_dosya_yolu,
    profil_normalize,
    secili_profil,
)
from kantar_servis.errors import KantarHatasi  # noqa: F401
from kantar_servis.logging_utils import gunluge_yaz, log_dosya_bilgisi, loglari_oku, loglari_temizle  # noqa: F401
from kantar_servis.serial_bridge import (  # noqa: F401
    agirlik_degerini_ayikla,
    ham_veriyi_duzenle,
    kantar_degerini_oku,
    seri_port_bilgileri,
    seri_port_secenekleri,
    seri_portlari_listele,
    serial_ham_veri_oku,
)
from kantar_servis.storage import (  # noqa: F401
    ayarlari_baslat,
    ayarlari_kaydet,
    ayarlari_oku,
    baglanti_ac,
    sqlite_durumu_oku,
)
from kantar_servis.web import (  # noqa: F401
    app,
    ayar_formu_alanlari,
    ayar_formu_html,
    calistir,
    form_ayarlari_al,
    istek_profili,
    json_cevabi,
    metin_cevabi,
    ortak_template_context,
    serial_port_parametresi,
    sorun_giderme_maddeleri,
)


if __name__ == "__main__":
    calistir()
