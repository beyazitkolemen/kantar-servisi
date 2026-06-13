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
    fetch("/serial/veri?" + urlParametreleri(), { cache: "no-store" })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        zaman.textContent = data.zaman || "-";
        if (data.ok) {
          okumaSayisi += 1;
          durum.textContent = data.uyari ? "Okundu / Uyari" : "Okundu";
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
        durum.textContent = "Baglanti hatasi";
        durumRengi("hata");
        satirYaz("HATA: " + error);
      })
      .finally(function () {
        istekSuruyor = false;
        sonrakiOkumayiPlanla();
      });
  }

  function portlariYenile() {
    document.getElementById("port-durum").textContent = "Portlar yenileniyor...";
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
        document.getElementById("port-durum").textContent = "Portlar okunamadi: " + error;
      });
  }

  function durdur() {
    izlemeAktif = false;
    if (timer) {
      window.clearTimeout(timer);
    }
    timer = null;
  }

  function baslat() {
    durdur();
    izlemeAktif = true;
    durum.textContent = "Izleniyor";
    durumRengi("bekle");
    oku();
  }

  document.getElementById("baslat").addEventListener("click", baslat);
  document.getElementById("tek-oku").addEventListener("click", oku);
  document.getElementById("durdur").addEventListener("click", function () {
    durdur();
    durum.textContent = "Durduruldu";
    durumRengi("bekle");
  });
  document.getElementById("temizle").addEventListener("click", function () {
    satirlar = [];
    panelGuncelle();
  });
  document.getElementById("kopyala").addEventListener("click", function () {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(akis.textContent || "");
    }
  });
  document.getElementById("port-yenile").addEventListener("click", portlariYenile);
  portlariYenile();
})();
