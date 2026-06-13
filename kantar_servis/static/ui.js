(function () {
  "use strict";

  function geriBildirimGoster(buton, mesaj, sure) {
    if (!buton) {
      return;
    }
    var orijinal = buton.getAttribute("data-orijinal-metin") || buton.textContent;
    buton.setAttribute("data-orijinal-metin", orijinal);
    buton.textContent = mesaj;
    window.setTimeout(function () {
      buton.textContent = buton.getAttribute("data-orijinal-metin") || orijinal;
    }, sure || 1800);
  }

  function panoyaKopyala(metin, buton) {
    if (!metin) {
      geriBildirimGoster(buton, "Kopyalanacak metin yok", 2000);
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(metin)
        .then(function () {
          geriBildirimGoster(buton, "Kopyalandı");
        })
        .catch(function () {
          geriBildirimGoster(buton, "Kopyalanamadı", 2000);
        });
      return;
    }
    geriBildirimGoster(buton, "Pano desteklenmiyor", 2000);
  }

  function formGonderiminiKilitle(form) {
    form.addEventListener("submit", function () {
      var buton = form.querySelector("[type=submit]");
      if (!buton || buton.disabled) {
        return;
      }
      var yukleniyor = buton.getAttribute("data-yukleniyor-metin") || "Kaydediliyor…";
      buton.setAttribute("data-orijinal-metin", buton.textContent);
      buton.textContent = yukleniyor;
      buton.disabled = true;
      buton.setAttribute("aria-busy", "true");
    });
  }

  document.querySelectorAll("[data-copy]").forEach(function (buton) {
    buton.addEventListener("click", function () {
      panoyaKopyala(buton.getAttribute("data-copy") || "", buton);
    });
  });

  document.querySelectorAll("form[data-submit-loading]").forEach(formGonderiminiKilitle);

  window.kantarUi = {
    geriBildirimGoster: geriBildirimGoster,
    panoyaKopyala: panoyaKopyala,
  };
}());
