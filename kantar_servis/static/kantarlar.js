(function () {
  "use strict";

  var formlar = document.querySelectorAll("[data-kantar-sil-form]");
  formlar.forEach(function (form) {
    form.addEventListener("submit", function (olay) {
      var kantarAdi = form.getAttribute("data-kantar-adi") || "Secili kantar";
      if (!window.confirm(kantarAdi + " silinecek. Bu islem geri alinamaz. Devam edilsin mi?")) {
        olay.preventDefault();
      }
    });
  });
}());
