from django.contrib import admin

from .models import Doacao, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "tipo", "organizacao", "cidade", "estado", "criado_em")
    list_filter = ("tipo", "estado")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "organizacao",
        "telefone",
    )
    readonly_fields = ("criado_em",)
    ordering = ("-criado_em",)


@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_alimento",
        "doador",
        "quantidade",
        "unidade",
        "data_validade",
        "status",
        "cidade",
        "criado_em",
    )
    list_filter = ("status", "categoria", "tipo_armazenamento", "estado")
    search_fields = (
        "nome_alimento",
        "doador__email",
        "doador__first_name",
        "cidade",
        "bairro",
    )
    readonly_fields = ("criado_em", "atualizado_em")
    list_select_related = ("doador", "reservada_por")
    date_hierarchy = "data_validade"
    ordering = ("-criado_em",)
