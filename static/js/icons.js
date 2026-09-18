/* Ícones PNG locais do iFeed.
   O caminho é calculado a partir deste próprio arquivo, por isso funciona no
   servidor Django sem CDN, npm ou configuração adicional. */
(function () {
  "use strict";

  const scriptUrl = document.currentScript?.src || "/static/js/icons.js";
  const iconsBase = new URL("../assets/icons/", scriptUrl);

  document.querySelectorAll("[data-icon]").forEach((holder) => {
    const name = holder.dataset.icon;
    if (!name || holder.querySelector("img.app-icon")) return;

    const image = document.createElement("img");
    image.className = "app-icon";
    image.src = new URL(`${name}.png`, iconsBase).href;
    image.alt = "";
    image.setAttribute("aria-hidden", "true");
    image.decoding = "async";
    holder.replaceChildren(image);
  });
})();
