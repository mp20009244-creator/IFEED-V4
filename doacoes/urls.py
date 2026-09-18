from django.urls import path

from . import views

urlpatterns = [
    # Páginas públicas
    path("", views.home, name="home"),
    path("como-funciona/", views.como_funciona, name="como_funciona"),
    path("impacto-social/", views.impacto_publico, name="impacto_publico"),
    path("quem-somos/", views.quem_somos, name="quem_somos"),

    # Contas
    path("entrar/", views.login_view, name="login"),
    path("cadastro/", views.cadastro_view, name="cadastro"),
    path("sair/", views.encerrar_sessao, name="logout"),

    # Área interna
    path("painel/", views.painel, name="painel"),
    path("doacoes-disponiveis/", views.doacoes_disponiveis, name="doacoes_disponiveis"),
    path("doacoes-disponiveis/dados/", views.mapa_doacoes_dados, name="mapa_doacoes_dados"),
    path("doacoes/<int:pk>/", views.doacao_detalhe, name="doacao_detalhe"),
    path("doacoes/<int:pk>/reservar/", views.reservar_doacao, name="reservar_doacao"),
    path("minhas-coletas/", views.minhas_coletas, name="minhas_coletas"),
    path("minhas-coletas/<int:pk>/atualizar/", views.atualizar_coleta, name="atualizar_coleta"),
    path("minhas-doacoes/", views.minhas_doacoes, name="minhas_doacoes"),
    path("minhas-doacoes/nova/", views.doacao_criar, name="doacao_criar"),
    path("minhas-doacoes/<int:pk>/editar/", views.doacao_editar, name="doacao_editar"),
    path("minhas-doacoes/<int:pk>/excluir/", views.doacao_excluir, name="doacao_excluir"),
    path("meu-impacto/", views.impacto, name="impacto"),
    path("reconhecimentos/", views.reconhecimentos, name="reconhecimentos"),
    path("perfil/", views.perfil, name="perfil"),

    # Endpoint legado compatível com o código do Pedro
    path("api/doacoes/", views.listar_doacoes, name="api_doacoes"),
]
