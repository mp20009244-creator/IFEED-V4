from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CadastroForm, DoacaoForm, LoginForm, PerfilForm
from .models import Doacao, Perfil

User = get_user_model()

# Abas oficiais de "Minhas doações" (valor da query → filtro de status)
STATUS_FILTRO_DOACOES = {
    "todas": None,
    "disponiveis": Doacao.Status.DISPONIVEL,
    "reservadas": Doacao.Status.RESERVADA,
    "coletadas": Doacao.Status.COLETADA,
    "entregues": Doacao.Status.ENTREGUE,
}
DOACOES_POR_PAGINA = 8


def _perfil(user, **defaults):
    perfil, _ = Perfil.objects.get_or_create(user=user, defaults=defaults)
    return perfil


def _metricas(user):
    """Agrega impacto do usuário sem carregar objetos em memória."""
    qs = user.doacoes_criadas.filter(status=Doacao.Status.ENTREGUE)
    # peso_estimado_kg não é coluna; calculamos em Python apenas o necessário
    # via values_list para evitar N+1 e manter a regra de conversão centralizada.
    pesos = [
        Doacao(
            quantidade=quantidade,
            unidade=unidade,
        ).peso_estimado_kg
        for quantidade, unidade in qs.values_list("quantidade", "unidade")
    ]
    doadas = sum(pesos, Decimal("0"))
    instituicoes = (
        qs.exclude(reservada_por__isnull=True)
        .values("reservada_por_id")
        .distinct()
        .count()
    )
    return {
        "alimentos_doados": round(doadas, 1),
        "refeicoes": int(doadas * Decimal("2")),
        "desperdicio": round(doadas * Decimal("0.68"), 1),
        "doacoes_realizadas": len(pesos),
        "instituicoes": instituicoes,
    }


def _serie_proporcional(total, labels, proporcoes):
    """Cria pontos coerentes com o total real sem depender de biblioteca externa."""
    total = float(total or 0)
    return {
        "labels": labels,
        "values": [round(total * proporcao, 1) for proporcao in proporcoes],
    }


def _grafico_impacto(total):
    """Séries usadas pelos filtros interativos da página Impacto."""
    return {
        "month": _serie_proporcional(
            total,
            ["01/05", "08/05", "15/05", "22/05", "29/05"],
            [0.16, 0.48, 0.40, 0.82, 1.0],
        ),
        "quarter": _serie_proporcional(
            total,
            ["Jun", "Jul", "Ago"],
            [0.45, 0.71, 1.0],
        ),
        "year": _serie_proporcional(
            total,
            ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago"],
            [0.09, 0.17, 0.28, 0.39, 0.53, 0.68, 0.84, 1.0],
        ),
    }


def _grafico_impacto_publico():
    """Séries demonstrativas da página pública, como na concept art aprovada."""
    return {
        "semester": {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "values": [320, 500, 450, 720, 1010, 1250],
        },
        "year": {
            "labels": [
                "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez",
            ],
            "values": [210, 340, 480, 430, 650, 760, 710, 880, 1050, 990, 1290, 1250],
        },
        "all": {
            "labels": ["2024", "2025", "2026"],
            "values": [420, 870, 1250],
        },
    }


def _contagem_por_status(queryset, *status_list):
    """Uma única query com Count filtrado por status."""
    aggregates = {
        status: Count("id", filter=Q(status=status)) for status in status_list
    }
    aggregates["total"] = Count("id")
    return queryset.aggregate(**aggregates)


def home(request):
    doacoes = (
        Doacao.objects.filter(status=Doacao.Status.DISPONIVEL)
        .select_related("doador")[:3]
    )
    return render(request, "public/home.html", {"doacoes_destaque": doacoes})


def como_funciona(request):
    return render(request, "public/como_funciona.html")


def impacto_publico(request):
    return render(
        request,
        "public/impacto.html",
        {"impacto_publico_chart": _grafico_impacto_publico()},
    )


def quem_somos(request):
    return render(request, "public/quem_somos.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("painel")

    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        django_login(request, form.get_user())
        if not request.POST.get("lembrar"):
            request.session.set_expiry(0)
        messages.success(request, "Bem-vindo de volta ao iFeed!")
        destino = request.POST.get("next") or request.GET.get("next")
        if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}):
            return redirect(destino)
        return redirect("painel")

    return render(request, "auth/login.html", {"form": form})


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect("painel")

    perfil_inicial = request.GET.get("perfil", Perfil.Tipo.DOADOR)
    if perfil_inicial not in Perfil.Tipo.values:
        perfil_inicial = Perfil.Tipo.DOADOR
    form = CadastroForm(request.POST or None, initial={"tipo": perfil_inicial})
    if request.method == "POST" and form.is_valid():
        user = form.save()
        django_login(request, user)
        messages.success(request, "Sua conta foi criada com sucesso!")
        return redirect("painel")

    return render(request, "auth/cadastro.html", {"form": form})


@require_POST
def encerrar_sessao(request):
    django_logout(request)
    messages.success(request, "Você saiu da sua conta com segurança.")
    return redirect("home")


@login_required
def painel(request):
    metricas = _metricas(request.user)
    proximas = (
        Doacao.objects.filter(status=Doacao.Status.DISPONIVEL)
        .exclude(doador=request.user)
        .select_related("doador", "doador__perfil_ifeed")[:3]
    )
    recentes = request.user.doacoes_criadas.select_related("reservada_por")[:4]
    return render(
        request,
        "internal/painel.html",
        {"metricas": metricas, "proximas": proximas, "recentes": recentes},
    )


def _doacoes_disponiveis_queryset(request):
    """Compartilhado entre a página de busca e o endpoint JSON do mapa."""
    busca = request.GET.get("q", "").strip()
    doacoes = (
        Doacao.objects.filter(status=Doacao.Status.DISPONIVEL)
        .exclude(doador=request.user)
        .select_related("doador", "doador__perfil_ifeed")
    )
    if busca:
        doacoes = doacoes.filter(
            Q(nome_alimento__icontains=busca)
            | Q(categoria__icontains=busca)
            | Q(doador__perfil_ifeed__organizacao__icontains=busca)
        )
    return doacoes, busca


@login_required
def doacoes_disponiveis(request):
    doacoes, busca = _doacoes_disponiveis_queryset(request)
    return render(
        request,
        "internal/doacoes_disponiveis.html",
        {"doacoes": doacoes, "busca": busca},
    )


@login_required
def mapa_doacoes_dados(request):
    """Endpoint dedicado ao mapa (Leaflet)."""
    doacoes, _ = _doacoes_disponiveis_queryset(request)
    doacoes = doacoes.filter(latitude__isnull=False, longitude__isnull=False)
    dados = []
    for doacao in doacoes:
        perfil = getattr(doacao.doador, "perfil_ifeed", None)
        organizacao = (
            (perfil.organizacao if perfil else "") or doacao.doador.get_full_name()
        )
        dados.append(
            {
                "id": doacao.id,
                "nome_alimento": doacao.nome_alimento,
                "organizacao": organizacao,
                "quantidade": doacao.quantidade_formatada,
                "data_validade": doacao.data_validade.strftime("%d/%m"),
                "foto_url": doacao.foto_url,
                "latitude": float(doacao.latitude),
                "longitude": float(doacao.longitude),
                "urgente": doacao.esta_urgente,
                "detalhe_url": reverse("doacao_detalhe", kwargs={"pk": doacao.pk}),
            }
        )
    return JsonResponse({"doacoes": dados})


@login_required
def doacao_detalhe(request, pk):
    doacao = get_object_or_404(
        Doacao.objects.select_related("doador", "doador__perfil_ifeed", "reservada_por"),
        pk=pk,
    )
    return render(request, "internal/doacao_detalhe.html", {"doacao": doacao})


@login_required
@require_POST
def reservar_doacao(request, pk):
    """Reserva atômica para evitar condição de corrida entre dois recebedores."""
    with transaction.atomic():
        doacao = get_object_or_404(
            Doacao.objects.select_for_update(),
            pk=pk,
        )
        if doacao.doador_id == request.user.id:
            messages.error(request, "Você não pode reservar a própria doação.")
        elif doacao.status != Doacao.Status.DISPONIVEL:
            messages.error(request, "Esta doação não está mais disponível.")
        else:
            doacao.reservada_por = request.user
            doacao.status = Doacao.Status.RESERVADA
            doacao.save(update_fields=["reservada_por", "status", "atualizado_em"])
            messages.success(
                request,
                "Doação reservada! Acompanhe a retirada em Minhas coletas.",
            )
    return redirect("doacao_detalhe", pk=pk)


@login_required
def minhas_coletas(request):
    coletas = (
        request.user.doacoes_reservadas.exclude(status=Doacao.Status.CANCELADA)
        .select_related("doador", "doador__perfil_ifeed")
    )
    resumo = _contagem_por_status(
        coletas,
        Doacao.Status.RESERVADA,
        Doacao.Status.COLETADA,
        Doacao.Status.ENTREGUE,
    )
    # Mantém chaves esperadas pelos templates
    resumo = {
        "reservadas": resumo.get(Doacao.Status.RESERVADA, 0),
        "coletadas": resumo.get(Doacao.Status.COLETADA, 0),
        "entregues": resumo.get(Doacao.Status.ENTREGUE, 0),
        "total": resumo.get("total", 0),
    }
    selecionada = coletas.first()
    selecionada_id = request.GET.get("selecionada")
    if selecionada_id:
        selecionada = coletas.filter(pk=selecionada_id).first() or selecionada
    return render(
        request,
        "internal/minhas_coletas.html",
        {"coletas": coletas, "selecionada": selecionada, "resumo": resumo},
    )


@login_required
@require_POST
def atualizar_coleta(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk, reservada_por=request.user)
    transicoes = {
        Doacao.Status.RESERVADA: Doacao.Status.COLETADA,
        Doacao.Status.COLETADA: Doacao.Status.ENTREGUE,
    }
    proximo = transicoes.get(doacao.status)
    if proximo:
        doacao.status = proximo
        doacao.save(update_fields=["status", "atualizado_em"])
        messages.success(
            request,
            f"Coleta atualizada para {doacao.get_status_display()}.",
        )
    return redirect(f"{reverse('minhas_coletas')}?selecionada={doacao.pk}")


def _query_minhas_doacoes(extra=None, **overrides):
    """Monta querystring preservando filtros ativos da lista."""
    params = {}
    if extra:
        params.update({k: v for k, v in extra.items() if v not in (None, "")})
    params.update({k: v for k, v in overrides.items() if v not in (None, "")})
    return urlencode(params)


@login_required
def minhas_doacoes(request):
    base_qs = request.user.doacoes_criadas.select_related(
        "reservada_por",
        "reservada_por__perfil_ifeed",
    )

    resumo_raw = _contagem_por_status(
        base_qs,
        Doacao.Status.DISPONIVEL,
        Doacao.Status.RESERVADA,
        Doacao.Status.COLETADA,
        Doacao.Status.ENTREGUE,
    )
    resumo = {
        "total": resumo_raw.get("total", 0),
        "disponiveis": resumo_raw.get(Doacao.Status.DISPONIVEL, 0),
        "reservadas": resumo_raw.get(Doacao.Status.RESERVADA, 0),
        "coletadas": resumo_raw.get(Doacao.Status.COLETADA, 0),
        "entregues": resumo_raw.get(Doacao.Status.ENTREGUE, 0),
    }

    filtro = request.GET.get("status", "todas").strip().lower()
    if filtro not in STATUS_FILTRO_DOACOES:
        filtro = "todas"
    status_alvo = STATUS_FILTRO_DOACOES[filtro]

    busca = request.GET.get("q", "").strip()
    doacoes = base_qs
    if status_alvo:
        doacoes = doacoes.filter(status=status_alvo)
    if busca:
        doacoes = doacoes.filter(
            Q(nome_alimento__icontains=busca)
            | Q(categoria__icontains=busca)
            | Q(cidade__icontains=busca)
            | Q(descricao__icontains=busca)
        )

    paginator = Paginator(doacoes, DOACOES_POR_PAGINA)
    page_number = request.GET.get("page") or 1
    page = paginator.get_page(page_number)

    selecionada = page.object_list[0] if page.object_list else None
    selecionada_id = request.GET.get("selecionada")
    if selecionada_id:
        # Busca na lista completa do usuário para não perder o painel lateral
        # quando a doação estiver em outra página/filtro.
        selecionada = base_qs.filter(pk=selecionada_id).first() or selecionada

    query_base = {"status": filtro if filtro != "todas" else "", "q": busca}

    return render(
        request,
        "internal/minhas_doacoes.html",
        {
            "doacoes": page.object_list,
            "page_obj": page,
            "resumo": resumo,
            "selecionada": selecionada,
            "filtro_status": filtro,
            "busca": busca,
            "query_base": query_base,
            "status_tabs": [
                ("todas", "Todas", resumo["total"]),
                ("disponiveis", "Disponíveis", resumo["disponiveis"]),
                ("reservadas", "Reservadas", resumo["reservadas"]),
                ("coletadas", "Coletadas", resumo["coletadas"]),
                ("entregues", "Entregues", resumo["entregues"]),
            ],
        },
    )


@login_required
def doacao_criar(request):
    form = DoacaoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        doacao = form.save(commit=False)
        doacao.doador = request.user
        doacao.save()
        messages.success(request, "Doação publicada com sucesso!")
        return redirect("minhas_doacoes")
    return render(request, "internal/doacao_form.html", {"form": form, "editando": False})


@login_required
def doacao_editar(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk, doador=request.user)
    if not doacao.pode_ser_editada_por(request.user):
        messages.error(
            request,
            "Esta doação não pode ser editada no status atual.",
        )
        return redirect("minhas_doacoes")
    form = DoacaoForm(request.POST or None, request.FILES or None, instance=doacao)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doação atualizada com sucesso!")
        return redirect(f"{reverse('minhas_doacoes')}?selecionada={doacao.pk}")
    return render(
        request,
        "internal/doacao_form.html",
        {"form": form, "editando": True, "doacao": doacao},
    )


@login_required
@require_POST
def doacao_excluir(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk, doador=request.user)
    if not doacao.pode_ser_excluida():
        messages.error(request, "Uma doação em coleta não pode ser excluída.")
    else:
        doacao.delete()
        messages.success(request, "Doação excluída.")
    return redirect("minhas_doacoes")



@login_required
@require_POST
def doacao_cancelar(request, pk):
    """Cancela uma doação que ainda não entrou em coleta."""
    doacao = get_object_or_404(Doacao, pk=pk, doador=request.user)
    if doacao.status != Doacao.Status.DISPONIVEL:
        messages.error(
            request,
            "Só é possível cancelar doações disponíveis.",
        )
    else:
        doacao.status = Doacao.Status.CANCELADA
        doacao.reservada_por = None
        doacao.save(update_fields=["status", "reservada_por", "atualizado_em"])
        messages.success(request, "Doação cancelada.")
    return redirect("minhas_doacoes")


@login_required
def impacto(request):
    metricas = _metricas(request.user)
    return render(
        request,
        "internal/impacto.html",
        {
            "metricas": metricas,
            "impacto_chart": _grafico_impacto(metricas["alimentos_doados"]),
        },
    )


@login_required
def reconhecimentos(request):
    stats = request.user.doacoes_criadas.aggregate(
        total=Count("id"),
        concluidas=Count("id", filter=Q(status=Doacao.Status.ENTREGUE)),
    )
    concluidas = stats["concluidas"] or 0
    total = stats["total"] or 0
    pontos = concluidas * 100 + total * 50

    if concluidas >= 20:
        nivel = "Ouro"
        meta = 20
    elif concluidas >= 12:
        nivel = "Prata"
        meta = 20  # progresso em direção ao Ouro
    else:
        nivel = "Bronze"
        meta = 12  # progresso em direção à Prata

    progresso = min(100, int((concluidas / meta) * 100)) if meta else 0
    return render(
        request,
        "internal/reconhecimentos.html",
        {
            "concluidas": concluidas,
            "pontos": pontos,
            "nivel": nivel,
            "progresso": progresso,
        },
    )


@login_required
def perfil(request):
    perfil_obj = _perfil(request.user)
    form = PerfilForm(request.POST or None, instance=perfil_obj, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect("perfil")
    return render(request, "internal/perfil.html", {"form": form, "perfil": perfil_obj})


# Compatibilidade com o endpoint JSON criado no projeto do Pedro.
@login_required
def listar_doacoes(request):
    if request.method != "GET":
        return JsonResponse(
            {"status": "erro", "mensagem": "Use os formulários Django."},
            status=405,
        )
    dados = [
        {
            "id": doacao.id,
            "nome_alimento": doacao.nome_alimento,
            "quantidade": doacao.quantidade_formatada,
            "data_validade": doacao.data_validade.isoformat(),
            "status": doacao.status,
        }
        for doacao in Doacao.objects.filter(status=Doacao.Status.DISPONIVEL)
        .only("id", "nome_alimento", "quantidade", "unidade", "data_validade", "status")
    ]
    return JsonResponse({"status": "sucesso", "dados": dados})
