from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Perfil",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("doador", "Quero doar"), ("recebedor", "Quero receber")], default="doador", max_length=20)),
                ("organizacao", models.CharField(blank=True, max_length=160)),
                ("tipo_organizacao", models.CharField(blank=True, max_length=80)),
                ("documento", models.CharField(blank=True, max_length=30)),
                ("telefone", models.CharField(blank=True, max_length=25)),
                ("funcao", models.CharField(blank=True, max_length=100)),
                ("cep", models.CharField(blank=True, max_length=9)),
                ("logradouro", models.CharField(blank=True, max_length=180)),
                ("numero", models.CharField(blank=True, max_length=20)),
                ("complemento", models.CharField(blank=True, max_length=100)),
                ("bairro", models.CharField(blank=True, max_length=100)),
                ("cidade", models.CharField(blank=True, max_length=100)),
                ("estado", models.CharField(blank=True, max_length=2)),
                ("descricao", models.TextField(blank=True)),
                ("foto_url", models.URLField(blank=True)),
                ("avisos_reservas", models.BooleanField(default=True)),
                ("lembretes_coleta", models.BooleanField(default=True)),
                ("resumo_impacto", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_ifeed", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Doacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_alimento", models.CharField(max_length=150)),
                ("categoria", models.CharField(choices=[("paes", "Pães e massas"), ("frutas", "Frutas"), ("verduras", "Verduras e legumes"), ("refeicoes", "Refeições prontas"), ("laticinios", "Laticínios"), ("mercearia", "Mercearia"), ("outros", "Outros")], max_length=20)),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=10)),
                ("unidade", models.CharField(choices=[("kg", "kg"), ("unidades", "unidades"), ("litros", "litros"), ("porcoes", "porções"), ("caixas", "caixas")], default="kg", max_length=20)),
                ("data_validade", models.DateField()),
                ("foto", models.FileField(blank=True, upload_to="doacoes_fotos/")),
                ("foto_padrao", models.CharField(blank=True, max_length=120)),
                ("tipo_armazenamento", models.CharField(choices=[("ambiente", "Temperatura ambiente"), ("refrigerado", "Refrigerado"), ("congelado", "Congelado")], default="ambiente", max_length=20)),
                ("horario_inicio", models.TimeField()),
                ("horario_fim", models.TimeField()),
                ("descricao", models.TextField(blank=True)),
                ("cep", models.CharField(max_length=9)),
                ("logradouro", models.CharField(max_length=180)),
                ("numero", models.CharField(max_length=20)),
                ("complemento", models.CharField(blank=True, max_length=100)),
                ("bairro", models.CharField(blank=True, max_length=100)),
                ("cidade", models.CharField(max_length=100)),
                ("estado", models.CharField(max_length=2)),
                ("status", models.CharField(choices=[("disponivel", "Disponível"), ("reservada", "Reservada"), ("coletada", "Coletada"), ("entregue", "Entregue"), ("pausada", "Pausada"), ("cancelada", "Cancelada")], default="disponivel", max_length=20)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("doador", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="doacoes_criadas", to=settings.AUTH_USER_MODEL)),
                ("reservada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doacoes_reservadas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Doação", "verbose_name_plural": "Doações", "ordering": ["data_validade", "-criado_em"]},
        ),
    ]
