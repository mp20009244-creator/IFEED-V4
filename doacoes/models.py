from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Perfil(models.Model):
    """Informações complementares da conta Django."""

    class Tipo(models.TextChoices):
        DOADOR = "doador", "Quero doar"
        RECEBEDOR = "recebedor", "Quero receber"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_ifeed",
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.DOADOR,
    )
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

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return self.organizacao or self.user.get_full_name() or self.user.username


class Doacao(models.Model):
    """Doação criada por um usuário e acompanhada até a entrega."""

    class Status(models.TextChoices):
        DISPONIVEL = "disponivel", "Disponível"
        RESERVADA = "reservada", "Reservada"
        COLETADA = "coletada", "Coletada"
        A_CAMINHO = "a_caminho", "A caminho"
        ENTREGUE = "entregue", "Entregue"
        PAUSADA = "pausada", "Pausada"
        CANCELADA = "cancelada", "Cancelada"

    class Categoria(models.TextChoices):
        PAES = "paes", "Pães e massas"
        FRUTAS = "frutas", "Frutas"
        VERDURAS = "verduras", "Verduras e legumes"
        REFEICOES = "refeicoes", "Refeições prontas"
        LATICINIOS = "laticinios", "Laticínios"
        MERCEARIA = "mercearia", "Mercearia"
        OUTROS = "outros", "Outros"

    class Unidade(models.TextChoices):
        KG = "kg", "kg"
        UNIDADES = "unidades", "unidades"
        LITROS = "litros", "litros"
        PORCOES = "porcoes", "porções"
        CAIXAS = "caixas", "caixas"

    class Armazenamento(models.TextChoices):
        AMBIENTE = "ambiente", "Temperatura ambiente"
        REFRIGERADO = "refrigerado", "Refrigerado"
        CONGELADO = "congelado", "Congelado"

    FOTO_PADRAO_POR_CATEGORIA = {
        Categoria.PAES: "food-bread.png",
        Categoria.FRUTAS: "food-fruits.png",
        Categoria.VERDURAS: "food-vegetables.png",
        Categoria.REFEICOES: "food-meals.png",
        Categoria.LATICINIOS: "food-milk.png",
    }

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
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unidade = models.CharField(
        max_length=20,
        choices=Unidade.choices,
        default=Unidade.KG,
    )
    data_validade = models.DateField()
    foto = models.ImageField(upload_to="doacoes_fotos/", blank=True)
    foto_padrao = models.CharField(max_length=120, blank=True)
    tipo_armazenamento = models.CharField(
        max_length=20,
        choices=Armazenamento.choices,
        default=Armazenamento.AMBIENTE,
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
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISPONIVEL,
        db_index=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_validade", "-criado_em"]
        verbose_name = "Doação"
        verbose_name_plural = "Doações"
        indexes = [
            models.Index(fields=["status", "data_validade"]),
            models.Index(fields=["doador", "status"]),
            models.Index(fields=["reservada_por", "status"]),
        ]

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
        nome = self.foto_padrao or self.FOTO_PADRAO_POR_CATEGORIA.get(
            self.categoria,
            "hero-food-box.png",
        )
        return f"/static/assets/img/{nome}"

    @property
    def peso_estimado_kg(self):
        if self.unidade in (self.Unidade.KG, self.Unidade.LITROS):
            return self.quantidade
        return self.quantidade * Decimal("0.40")

    @property
    def esta_urgente(self):
        """Indica prioridade de retirada por validade próxima.

        Critérios (alinhados a práticas de bancos de alimentos):
        - só para doações ainda disponíveis ou reservadas;
        - validade já passou, é hoje ou é amanhã;
        - se a validade é hoje, reforça urgência quando faltam até 2h
          para o fim da janela de retirada.
        """
        if self.status not in (self.Status.DISPONIVEL, self.Status.RESERVADA):
            return False

        hoje = timezone.localdate()
        if self.data_validade < hoje:
            return True
        if self.data_validade > hoje + timedelta(days=1):
            return False

        # Validade amanhã: urgente, mas sem depender do horário de hoje.
        if self.data_validade == hoje + timedelta(days=1):
            return True

        # Validade hoje: sempre prioritária; destaca ainda mais perto do fim.
        agora = timezone.localtime()
        fim_retirada = timezone.make_aware(
            datetime.combine(hoje, self.horario_fim),
            timezone.get_current_timezone(),
        )
        # Já passou do horário ou está na janela final de 2 horas.
        return agora >= (fim_retirada - timedelta(hours=2))

    @property
    def tem_localizacao(self):
        return self.latitude is not None and self.longitude is not None

    def pode_ser_editada_por(self, user):
        return self.doador_id == user.id and self.status == self.Status.DISPONIVEL

    def pode_ser_excluida(self):
        return self.status not in {
            self.Status.RESERVADA,
            self.Status.COLETADA,
            self.Status.A_CAMINHO,
        }
