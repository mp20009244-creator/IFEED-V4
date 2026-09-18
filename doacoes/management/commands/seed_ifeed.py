from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from doacoes.models import Doacao, Perfil

User = get_user_model()


class Command(BaseCommand):
    help = "Cria usuários e doações demonstrativas do iFeed."

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        demo, criado = User.objects.get_or_create(
            username="demo@ifeed.com",
            defaults={
                "email": "demo@ifeed.com",
                "first_name": "Carlos",
                "last_name": "Almeida",
            },
        )
        if criado or not demo.has_usable_password():
            demo.set_password("Ifeed@2026")
            demo.save()
        Perfil.objects.update_or_create(
            user=demo,
            defaults={
                "tipo": "doador",
                "organizacao": "Padaria Boa Massa",
                "tipo_organizacao": "Padaria",
                "telefone": "(61) 99999-1234",
                "funcao": "Responsável pelas doações",
                "cep": "70040-010",
                "logradouro": "Rua das Flores",
                "numero": "123",
                "complemento": "Loja 02",
                "bairro": "Asa Sul",
                "cidade": "Brasília",
                "estado": "DF",
                "descricao": "Produção artesanal de pães e alimentos frescos.",
            },
        )

        recebedor, _ = User.objects.get_or_create(
            username="ong@ifeed.com",
            defaults={"email": "ong@ifeed.com", "first_name": "Ana", "last_name": "Souza"},
        )
        recebedor.set_password("Ifeed@2026")
        recebedor.save()
        Perfil.objects.update_or_create(
            user=recebedor,
            defaults={"tipo": "recebedor", "organizacao": "ONG Prato Cheio", "cidade": "Brasília", "estado": "DF"},
        )

        parceiros = []
        for indice, (email, nome, org, cidade) in enumerate(
            [
                ("aurora@ifeed.com", "Marina Aurora", "Padaria Aurora", "São Paulo"),
                ("verdevida@ifeed.com", "Paulo Verde", "Hortifruti Verde Vida", "São Paulo"),
                ("bompreco@ifeed.com", "Bianca Lima", "Mercado Bom Preço", "São Paulo"),
                ("sabordodia@ifeed.com", "Rafael Dias", "Restaurante Sabor do Dia", "São Paulo"),
            ]
        ):
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": nome.split()[0], "last_name": " ".join(nome.split()[1:])},
            )
            user.set_password("Ifeed@2026")
            user.save()
            Perfil.objects.update_or_create(
                user=user,
                defaults={"tipo": "doador", "organizacao": org, "cidade": cidade, "estado": "SP", "telefone": f"(11) 9999{indice}-0000"},
            )
            parceiros.append(user)

        base = {
            "horario_inicio": time(14, 0),
            "horario_fim": time(18, 0),
            "cep": "05402-000",
            "logradouro": "Rua das Flores",
            "numero": "123",
            "bairro": "Pinheiros",
            "cidade": "São Paulo",
            "estado": "SP",
            "tipo_armazenamento": "ambiente",
        }

        externos = [
            (parceiros[0], "Pães artesanais", "paes", 18, "kg", 5, "food-bread.png"),
            (parceiros[1], "Legumes variados", "verduras", 32, "kg", 4, "food-vegetables.png"),
            (parceiros[2], "Frutas da estação", "frutas", 45, "kg", 6, "food-fruits.png"),
            (parceiros[3], "Marmitas prontas", "refeicoes", 24, "unidades", 3, "food-meals.png"),
        ]
        for indice, (doador, nome, categoria, qtd, unidade, dias, foto) in enumerate(externos):
            Doacao.objects.update_or_create(
                doador=doador,
                nome_alimento=nome,
                defaults={
                    **base,
                    "categoria": categoria,
                    "quantidade": Decimal(str(qtd)),
                    "unidade": unidade,
                    "data_validade": hoje + timedelta(days=dias),
                    "foto_padrao": foto,
                    "descricao": "Alimentos frescos, selecionados e em perfeito estado para consumo.",
                    "status": "disponivel",
                    "reservada_por": None,
                },
            )

        proprias = [
            ("Pães variados", "paes", 50, "unidades", "disponivel", "food-bread.png"),
            ("Frutas variadas", "frutas", 15, "kg", "reservada", "food-fruits.png"),
            ("Marmitas prontas", "refeicoes", 30, "unidades", "coletada", "food-meals.png"),
            ("Verduras variadas", "verduras", 10, "kg", "entregue", "food-vegetables.png"),
            ("Leite integral", "laticinios", 18, "litros", "disponivel", "food-milk.png"),
        ]
        for indice, (nome, categoria, qtd, unidade, status, foto) in enumerate(proprias):
            Doacao.objects.update_or_create(
                doador=demo,
                nome_alimento=nome,
                defaults={
                    **base,
                    "categoria": categoria,
                    "quantidade": Decimal(str(qtd)),
                    "unidade": unidade,
                    "data_validade": hoje + timedelta(days=indice + 2),
                    "foto_padrao": foto,
                    "descricao": "Doação demonstrativa cadastrada pela Padaria Boa Massa.",
                    "status": status,
                    "reservada_por": recebedor if status in {"reservada", "coletada", "entregue"} else None,
                },
            )

        # Histórico concluído para alimentar gráficos, impacto e selo Prata.
        for indice in range(1, 12):
            Doacao.objects.update_or_create(
                doador=demo,
                nome_alimento=f"Doação concluída {indice:02d}",
                defaults={
                    **base,
                    "categoria": "paes" if indice % 2 else "verduras",
                    # As 11 entregas históricas + a entrega de 10 kg acima
                    # totalizam 1.250 kg, mantendo os indicadores coerentes
                    # com a concept art aprovada.
                    "quantidade": Decimal(str(88 + indice * 4 + (8 if indice == 11 else 0))),
                    "unidade": "kg",
                    "data_validade": hoje + timedelta(days=10 + indice),
                    "foto_padrao": "food-bread.png" if indice % 2 else "food-vegetables.png",
                    "descricao": "Registro demonstrativo de entrega concluída.",
                    "status": "entregue",
                    "reservada_por": recebedor,
                },
            )

        # Duas reservas de outros estabelecimentos aparecem em Minhas coletas.
        for indice, doacao in enumerate(Doacao.objects.filter(doador__in=parceiros)[:2]):
            doacao.reservada_por = demo
            doacao.status = "reservada" if indice == 0 else "coletada"
            doacao.save(update_fields=["reservada_por", "status"])

        self.stdout.write(self.style.SUCCESS("Dados demonstrativos criados com sucesso."))
        self.stdout.write("Login: demo@ifeed.com | Senha: Ifeed@2026")
