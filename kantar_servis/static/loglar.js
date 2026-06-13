(function () {
  "use strict";

  var logAlani = document.getElementById("loglar");
  var yenileButon = document.getElementById("yenile");
  var istekSuruyor = false;
  var BOS_MESAJ = "Henüz log kaydı yok. Servis çalıştığında kayıtlar burada görünür.";
  var YUKLENIYOR_MESAJ = "Loglar yükleniyor…";

  function yukleniyorGoster() {
    if (logAlani) {
      logAlani.textContent = YUKLENIYOR_MESAJ;
      logAlani.setAttribute("aria-busy", "true");
    }
    if (yenileButon) {
      yenileButon.disabled = true;
      yenileButon.setAttribute("aria-busy", "true");
      yenileButon.setAttribute("data-orijinal-metin", yenileButon.textContent);
      yenileButon.textContent = "Yükleniyor…";
    }
  }

  function yukleniyorGizle() {
    if (logAlani) {
      logAlani.setAttribute("aria-busy", "false");
    }
    if (yenileButon) {
      yenileButon.disabled = false;
      yenileButon.setAttribute("aria-busy", "false");
      yenileButon.textContent = yenileButon.getAttribute("data-orijinal-metin") || "Yenile";
    }
  }

  function yukle() {
    if (istekSuruyor) {
      return;
    }
    istekSuruyor = true;
    yukleniyorGoster();
    fetch("/loglar/veri", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        var satirlar = data.loglar || [];
        if (satirlar.length === 0) {
          logAlani.textContent = BOS_MESAJ;
        } else {
          logAlani.textContent = satirlar.join("\n");
        }
        if (data.log_bilgisi) {
          document.getElementById("log-boyut").textContent = data.log_bilgisi.boyut_kb + " KB";
          document.getElementById("log-son-guncelleme").textContent = data.log_bilgisi.son_guncelleme;
        }
      })
      .catch(function (error) {
        logAlani.textContent = "Loglar okunamadı: " + error;
      })
      .finally(function () {
        istekSuruyor = false;
        yukleniyorGizle();
      });
  }

  if (logAlani && !logAlani.textContent.trim()) {
    logAlani.textContent = BOS_MESAJ;
  }

  yenileButon.addEventListener("click", yukle);
  document.getElementById("log-temizle-formu").addEventListener("submit", function (event) {
    if (!window.confirm("Log kayıtları temizlensin mi?")) {
      event.preventDefault();
    }
  });
  window.setInterval(yukle, 5000);
}());
