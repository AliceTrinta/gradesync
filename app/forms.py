from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from app.models import Avaliacao, Disciplina, Grade, Professor, Simulacao, Turma

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Usuário", "autofocus": True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Senha"}),
    )


class CadastroForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Nome"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Sobrenome"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Usuário"}),
    )
    matricula = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={"placeholder": "Matrícula"}),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "Senha"}),
    )
    password_confirm = forms.CharField(
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


class GradeForm(forms.Form):
    periodo = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={"placeholder": "Ex: 2026.1"}),
    )


class SimulacaoForm(forms.Form):
    periodo = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={"placeholder": "Ex: 2026.2"}),
    )
    turmas = forms.ModelMultipleChoiceField(
        queryset=Turma.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, grade_turmas_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if grade_turmas_qs is not None:
            self.fields["turmas"].queryset = grade_turmas_qs


class AvaliacaoForm(forms.Form):
    ano = forms.IntegerField(min_value=2000)
    semestre = forms.IntegerField(min_value=1, max_value=2)
    nota = forms.DecimalField(min_value=0, max_value=10, decimal_places=2)
    professor = forms.ModelChoiceField(
        queryset=Professor.objects.all(),
        empty_label="Selecione o professor",
    )
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.all(),
        empty_label="Selecione a disciplina",
    )


class PerfilForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Nome"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Sobrenome"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
