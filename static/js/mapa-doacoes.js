/* Mapa de doações disponíveis, com Leaflet.js + OpenStreetMap.
   Só executa se existir #donation-map na página (busca de doações). */
(function () {
  "use strict";

  const mapaElemento = document.getElementById("donation-map");
  if (!mapaElemento || typeof L === "undefined") return;

  // Ícone das doações (verde ou amarelo se for urgente)
  const iconePorUrgencia = (urgente) =>
    L.divIcon({
      className: "",
      html: `<span class="map-pin${urgente ? " urgent" : ""}"></span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -30],
    });

  // NOVO: Ícone especial para o usuário (Ponto Azul de GPS)
  const iconeUsuario = L.divIcon({
    className: "",
    html: `<div style="width: 20px; height: 20px; background: #4285f4; border: 3px solid white; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });

  const mapa = L.map(mapaElemento, { scrollWheelZoom: false });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(mapa);

  // --- INÍCIO DO SISTEMA DE LOCALIZAÇÃO POR IP ---
  
  //  Posição de segurança (São Paulo) - O meu "Plano B" pra nao dar bugs facilmente
  const posicaoSeguranca = [-23.5505, -46.6333];
  
  // O mapa liga primeiro na posição de segurança para nunca ficar em branco
  mapa.setView(posicaoSeguranca, 12); 

  // O assistente Silencioso
  async function focarNaRegiaoDoUsuario() {
    try { // "Tente fazer isso:"
      // Bate no catálogo gratuito e confiável de IPs (ipwho.is)
      const resposta = await fetch("https://ipwho.is/");
      const dados = await resposta.json();

      // Se deu certo e o catálogo devolveu as coordenadas da cidade, move a câmera
      if (dados.success && dados.latitude && dados.longitude) {
        mapa.setView([dados.latitude, dados.longitude], 12);
      }
    } catch (erro) { // "Se der errado:"
      // O Assistente engole o choro em silêncio. 
      // Não quebra a tela, apenas mantém na posição de segurança.
      console.warn("Assistente de IP indisponível no momento. Usando Plano B.");
    }
  }
  
  // Dá a ordem para o Assistente trabalhar assim que o mapa carregar
  focarNaRegiaoDoUsuario();
  
  // --- FIM DO SISTEMA DE LOCALIZAÇÃO POR IP ---

  let marcadores = [];
  let marcadorUsuario = null; // Para guardar o ponto do usuário
  let circuloRaio = null;     // Para guardar o Radar de 5km

  const carregarDoacoes = async () => {
    try {
      // O mapa puxa as informações usando a URL (o "bilhete") que criamos na Gaveta
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

      // Se a pessoa AINDA NÃO ativou a localização, o mapa foca nos alimentos
      if (marcadores.length && !marcadorUsuario) {
        mapa.fitBounds(L.featureGroup(marcadores).getBounds().pad(0.2));
      }
    } catch (erro) {
      console.error(erro);
    }
  };

  carregarDoacoes();

  // NOVO: Lógica completa do Radar do Botão "Usar minha localização"
  document.querySelector("[data-location-button]")?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      window.alert("Geolocalização não disponível neste navegador.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (posicao) => {
        const lat = posicao.coords.latitude;
        const lng = posicao.coords.longitude;

        // Limpa o ponto e o círculo anteriores (se a pessoa clicar duas vezes)
        if (marcadorUsuario) mapa.removeLayer(marcadorUsuario);
        if (circuloRaio) mapa.removeLayer(circuloRaio);

        // 1. Coloca o Ponto Azul na casa do usuário
        marcadorUsuario = L.marker([lat, lng], { icon: iconeUsuario }).addTo(mapa);
        marcadorUsuario.bindPopup("<b>Você está aqui!</b>").openPopup();

        // 2. Desenha o Radar de 5km (5000 metros) verde e translúcido
        circuloRaio = L.circle([lat, lng], {
          color: '#0f972f',
          fillColor: '#0f972f',
          fillOpacity: 0.1,
          radius: 5000 
        }).addTo(mapa);

        // 3. Dá o zoom automático para a tela enquadrar exatamente o círculo
        mapa.fitBounds(circuloRaio.getBounds());
      },
      () => window.alert("Permita o acesso à localização no navegador para usar este recurso.")
    );
  });
})();