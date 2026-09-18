from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Doacao, Perfil

User = get_user_model()


class IFeedFlowTests(TestCase):
    def setUp(self):
        self.doador = User.objects.create_user(
            username="doador@teste.com",
            email="doador@teste.com",
            password="Teste@12345",
            first_name="Doador",
        )
        Perfil.objects.create(user=self.doador, tipo="doador", organizacao="Padaria Teste")
        self.recebedor = User.objects.create_user(
            username="ong@teste.com",
            email="ong@teste.com",
            password="Teste@12345",
            first_name="ONG",
        )
        Perfil.objects.create(user=self.recebedor, tipo="recebedor", organizacao="ONG Teste")
        self.doacao = Doacao.objects.create(
            doador=self.doador,
            nome_alimento="Pães artesanais",
            categoria="paes",
            quantidade=10,
            unidade="kg",
            data_validade=date.today() + timedelta(days=2),
            tipo_armazenamento="ambiente",
            horario_inicio=time(14),
            horario_fim=time(18),
            cep="70000-000",
            logradouro="Rua Teste",
            numero="10",
            cidade="Brasília",
            estado="DF",
        )

    def test_paginas_publicas(self):
        for nome in ("home", "como_funciona", "impacto_publico", "quem_somos", "login", "cadastro"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_cadastro_cria_usuario_e_perfil(self):
        response = self.client.post(
            reverse("cadastro"),
            {
                "tipo": "doador",
                "nome": "Maria Silva",
                "email": "maria@teste.com",
                "organizacao": "Mercado Maria",
                "telefone": "(61) 99999-0000",
                "cep": "70000-100",
                "cidade": "Brasília",
                "aceite_termos": "on",
                "password1": "SenhaSegura@2026",
                "password2": "SenhaSegura@2026",
            },
        )
        self.assertRedirects(response, reverse("painel"))
        user = User.objects.get(email="maria@teste.com")
        self.assertEqual(user.perfil_ifeed.organizacao, "Mercado Maria")

    def test_login_por_email(self):
        response = self.client.post(reverse("login"), {"identificador": "doador@teste.com", "senha": "Teste@12345"})
        self.assertRedirects(response, reverse("painel"))

    def test_area_interna_exige_login(self):
        response = self.client.get(reverse("painel"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_reserva_de_doacao(self):
        self.client.force_login(self.recebedor)
        response = self.client.post(reverse("reservar_doacao", args=[self.doacao.pk]))
        self.assertRedirects(response, reverse("doacao_detalhe", args=[self.doacao.pk]))
        self.doacao.refresh_from_db()
        self.assertEqual(self.doacao.status, "reservada")
        self.assertEqual(self.doacao.reservada_por, self.recebedor)

    def test_paginas_internas_renderizam(self):
        self.client.force_login(self.doador)
        paginas = (
            "painel",
            "doacoes_disponiveis",
            "minhas_coletas",
            "minhas_doacoes",
            "doacao_criar",
            "impacto",
            "reconhecimentos",
            "perfil",
        )
        for nome in paginas:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_grafico_de_impacto_tem_tres_periodos_interativos(self):
        self.client.force_login(self.doador)
        response = self.client.get(reverse("impacto"))
        self.assertContains(response, 'id="impact-chart-data"')
        self.assertContains(response, 'data-chart-period="month"')
        self.assertContains(response, 'data-chart-period="quarter"')
        self.assertContains(response, 'data-chart-period="year"')

    def test_grafico_publico_e_icones_das_concept_arts(self):
        response = self.client.get(reverse("impacto_publico"))
        self.assertContains(response, 'id="public-impact-chart-data"')
        self.assertContains(response, 'data-chart-period="semester"')
        self.assertContains(response, "assets/icons/concept/env-reduce.png")
        self.assertContains(response, "assets/icons/concept/calc-history.png")

    def test_selo_prata_usa_png_completo(self):
        self.client.force_login(self.doador)
        response = self.client.get(reverse("reconhecimentos"))
        self.assertContains(response, "assets/img/badge-silver.png", count=2)

    def test_doador_cadastra_nova_doacao(self):
        self.client.force_login(self.doador)
        response = self.client.post(
            reverse("doacao_criar"),
            {
                "nome_alimento": "Legumes frescos",
                "categoria": "verduras",
                "quantidade": "20",
                "unidade": "kg",
                "data_validade": (date.today() + timedelta(days=3)).isoformat(),
                "tipo_armazenamento": "ambiente",
                "horario_inicio": "09:00",
                "horario_fim": "12:00",
                "descricao": "Produtos próprios para consumo.",
                "cep": "70000-000",
                "logradouro": "Rua Nova",
                "numero": "20",
                "complemento": "",
                "bairro": "Centro",
                "cidade": "Brasília",
                "estado": "DF",
                "alimento_proprio": "on",
            },
        )
        self.assertRedirects(response, reverse("minhas_doacoes"))
        self.assertTrue(Doacao.objects.filter(doador=self.doador, nome_alimento="Legumes frescos").exists())
