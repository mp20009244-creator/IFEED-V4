from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Doacao, Perfil

User = get_user_model()


class LoginForm(forms.Form):
    identificador = forms.CharField(label="E-mail ou usuário")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user_cache = None
        self.fields["identificador"].widget.attrs.update(
            {"placeholder": "seuemail@exemplo.com", "autocomplete": "username"}
        )
        self.fields["senha"].widget.attrs.update(
            {"placeholder": "Digite sua senha", "autocomplete": "current-password"}
        )

    def clean(self):
        dados = super().clean()
        identificador = dados.get("identificador", "").strip()
        senha = dados.get("senha")
        username = identificador

        if "@" in identificador:
            encontrado = User.objects.filter(email__iexact=identificador).first()
            if encontrado:
                username = encontrado.username

        self.user_cache = authenticate(
            self.request,
            username=username,
            password=senha,
        )
        if self.user_cache is None:
            raise forms.ValidationError("E-mail/usuário ou senha incorretos.")
        if not self.user_cache.is_active:
            raise forms.ValidationError("Esta conta está desativada.")
        return dados

    def get_user(self):
        return self.user_cache


class CadastroForm(UserCreationForm):
    tipo = forms.ChoiceField(label="Como você quer participar?", choices=Perfil.TIPO_CHOICES)
    nome = forms.CharField(label="Nome completo", max_length=150)
    email = forms.EmailField(label="E-mail")
    organizacao = forms.CharField(label="Nome da organização", max_length=160, required=False)
    telefone = forms.CharField(label="Telefone", max_length=25, required=False)
    cep = forms.CharField(label="CEP", max_length=9, required=False)
    cidade = forms.CharField(label="Cidade", max_length=100, required=False)
    aceite_termos = forms.BooleanField(
        label="Li e aceito os Termos de uso e a Política de privacidade",
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("nome", "email", "tipo", "organizacao", "telefone", "cep", "cidade")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Senha"
        self.fields["password2"].label = "Confirmar senha"
        placeholders = {
            "nome": "Seu nome completo",
            "email": "seuemail@exemplo.com",
            "organizacao": "Ex.: Padaria Boa Massa",
            "telefone": "(11) 99999-9999",
            "cep": "00000-000",
            "cidade": "São Paulo",
            "password1": "Crie uma senha segura",
            "password2": "Digite a senha novamente",
        }
        for nome, placeholder in placeholders.items():
            self.fields[nome].widget.attrs["placeholder"] = placeholder

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        nome = self.cleaned_data["nome"].strip().split(maxsplit=1)
        user.first_name = nome[0]
        user.last_name = nome[1] if len(nome) > 1 else ""
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
            Perfil.objects.create(
                user=user,
                tipo=self.cleaned_data["tipo"],
                organizacao=self.cleaned_data["organizacao"],
                telefone=self.cleaned_data["telefone"],
                cep=self.cleaned_data["cep"],
                cidade=self.cleaned_data["cidade"],
            )
        return user


class DoacaoForm(forms.ModelForm):
    alimento_proprio = forms.BooleanField(
        label="Confirmo que o alimento está próprio para consumo",
        required=True,
    )

    class Meta:
        model = Doacao
        exclude = ("doador", "reservada_por", "status", "foto_padrao")
        widgets = {
            "data_validade": forms.DateInput(attrs={"type": "date"}),
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_fim": forms.TimeInput(attrs={"type": "time"}),
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "estado": forms.TextInput(attrs={"maxlength": 2}),
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError("A imagem deve possuir no máximo 5 MB.")
        if foto and getattr(foto, "content_type", "") not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise forms.ValidationError("Envie uma imagem JPG, PNG ou WebP.")
        return foto

    def clean(self):
        dados = super().clean()
        inicio = dados.get("horario_inicio")
        fim = dados.get("horario_fim")
        if inicio and fim and fim <= inicio:
            self.add_error("horario_fim", "O horário final deve ser posterior ao inicial.")
        return dados


class PerfilForm(forms.ModelForm):
    nome_completo = forms.CharField(label="Nome completo", max_length=150)
    email = forms.EmailField(label="E-mail", disabled=True)

    class Meta:
        model = Perfil
        exclude = ("user", "foto_url", "criado_em")
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["nome_completo"].initial = user.get_full_name()
            self.fields["email"].initial = user.email

    def save(self, commit=True):
        perfil = super().save(commit=False)
        if self.user:
            nome = self.cleaned_data["nome_completo"].strip().split(maxsplit=1)
            self.user.first_name = nome[0] if nome else ""
            self.user.last_name = nome[1] if len(nome) > 1 else ""
            if commit:
                self.user.save(update_fields=["first_name", "last_name"])
        if commit:
            perfil.save()
        return perfil
