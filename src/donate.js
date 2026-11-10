/* donate.js — contribution button (greek.craven.fr / Grecs du Roi).
   Mirrors the latin.craven.fr and englisc.craven.fr reference sites
   (t_f742647a). The Polar Checkout Link lives on the <form> in
   data-donate-link — NOT an <a href> — so the server-rendered HTML
   stays free of external anchors. On submit we open the payment URL
   in a new tab with the chosen amount appended as ?amount=<value>,
   which Polar Checkout Links accept as a pay-what-you-want prefill.
   Without JS the button is a plain submit inside a form whose action
   is the current page: the browser reloads and the button copy ("€10
   (one-off, chargeable)") still conveys the intended charge — no dead
   button, no 404. */
(function () {
  "use strict";

  function init() {
    var forms = document.querySelectorAll("form[data-donate-link]");
    Array.prototype.forEach.call(forms, function (form) {
      var link = form.getAttribute("data-donate-link");
      if (!link) return;
      var input = form.querySelector("input[name='amount']");
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var amount;
        try {
          amount = input ? input.value.trim() : "";
        } catch (e) {
          amount = "";
        }
        var url = link;
        if (amount) {
          url += (url.indexOf("?") === -1 ? "?" : "&") +
            "amount=" + encodeURIComponent(amount);
        }
        window.open(url, "_blank", "noopener,noreferrer,width=800,height=950");
      }, true);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
