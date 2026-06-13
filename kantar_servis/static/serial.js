(function () {
  "use strict";

  var timer = null;
  var izlemeAktif = false;
  var istekSuruyor = false;
  var okumaSayisi = 0;
  var hataSayisi = 0;
  var satirlar = [];
  var akis = document.getElementById("akis");
  var durum = document.getElementById("durum");
  var agirlik = document.getElementById("agirlik");
  var zaman = document.getElementById("zaman");
  var portSelect = document.getElementById("port");
  var baslatButon = document.getElementById("baslat");
  var tekOkuButon = document.getElementById("tek-oku");
  var durdurButon = document.getElementById("durdur");
  var kopyalaButon = document.getElementById("kopyala");
  var portYenileButon = document.getElementById("port-yenile");

  function maksimumSatir() {
    var deger = parseInt(document.getElementById("maksimum-satir").value || "250", 10);
    return Math.max(25, Math.min(2000, deger));
  }

  function yenilemeAraligi() {
    var deger = parseInt(document.getElementById("aralik").value || "750", 10);
    return Math.max(250, deger);
  }

  function panelGuncelle() {
    akis.textContent = satirlar.join("\n");
    if (document.getElementById("otomatik-kaydir").checked) {
      akis.scrollTop = akis.scrollHeight;
    }
  }

  function satirYaz(metin) {
    satirlar.push(metin);
    if (satirlar.length > maksimumSatir()) {
      satirlar = satirlar.slice(satirlar.length - maksimumSatir());
    }
    panelGuncelle();
  }

  function durumRengi(tip) {
    var renk = tip === "hata" ? "text-rose-700" : (tip === "ok" ? "text-emerald-700" : "text-slate-900");
    durum.className = "mt-1 text-lg font-bold " + renk;
  }

  function urlParametreleri() {
    return "kantar=" + encodeURIComponent(document.getElementById("kantar").value) +
      "&port=" + encodeURIComponent(portSelect.value);
  }

  function butonlariKilitle(kilitli) {
    if (baslatButon) {
      baslatButon.disabled = kilitli && izlemeAktif;
    }
    if (tekOkuButon) {
      tekOkuButon.disabled = kilitli;
      tekOkuButon.setAttribute("aria-busy", kilitli ? "true" : "false");
    }
    if (portYenileButon) {
      portYenileButon.disabled = kilitli;
    }
    if (akis) {
      akis.setAttribute("aria-busy", kilitli ? "true" : "false");
    }
  }

  function izlemeDurumunuGuncelle() {
    if (!baslatButon) {
      return;
    }
    baslatButon.setAttribute("aria-pressed", izlemeAktif ? "true" : "false");
    if (izlemeAktif) {
      baslatButon.classList.add("ring-2", "ring-emerald-300");
    } else {
      baslatButon.classList.remove("ring-2", "ring-emerald-300");
    }
  }

  function sonrakiOkumayiPlanla() {
    if (izlemeAktif) {
      timer = window.setTimeout(oku, yenilemeAraligi());
    }
  }

  function oku() {
    if (istekSuruyor) {
      return;
    }
    istekSuruyor = true;
    butonlariKilitle(true);
    if (!izlemeAktif) {
      durum.textContent = "Okunuyor…";
      durumRengi("bekle");
    }
    fetch("/serial/veri?" + urlParametreleri(), { cache: "no-store" })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        zaman.textContent = data.zaman || "-";
        if (data.ok) {
          okumaSayisi += 1;
          durum.textContent = data.uyari ? "Okundu / Uyarı" : "Okundu";
          durumRengi(data.uyari ? "bekle" : "ok");
          agirlik.textContent = data.agirlik || "-";
          document.getElementById("port-baud").textContent = (data.seri_port || "-") + " / " + (data.baud_hizi || "-");
          document.getElementById("timeout").textContent = data.timeout || "-";
          document.getElementById("okuma-boyutu").textContent = data.okuma_boyutu || "-";
          document.getElementById("ham-uzunluk").textContent = data.ham_uzunluk || "0";
          document.getElementById("son-hex").textContent = data.ham_hex || "-";
          var satir = "[" + (data.zaman || "") + "] " + data.seri_port + " RAW: " + (data.ham_veri || "") +
            (data.agirlik ? " | KG: " + data.agirlik : "");
          if (document.getElementById("hex-goster").checked && data.ham_hex) {
            satir += " | HEX: " + data.ham_hex;
          }
          if (data.uyari) {
            satir += " | UYARI: " + data.uyari.replace(/\n/g, " ");
          }
          satirYaz(satir);
        } else {
          hataSayisi += 1;
          durum.textContent = "Hata";
          durumRengi("hata");
          satirYaz("[" + (data.zaman || "") + "] HATA: " + (data.hata || "Bilinmeyen hata"));
        }
        document.getElementById("okuma-sayisi").textContent = okumaSayisi;
        document.getElementById("hata-sayisi").textContent = hataSayisi;
      })
      .catch(function (error) {
        hataSayisi += 1;
        document.getElementById("hata-sayisi").textContent = hataSayisi;
        durum.textContent = "Bağlantı hatası";
        durumRengi("hata");
        satirYaz("HATA: " + error);
      })
      .finally(function () {
        istekSuruyor = false;
        butonlariKilitle(false);
        if (izlemeAktif) {
          durum.textContent = "İzleniyor";
          durumRengi("bekle");
        }
        sonrakiOkumayiPlanla();
      });
  }

  function portlariYenile() {
    document.getElementById("port-durum").textContent = "Portlar yenileniyor…";
    if (portYenileButon) {
      portYenileButon.disabled = true;
    }
    fetch("/serial/portlar?" + urlParametreleri(), { cache: "no-store" })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        var mevcut = portSelect.value;
        portSelect.innerHTML = "";
        (data.port_secenekleri || []).forEach(function (secenek) {
          var option = document.createElement("option");
          option.value = secenek.value;
          option.textContent = secenek.label;
          option.selected = secenek.selected || secenek.value === mevcut;
          portSelect.appendChild(option);
        });
        document.getElementById("port-durum").textContent = "Son yenileme: " + (data.zaman || "-");
      })
      .catch(function (error) {
        document.getElementById("port-durum").textContent = "Portlar okunamadı: " + error;
      })
      .finally(function () {
        if (portYenileButon) {
          portYenileButon.disabled = false;
        }
      });
  }

  function durdur() {
    izlemeAktif = false;
    if (timer) {
      window.clearTimeout(timer);
    }
    timer = null;
    izlemeDurumunuGuncelle();
  }

  function baslat() {
    durdur();
    izlemeAktif = true;
    durum.textContent = "İzleniyor";
    durumRengi("bekle");
    izlemeDurumunuGuncelle();
    oku();
  }

  baslatButon.addEventListener("click", baslat);
  tekOkuButon.addEventListener("click", oku);
  durdurButon.addEventListener("click", function () {
    durdur();
    durum.textContent = "Durduruldu";
    durumRengi("bekle");
  });
  document.getElementById("temizle").addEventListener("click", function () {
    satirlar = [];
    panelGuncelle();
    if (!izlemeAktif && satirlar.length === 0) {
      akis.textContent = "Akış temizlendi. Başlat veya Tek Oku ile yeniden izlemeye başlayın.";
    }
  });
  kopyalaButon.addEventListener("click", function () {
    var metin = akis.textContent || "";
    if (window.kantarUi && window.kantarUi.panoyaKopyala) {
      window.kantarUi.panoyaKopyala(metin, kopyalaButon);
      return;
    }
    if (navigator.clipboard) {
      navigator.clipboard.writeText(metin);
    }
  });
  portYenileButon.addEventListener("click", portlariYenile);
  portlariYenile();
}());
