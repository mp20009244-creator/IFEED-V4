/* Mapa de doações disponíveis, com Leaflet.js + OpenStreetMap.
   Só executa se existir #donation-map na página (busca de doações). */
(function () {
  "use strict";

  const mapaElemento = document.getElementById("donation-map");
  if (!mapaElemento || typeof L === "undefined") return;

  const iconePorUrgencia = (urgente) =>
    L.divIcon({
      className: "",
      html: `<span class="map-pin${urgente ? " urgent" : ""}"></span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -30],
    });

  const mapa = L.map(mapaElemento, { scrollWheelZoom: false });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(mapa);

  mapa.setView([-23.5505, -46.6333], 12); // ajustado assim que os dados chegarem

  let marcadores = [];

  const carregarDoacoes = async () => {
    try {
      const resposta = await fetch(mapaElemento.dataset.mapaUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resposta.ok) throw new Error("Falha ao carregar doações do mapa.");
      const dados = await resposta.json();

      marcadores.forEach((marcador) => mapa.removeLayer(marcador));
      marcadores = [];

      dados.doacoes.forEach((doacao) => {
        const marcador = L.marker([doacao.latitude, doacao.longitude], {
          icon: iconePorUrgencia(doacao.urgente),
        }).addTo(mapa);
        marcador.bindPopup(`
          <div class="donation-popup">
            <img src="${doacao.foto_url}" alt="">
            <div>
              <strong>${doacao.nome_alimento}</strong>
              <span>${doacao.organizacao}</span>
              <span>${doacao.quantidade} · Validade ${doacao.data_validade}</span>
              <a href="${doacao.detalhe_url}">Ver doação</a>
            </div>
          </div>
        `);
        marcadores.push(marcador);
      });

      if (marcadores.length) {
        mapa.fitBounds(L.featureGroup(marcadores).getBounds().pad(0.2));
      }
    } catch (erro) {
      console.error(erro);
    }
  };

  carregarDoacoes();

  document.querySelector("[data-location-button]")?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      window.alert("Geolocalização não disponível neste navegador.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (posicao) => mapa.setView([posicao.coords.latitude, posicao.coords.longitude], 14),
      () => window.alert("Permita o acesso à localização no navegador para usar este recurso."),
    );
  });
})();