import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CadastroForm, DoacaoForm, LoginForm, PerfilForm
from .models import Doacao, Perfil

User = get_user_model()


def _perfil(user, **defaults):
    perfil, _ = Perfil.objects.get_or_create(user=user, defaults=defaults)
    return perfil


def _metricas(user):
    entregues = list(user.doacoes_criadas.filter(status="entregue"))
    doadas = sum((item.peso_estimado_kg for item in entregues), Decimal("0"))
    refeicoes = int(doadas * Decimal("2"))
    desperdicio = doadas * Decimal("0.68")
    instituicoes = len({item.reservada_por_id for item in entregues if item.reservada_por_id})
    return {
        "alimentos_doados": round(doadas, 1),
        "refeicoes": refeicoes,
        "desperdicio": round(desperdicio, 1),
        "doacoes_realizadas": len(entregues),
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
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
            "values": [210, 340, 480, 430, 650, 760, 710, 880, 1050, 990, 1290, 1250],
        },
        "all": {
            "labels": ["2024", "2025", "2026"],
            "values": [420, 870, 1250],
        },
    }


def home(request):
    doacoes = Doacao.objects.filter(status="disponivel").select_related("doador")[:3]
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

    perfil_inicial = request.GET.get("perfil", "doador")
    if perfil_inicial not in {"doador", "recebedor"}:
        perfil_inicial = "doador"
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
        Doacao.objects.filter(status="disponivel")
        .exclude(doador=request.user)
        .select_related("doador", "doador__perfil_ifeed")[:3]
    )
    recentes = request.user.doacoes_criadas.all()[:4]
    return render(
        request,
        "internal/painel.html",
        {"metricas": metricas, "proximas": proximas, "recentes": recentes},
    )



def _doacoes_disponiveis_queryset(request):
    """Compartilhado entre a página de busca e o endpoint JSON do mapa,
    pra garantir que os dois sempre mostrem exatamente a mesma coisa."""
    busca = request.GET.get("q", "").strip()
    doacoes = (
        Doacao.objects.filter(status="disponivel")
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
    """Endpoint  dedicado ao mapa"""
    doacoes, _ = _doacoes_disponiveis_queryset(request)
    doacoes = doacoes.filter(latitude__isnull=False, longitude__isnull=False)
    dados = []
    for doacao in doacoes:
        perfil = getattr(doacao.doador, "perfil_ifeed", None)
        organizacao = (perfil.organizacao if perfil else "") or doacao.doador.get_full_name()
        dados.append({
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
        })
    return JsonResponse({"doacoes": dados})

@login_required
def doacao_detalhe(request, pk):
    doacao = get_object_or_404(
        Doacao.objects.select_related("doador", "doador__perfil_ifeed"),
        pk=pk,
    )
    return render(request, "internal/doacao_detalhe.html", {"doacao": doacao})


@login_required
@require_POST
def reservar_doacao(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk)
    if doacao.doador_id == request.user.id:
        messages.error(request, "Você não pode reservar a própria doação.")
    elif doacao.status != "disponivel":
        messages.error(request, "Esta doação não está mais disponível.")
    else:
        doacao.reservada_por = request.user
        doacao.status = "reservada"
        doacao.save(update_fields=["reservada_por", "status", "atualizado_em"])
        messages.success(request, "Doação reservada! Acompanhe a retirada em Minhas coletas.")
    return redirect("doacao_detalhe", pk=pk)


@login_required
def minhas_coletas(request):
    coletas = request.user.doacoes_reservadas.exclude(status="cancelada").select_related(
        "doador", "doador__perfil_ifeed"
    )
    selecionada = coletas.first()
    selecionada_id = request.GET.get("selecionada")
    if selecionada_id:
        selecionada = coletas.filter(pk=selecionada_id).first() or selecionada
    resumo = {
        "reservadas": coletas.filter(status="reservada").count(),
        "coletadas": coletas.filter(status="coletada").count(),
        "entregues": coletas.filter(status="entregue").count(),
        "total": coletas.count(),
    }
    return render(
        request,
        "internal/minhas_coletas.html",
        {"coletas": coletas, "selecionada": selecionada, "resumo": resumo},
    )


@login_required
@require_POST
def atualizar_coleta(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk, reservada_por=request.user)
    proximo = {"reservada": "coletada", "coletada": "entregue"}.get(doacao.status)
    if proximo:
        doacao.status = proximo
        doacao.save(update_fields=["status", "atualizado_em"])
        messages.success(request, f"Coleta atualizada para {doacao.get_status_display()}.")
    return redirect(f"{reverse('minhas_coletas')}?selecionada={doacao.pk}")


@login_required
def minhas_doacoes(request):
    doacoes = request.user.doacoes_criadas.select_related("reservada_por")
    resumo = {
        "total": doacoes.count(),
        "disponiveis": doacoes.filter(status="disponivel").count(),
        "reservadas": doacoes.filter(status="reservada").count(),
        "entregues": doacoes.filter(status="entregue").count(),
    }
    selecionada = doacoes.first()
    selecionada_id = request.GET.get("selecionada")
    if selecionada_id:
        selecionada = doacoes.filter(pk=selecionada_id).first() or selecionada
    return render(
        request,
        "internal/minhas_doacoes.html",
        {"doacoes": doacoes, "resumo": resumo, "selecionada": selecionada},
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
    form = DoacaoForm(request.POST or None, request.FILES or None, instance=doacao)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doação atualizada com sucesso!")
        return redirect("minhas_doacoes")
    return render(
        request,
        "internal/doacao_form.html",
        {"form": form, "editando": True, "doacao": doacao},
    )


@login_required
@require_POST
def doacao_excluir(request, pk):
    doacao = get_object_or_404(Doacao, pk=pk, doador=request.user)
    if doacao.status in {"reservada", "coletada"}:
        messages.error(request, "Uma doação em coleta não pode ser excluída.")
    else:
        doacao.delete()
        messages.success(request, "Doação excluída.")
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
    concluidas = request.user.doacoes_criadas.filter(status="entregue").count()
    pontos = concluidas * 100 + request.user.doacoes_criadas.count() * 50
    nivel = "Ouro" if concluidas >= 20 else "Prata" if concluidas >= 12 else "Bronze"
    progresso = min(100, int((concluidas / (20 if nivel == "Prata" else 12)) * 100))
    return render(
        request,
        "internal/reconhecimentos.html",
        {"concluidas": concluidas, "pontos": pontos, "nivel": nivel, "progresso": progresso},
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
    if request.method == "GET":
        dados = [
            {
                "id": doacao.id,
                "nome_alimento": doacao.nome_alimento,
                "quantidade": doacao.quantidade_formatada,
                "data_validade": doacao.data_validade.isoformat(),
                "status": doacao.status,
            }
            for doacao in Doacao.objects.filter(status="disponivel")
        ]
        return JsonResponse({"status": "sucesso", "dados": dados})
    return JsonResponse({"status": "erro", "mensagem": "Use os formulários Django."}, status=405)
