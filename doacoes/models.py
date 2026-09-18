from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

class Perfil(models.Model):
    """Informações complementares da conta Django."""

    TIPO_CHOICES = [
        ("doador", "Quero doar"),
        ("recebedor", "Quero receber"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_ifeed",
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="doador")
    organizacao = models.CharField(max_length=160, blank=True)
    tipo_organizacao = models.CharField(max_length=80, blank=True)
    documento = models.CharField(max_length=30, blank=True)
    telefone = models.CharField(max_length=25, blank=True)
    funcao = models.CharField(max_length=100, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=180, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    descricao = models.TextField(blank=True)
    foto_url = models.URLField(blank=True)
    avisos_reservas = models.BooleanField(default=True)
    lembretes_coleta = models.BooleanField(default=True)
    resumo_impacto = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organizacao or self.user.get_full_name() or self.user.username


class Doacao(models.Model):
    """Doação criada por um usuário e acompanhada até a entrega."""

    STATUS_CHOICES = [
        ("disponivel", "Disponível"),
        ("reservada", "Reservada"),
        ("coletada", "Coletada"),
        ("a_caminho", "A caminho"),
        ("entregue", "Entregue"),
        ("pausada", "Pausada"),
        ("cancelada", "Cancelada"),
    ]
    CATEGORIA_CHOICES = [
        ("paes", "Pães e massas"),
        ("frutas", "Frutas"),
        ("verduras", "Verduras e legumes"),
        ("refeicoes", "Refeições prontas"),
        ("laticinios", "Laticínios"),
        ("mercearia", "Mercearia"),
        ("outros", "Outros"),
    ]
    UNIDADE_CHOICES = [
        ("kg", "kg"),
        ("unidades", "unidades"),
        ("litros", "litros"),
        ("porcoes", "porções"),
        ("caixas", "caixas"),
    ]
    ARMAZENAMENTO_CHOICES = [
        ("ambiente", "Temperatura ambiente"),
        ("refrigerado", "Refrigerado"),
        ("congelado", "Congelado"),
    ]

    doador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doacoes_criadas",
    )
    reservada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="doacoes_reservadas",
        blank=True,
        null=True,
    )
    nome_alimento = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=20, choices=UNIDADE_CHOICES, default="kg")
    data_validade = models.DateField()
    foto = models.FileField(upload_to="doacoes_fotos/", blank=True)
    foto_padrao = models.CharField(max_length=120, blank=True)
    tipo_armazenamento = models.CharField(
        max_length=20,
        choices=ARMAZENAMENTO_CHOICES,
        default="ambiente",
    )
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()
    descricao = models.TextField(blank=True)
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=180)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="disponivel")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_validade", "-criado_em"]
        verbose_name = "Doação"
        verbose_name_plural = "Doações"

    def __str__(self):
        return f"{self.nome_alimento} — {self.get_status_display()}"

    def get_absolute_url(self):
        return reverse("doacao_detalhe", kwargs={"pk": self.pk})

    @property
    def quantidade_formatada(self):
        valor = self.quantidade
        if valor == valor.to_integral():
            valor = int(valor)
        return f"{valor} {self.get_unidade_display()}"

    @property
    def endereco_resumido(self):
        return f"{self.logradouro}, {self.numero} · {self.cidade} — {self.estado}"

    @property
    def foto_url(self):
        if self.foto:
            return self.foto.url
        nome = self.foto_padrao or {
            "paes": "food-bread.png",
            "frutas": "food-fruits.png",
            "verduras": "food-vegetables.png",
            "refeicoes": "food-meals.png",
            "laticinios": "food-milk.png",
        }.get(self.categoria, "hero-food-box.png")
        return f"/static/assets/img/{nome}"

    @property
    def peso_estimado_kg(self):
        if self.unidade == "kg":
            return self.quantidade
        if self.unidade == "litros":
            return self.quantidade
        return self.quantidade * Decimal("0.40")
    
    @property
    def esta_urgente(self):
        if self.status not in ("disponivel", "reservada"):
            return False
        limite = datetime.combine(date.today(), self.horario_fim) - timedelta(minutes=90)
        agora = datetime.combine(date.today(), timezone.localtime().time())
        return agora >= limite

    @property
    def tem_localizacao(self):
        return self.latitude is not None and self.longitude is not None
