/* Interações leves do front-end. Nenhuma regra importante depende deste arquivo:
   login, cadastro, reservas e doações continuam validados pelo Django. */
(function () {
  "use strict";

  const one = (selector, root = document) => root.querySelector(selector);
  const all = (selector, root = document) => [
    ...root.querySelectorAll(selector),
  ];

  const menuButton = one(".menu-toggle");
  const publicMenu = one("#public-menu");
  if (menuButton && publicMenu) {
    menuButton.addEventListener("click", () => {
      const aberto = publicMenu.classList.toggle("open");
      menuButton.setAttribute("aria-expanded", String(aberto));
    });
  }

  const dashMenu = one("#dash-menu");
  const sidebar = one("#sidebar");
  const backdrop = one("#drawer-backdrop");
  const closeDrawer = () => {
    sidebar?.classList.remove("open");
    if (backdrop) backdrop.hidden = true;
  };
  dashMenu?.addEventListener("click", () => {
    sidebar?.classList.add("open");
    if (backdrop) backdrop.hidden = false;
  });
  backdrop?.addEventListener("click", closeDrawer);

  const bell = one("#bell-button");
  const notifications = one("#notification-pop");
  const setNotificationsOpen = (open) => {
    if (!notifications || !bell) return;
    notifications.hidden = !open;
    bell.setAttribute("aria-expanded", String(open));
  };
  bell?.addEventListener("click", (event) => {
    event.stopPropagation();
    if (!notifications) return;
    setNotificationsOpen(notifications.hidden);
  });
  document.addEventListener("click", (event) => {
    if (!notifications || notifications.hidden) return;
    const wrap = one(".notification-wrap");
    if (wrap && !wrap.contains(event.target)) {
      setNotificationsOpen(false);
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setNotificationsOpen(false);
  });

  all(".flash-message button").forEach((button) => {
    button.addEventListener("click", () =>
      button.closest(".flash-message")?.remove(),
    );
  });
  window.setTimeout(
    () => all(".flash-message").forEach((item) => item.remove()),
    6500,
  );

  all(".faq-item button").forEach((button) => {
    button.addEventListener("click", () => {
      const answer = button.parentElement.querySelector("p");
      const marker = button.querySelector("span");
      if (!answer) return;
      answer.hidden = !answer.hidden;
      if (marker) marker.textContent = answer.hidden ? "+" : "−";
    });
  });

  const roleGrid = one("[data-role-grid]");
  roleGrid?.addEventListener("change", (event) => {
    const input = event.target.closest("input[type=radio]");
    if (!input) return;
    all(".role-card", roleGrid).forEach((card) =>
      card.classList.toggle("selected", card.contains(input)),
    );
  });

  all("[data-confirm-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirmForm)) event.preventDefault();
    });
  });

  const photoInput = one("#id_foto");
  const photoPreview = one("#photo-preview");
  photoInput?.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (file && photoPreview) photoPreview.src = URL.createObjectURL(file);
  });

  // Quantidade se adapta à unidade: kg/litros aceitam vírgula; demais só inteiros.
  const quantityInput =
    one("[data-quantity-input]") || one("#id_quantidade");
  const unitSelect = one("[data-unit-select]") || one("#id_unidade");
  const unidadesDecimais = new Set(["kg", "litros"]);
  const helpQuantidade = () => {
    if (!quantityInput) return null;
    const label = quantityInput.closest("label");
    if (!label) return null;
    let hint = label.querySelector("[data-quantity-hint]");
    if (!hint) {
      hint = document.createElement("small");
      hint.dataset.quantityHint = "1";
      label.appendChild(hint);
    }
    return hint;
  };
  const aplicarRegraQuantidade = () => {
    if (!quantityInput || !unitSelect) return;
    const unidade = unitSelect.value;
    const decimal = unidadesDecimais.has(unidade);
    quantityInput.inputMode = decimal ? "decimal" : "numeric";
    quantityInput.placeholder = decimal ? "Ex.: 2,5" : "Ex.: 10";
    quantityInput.dataset.allowDecimal = decimal ? "1" : "0";
    const hint = helpQuantidade();
    if (hint) {
      hint.textContent = decimal
        ? "Use vírgula para decimais (ex.: 1,5 kg)."
        : "Somente números inteiros para esta unidade.";
    }
    // Se trocar para unidade inteira e houver decimal, arredonda para baixo no campo.
    if (!decimal && quantityInput.value) {
      const normalizado = quantityInput.value.replace(",", ".");
      const numero = Number(normalizado);
      if (!Number.isNaN(numero) && !Number.isInteger(numero)) {
        quantityInput.value = String(Math.trunc(numero));
      }
    }
  };
  const sanitizarQuantidade = (valor, allowDecimal) => {
    let limpo = String(valor || "").replace(/[^\d.,]/g, "");
    // Mantém só o primeiro separador decimal (vírgula ou ponto).
    if (allowDecimal) {
      const match = limpo.match(/^(\d*)([.,]?)(\d*)/);
      if (!match) return "";
      const sep = match[2] ? "," : "";
      return `${match[1]}${sep}${match[3]}`;
    }
    return limpo.replace(/[.,]/g, "");
  };
  unitSelect?.addEventListener("change", aplicarRegraQuantidade);
  quantityInput?.addEventListener("input", () => {
    const allowDecimal = quantityInput.dataset.allowDecimal === "1";
    const atual = quantityInput.value;
    const limpo = sanitizarQuantidade(atual, allowDecimal);
    if (atual !== limpo) quantityInput.value = limpo;
  });
  quantityInput?.addEventListener("blur", () => {
    if (!quantityInput.value) return;
    const allowDecimal = quantityInput.dataset.allowDecimal === "1";
    // Normaliza ponto digitado para vírgula (padrão BR na interface).
    if (allowDecimal && quantityInput.value.includes(".")) {
      quantityInput.value = quantityInput.value.replace(".", ",");
    }
  });
  aplicarRegraQuantidade();

  const cepInput = one("#id_cep");
  const cepFeedback = one("#cep-feedback");
  const setValue = (id, value) => {
    const field = one(`#${id}`);
    if (field && value) field.value = value;
  };
  cepInput?.addEventListener("blur", async () => {
    const cep = cepInput.value.replace(/\D/g, "");
    if (cep.length !== 8) return;
    if (cepFeedback) cepFeedback.textContent = "Consultando CEP...";
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const address = await response.json();
      if (!response.ok || address.erro) throw new Error("CEP não encontrado");
      setValue("id_logradouro", address.logradouro);
      setValue("id_bairro", address.bairro);
      setValue("id_cidade", address.localidade);
      setValue("id_estado", address.uf);
      if (cepFeedback)
        cepFeedback.textContent =
          "✓ Endereço preenchido automaticamente pela ViaCEP";
    } catch (_) {
      if (cepFeedback)
        cepFeedback.textContent =
          "Não foi possível consultar o CEP; preencha o endereço manualmente.";
    }
  });

  const doacaoLocationButton = one("#doacao-location-button");
  const doacaoLocationStatus = one("#doacao-location-status");
  const doacaoLatitude = one("#id_latitude");
  const doacaoLongitude = one("#id_longitude");
  doacaoLocationButton?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      if (doacaoLocationStatus) doacaoLocationStatus.textContent = "Geolocalização não disponível neste navegador.";
      return;
    }
    doacaoLocationButton.disabled = true;
    if (doacaoLocationStatus) doacaoLocationStatus.textContent = "Obtendo localização...";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (doacaoLatitude) doacaoLatitude.value = position.coords.latitude.toFixed(6);
        if (doacaoLongitude) doacaoLongitude.value = position.coords.longitude.toFixed(6);
        if (doacaoLocationStatus) doacaoLocationStatus.textContent = "✓ Localização registrada.";
        doacaoLocationButton.disabled = false;
      },
      () => {
        if (doacaoLocationStatus) doacaoLocationStatus.textContent = "Permita o acesso à localização no navegador para usar este recurso.";
        doacaoLocationButton.disabled = false;
      },
    );
  });

  /* Gráficos SVG reais e responsivos da página Impacto. Os dados são
     fornecidos pelo Django e cada aba redesenha linha, área, eixos e pontos. */
  const svgNamespace = "http://www.w3.org/2000/svg";
  const createSvg = (tag, attributes = {}) => {
    const element = document.createElementNS(svgNamespace, tag);
    Object.entries(attributes).forEach(([name, value]) =>
      element.setAttribute(name, String(value)),
    );
    return element;
  };

  const formatChartValue = (value) =>
    new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value);

  const chartCaptions = {
    month: "Quilos destinados ao longo do mês",
    quarter: "Quilos destinados nos últimos três meses",
    year: "Quilos destinados ao longo do ano",
    semester: "Quilos destinados nos últimos seis meses",
    all: "Quilos destinados em todo o período",
  };

  const renderLineChart = (chart, period) => {
    const sourceId = chart.dataset.source;
    const source = sourceId ? document.getElementById(sourceId) : null;
    if (!source) return;

    let datasets;
    try {
      datasets = JSON.parse(source.textContent);
    } catch (_) {
      return;
    }
    const dataset = datasets[period] || datasets[Object.keys(datasets)[0]];
    if (!dataset?.labels?.length || !dataset?.values?.length) return;

    const svg = one("svg", chart);
    const grid = one("[data-chart-grid]", chart);
    const area = one("[data-chart-area]", chart);
    const line = one("[data-chart-line]", chart);
    const points = one("[data-chart-points]", chart);
    const labels = one("[data-chart-labels]", chart);
    const tooltip = one(".chart-tooltip", chart);
    if (!svg || !grid || !area || !line || !points || !labels) return;

    const bounds = { left: 66, right: 654, top: 24, bottom: 222 };
    const values = dataset.values.map((value) => Number(value) || 0);
    const highest = Math.max(...values, 1);
    const step = highest <= 100 ? 25 : highest <= 500 ? 100 : 300;
    const maximum = Math.max(step, Math.ceil(highest / step) * step);
    const ticks = 5;

    grid.replaceChildren();
    points.replaceChildren();
    labels.replaceChildren();

    for (let index = 0; index <= ticks; index += 1) {
      const y = bounds.bottom - ((bounds.bottom - bounds.top) * index) / ticks;
      grid.append(
        createSvg("line", {
          x1: bounds.left,
          x2: bounds.right,
          y1: y,
          y2: y,
        }),
      );
      const tickLabel = createSvg("text", { x: 10, y: y + 5 });
      tickLabel.textContent = formatChartValue((maximum * index) / ticks);
      grid.append(tickLabel);
    }

    const coordinates = values.map((value, index) => {
      const divisor = Math.max(values.length - 1, 1);
      const x = bounds.left + ((bounds.right - bounds.left) * index) / divisor;
      const y = bounds.bottom - ((bounds.bottom - bounds.top) * value) / maximum;
      return { x, y, value, label: dataset.labels[index] || "" };
    });
    const path = coordinates
      .map(({ x, y }, index) => `${index ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`)
      .join(" ");
    line.setAttribute("d", path);
    area.setAttribute(
      "d",
      `${path} L${bounds.right} ${bounds.bottom} L${bounds.left} ${bounds.bottom} Z`,
    );

    coordinates.forEach(({ x, y, value, label: pointLabel }) => {
      const circle = createSvg("circle", { cx: x, cy: y, r: 5.5 });
      const title = createSvg("title");
      title.textContent = `${pointLabel}: ${formatChartValue(value)} kg`;
      circle.append(title);
      if (tooltip) {
        circle.addEventListener("pointerenter", () => {
          tooltip.textContent = `${pointLabel} · ${formatChartValue(value)} kg`;
          tooltip.style.left = `${(x / 680) * 100}%`;
          tooltip.style.top = `${(y / 280) * 100}%`;
          tooltip.hidden = false;
        });
        circle.addEventListener("pointerleave", () => {
          tooltip.hidden = true;
        });
      }
      points.append(circle);

      const xLabel = createSvg("text", {
        x,
        y: 260,
        "text-anchor": "middle",
      });
      xLabel.textContent = pointLabel;
      labels.append(xLabel);
    });

    const caption = chart
      .closest(".chart-card, .public-chart-card")
      ?.querySelector("[data-chart-caption]");
    if (caption && chartCaptions[period]) caption.textContent = chartCaptions[period];
    chart.dataset.activePeriod = period;
    line.classList.remove("is-drawn");
    window.requestAnimationFrame(() => line.classList.add("is-drawn"));
  };

  all("[data-line-chart]").forEach((chart) => {
    const chartName = chart.dataset.lineChart;
    const tabs = one(`[data-chart-tabs="${chartName}"]`);
    const tabButtons = tabs ? all("[data-chart-period]", tabs) : [];
    const firstPeriod = tabButtons.find((button) =>
      button.classList.contains("active"),
    )?.dataset.chartPeriod;
    renderLineChart(chart, firstPeriod || "month");

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        tabButtons.forEach((item) => {
          const active = item === button;
          item.classList.toggle("active", active);
          item.setAttribute("aria-pressed", String(active));
        });
        renderLineChart(chart, button.dataset.chartPeriod);
      });
    });
  });

  // Só troca classe em botões puramentes visuais.
  // Abas com <a href="?..."> (ex.: Minhas doações) devem navegar normalmente.
  all(".tabs button, .period-tabs button, .view-buttons button").forEach(
    (button) => {
      if (button.tagName !== "BUTTON") return;
      button.addEventListener("click", () => {
        all("button", button.parentElement).forEach((item) =>
          item.classList.remove("active"),
        );
        button.classList.add("active");
      });
    },
  );

  all("[data-print-button]").forEach((button) =>
    button.addEventListener("click", () => window.print()),
  );

  const profileTabs = one(".profile-tabs");
  const profilePanels = all(".profile-form .tab-panel");
  const activateProfileTab = (tabId) => {
    if (!profileTabs || !tabId) return;
    all("button[data-tab]", profileTabs).forEach((button) => {
      const active = button.dataset.tab === tabId;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
    });
    profilePanels.forEach((panel) => {
      const active = panel.id === tabId;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  };
  if (profileTabs && profilePanels.length) {
    profileTabs.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-tab]");
      if (!button) return;
      event.preventDefault();
      activateProfileTab(button.dataset.tab);
    });
    all("[data-profile-tab]").forEach((link) => {
      link.addEventListener("click", () => activateProfileTab(link.dataset.profileTab));
    });
    const panelWithErrors = profilePanels.find((panel) =>
      panel.querySelector(".errorlist, .form-alert, .error"),
    );
    if (panelWithErrors) activateProfileTab(panelWithErrors.id);
    else if (location.hash === "#campo-foto") activateProfileTab("pessoais");
  }
})();
