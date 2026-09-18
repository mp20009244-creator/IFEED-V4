from django.contrib import admin

from .models import Doacao, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "tipo", "organizacao", "cidade", "estado")
    list_filter = ("tipo", "estado")
    search_fields = ("user__email", "user__first_name", "organizacao")


@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_alimento",
        "doador",
        "quantidade",
        "unidade",
        "data_validade",
        "status",
    )
    list_filter = ("status", "categoria", "tipo_armazenamento")
    search_fields = ("nome_alimento", "doador__email", "cidade")
    readonly_fields = ("criado_em", "atualizado_em")
