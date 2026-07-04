from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuário",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Usuário", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Senha"}),
    )


class CadastroForm(forms.Form):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Nome"}),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Sobrenome"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    username = forms.CharField(
        label="Usuário",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Usuário"}),
    )
    matricula = forms.CharField(
        label="Matrícula",
        max_length=32,
        widget=forms.TextInput(attrs={"placeholder": "Matrícula"}),
    )
    password = forms.CharField(
        label="Senha",
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "Senha"}),
    )
    password_confirm = forms.CharField(
        label="Confirme a senha",
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirme a senha"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "As senhas não coincidem.")
        return cleaned
