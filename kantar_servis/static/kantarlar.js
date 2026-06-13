(function () {
  "use strict";

  var silmeFormlari = document.querySelectorAll("[data-kantar-sil-form]");
  silmeFormlari.forEach(function (form) {
    form.addEventListener("submit", function (olay) {
      var kantarAdi = form.getAttribute("data-kantar-adi") || "Seçili kantar";
      if (!window.confirm(kantarAdi + " silinecek. Bu işlem geri alınamaz. Devam edilsin mi?")) {
        olay.preventDefault();
      }
    });
  });

  var kantarSecimi = document.getElementById("kantar-secimi");
  if (kantarSecimi) {
    kantarSecimi.addEventListener("change", function () {
      var secilen = kantarSecimi.value;
      if (secilen) {
        window.location.href = "/ayarlar?kantar=" + encodeURIComponent(secilen);
      }
    });
  }
}());
