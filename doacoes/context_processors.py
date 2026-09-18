def perfil_ifeed(request):
    """Disponibiliza o perfil do usuário em todos os templates internos."""
    if not request.user.is_authenticated:
        return {"perfil_ifeed": None}

    perfil = getattr(request.user, "perfil_ifeed", None)
    return {"perfil_ifeed": perfil}
