(function () {
  "use strict";

  var logAlani = document.getElementById("loglar");
  var istekSuruyor = false;

  function yukle() {
    if (istekSuruyor) {
      return;
    }
    istekSuruyor = true;
    fetch("/loglar/veri", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        logAlani.textContent = (data.loglar || []).join("\n");
        if (data.log_bilgisi) {
          document.getElementById("log-boyut").textContent = data.log_bilgisi.boyut_kb + " KB";
          document.getElementById("log-son-guncelleme").textContent = data.log_bilgisi.son_guncelleme;
        }
      })
      .catch(function (error) {
        logAlani.textContent = "Loglar okunamadi: " + error;
      })
      .finally(function () {
        istekSuruyor = false;
      });
  }

  document.getElementById("yenile").addEventListener("click", yukle);
  document.getElementById("log-temizle-formu").addEventListener("submit", function (event) {
    if (!window.confirm("Log kayitlari temizlensin mi?")) {
      event.preventDefault();
    }
  });
  window.setInterval(yukle, 5000);
})();
