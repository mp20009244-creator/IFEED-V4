from django.urls import reverse
from django.utils import timezone

from .models import Doacao


def perfil_ifeed(request):
    """Disponibiliza o perfil do usuário em todos os templates internos."""
    if not request.user.is_authenticated:
        return {"perfil_ifeed": None, "notificacoes": [], "notificacoes_count": 0}

    perfil = getattr(request.user, "perfil_ifeed", None)
    notificacoes = _montar_notificacoes(request.user)
    return {
        "perfil_ifeed": perfil,
        "notificacoes": notificacoes,
        "notificacoes_count": len(notificacoes),
    }


def _montar_notificacoes(user):
    """Gera avisos úteis a partir do estado atual das doações do usuário."""
    itens = []
    agora = timezone.localtime()

    # Doações do usuário que foram reservadas recentemente
    reservadas = (
        user.doacoes_criadas.filter(status=Doacao.Status.RESERVADA)
        .select_related("reservada_por", "reservada_por__perfil_ifeed")
        .order_by("-atualizado_em")[:5]
    )
    for doacao in reservadas:
        org = ""
        if doacao.reservada_por:
            perfil = getattr(doacao.reservada_por, "perfil_ifeed", None)
            org = (perfil.organizacao if perfil else "") or doacao.reservada_por.get_full_name()
        itens.append(
            {
                "titulo": "Doação reservada",
                "texto": f"“{doacao.nome_alimento}” foi reservada"
                + (f" por {org}" if org else "")
                + ".",
                "url": f"{reverse('minhas_doacoes')}?selecionada={doacao.pk}",
                "quando": doacao.atualizado_em,
            }
        )

    # Coletas do usuário aguardando ação
    coletas = (
        user.doacoes_reservadas.filter(
            status__in=[Doacao.Status.RESERVADA, Doacao.Status.COLETADA]
        )
        .select_related("doador", "doador__perfil_ifeed")
        .order_by("-atualizado_em")[:5]
    )
    for doacao in coletas:
        if doacao.status == Doacao.Status.RESERVADA:
            titulo = "Coleta pendente"
            texto = f"Confirme a retirada de “{doacao.nome_alimento}”."
        else:
            titulo = "Entrega pendente"
            texto = f"Confirme a entrega de “{doacao.nome_alimento}”."
        itens.append(
            {
                "titulo": titulo,
                "texto": texto,
                "url": f"{reverse('minhas_coletas')}?selecionada={doacao.pk}",
                "quando": doacao.atualizado_em,
            }
        )

    # Doações disponíveis próximas do vencimento (urgentes) que não são do usuário
    urgentes = (
        Doacao.objects.filter(status=Doacao.Status.DISPONIVEL)
        .exclude(doador=user)
        .order_by("data_validade", "horario_fim")[:8]
    )
    for doacao in urgentes:
        if not doacao.esta_urgente:
            continue
        itens.append(
            {
                "titulo": "Doação urgente",
                "texto": f"“{doacao.nome_alimento}” em {doacao.cidade} vence em breve.",
                "url": reverse("doacao_detalhe", kwargs={"pk": doacao.pk}),
                "quando": agora,
            }
        )
        if len([i for i in itens if i["titulo"] == "Doação urgente"]) >= 2:
            break

    # Ordena por data (mais recente primeiro) e limita
    itens.sort(key=lambda item: item["quando"] or agora, reverse=True)
    return itens[:8]
