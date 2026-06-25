from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app import __version__
from app.exceptions import EntidadeNaoEncontrada, SimulacaoIncompletaError
from app.forms import (
    AvaliacaoForm,
    CadastroForm,
    GradeForm,
    LoginForm,
    PerfilForm,
    SimulacaoForm,
)
from app.models import Disciplina, Grade, Professor, Simulacao
from app.services import (
    AlunoService,
    AvaliacaoService,
    DisciplinaService,
    GradeService,
    ProfessorService,
    SimulacaoService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_aluno(request):
    """Retorna o Aluno vinculado ao user logado, ou None."""
    return getattr(request.user, "aluno", None)


# ---------------------------------------------------------------------------
# Públicas
# ---------------------------------------------------------------------------


def api_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "app": "GradeSync",
            "version": __version__,
            "endpoints": {
                "home": reverse("app:home"),
                "admin": reverse("admin:index"),
            },
        }
    )


# ---------------------------------------------------------------------------
# Auth (B1)
# ---------------------------------------------------------------------------


def login_view(request):
    if request.user.is_authenticated:
        return redirect("app:home")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", reverse("app:home"))
            return redirect(next_url)
        messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "app/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("app:login")


# ---------------------------------------------------------------------------
# Cadastro (B2)
# ---------------------------------------------------------------------------


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("app:home")

    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = AlunoService()
        try:
            service.criar_aluno(
                matricula=form.cleaned_data["matricula"],
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data.get("last_name", ""),
            )
        except ValidationError as e:
            for field, errs in e.message_dict.items():
                for err in errs:
                    messages.error(request, err)
            return render(request, "app/cadastro.html", {"form": form})

        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user:
            login(request, user)
        messages.success(request, "Conta criada com sucesso!")
        return redirect("app:home")

    return render(request, "app/cadastro.html", {"form": form})


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------


@login_required
def home(request):
    context = {
        "app_name": "GradeSync",
        "version": __version__,
        "api_status_url": reverse("app:api-status"),
        "admin_url": reverse("admin:index"),
    }
    return render(request, "app/home.html", context)


# ---------------------------------------------------------------------------
# Grades (B3)
# ---------------------------------------------------------------------------


@login_required
def grade_list(request):
    aluno = _get_aluno(request)
    if not aluno:
        messages.error(request, "Perfil de aluno não encontrado.")
        return redirect("app:home")

    grades = Grade.objects.filter(aluno=aluno).order_by("-periodo")
    return render(request, "app/grade_list.html", {"grades": grades})


@login_required
def grade_create(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    form = GradeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = GradeService()
        service.criar_grade(periodo=form.cleaned_data["periodo"], aluno=aluno)
        messages.success(request, "Grade criada com sucesso!")
        return redirect("app:grade-list")

    return render(request, "app/grade_form.html", {"form": form, "editing": False})


@login_required
def grade_edit(request, grade_id):
    aluno = _get_aluno(request)
    grade = get_object_or_404(Grade, id=grade_id, aluno=aluno)

    form = GradeForm(request.POST or None, initial={"periodo": grade.periodo})
    if request.method == "POST" and form.is_valid():
        service = GradeService()
        service.atualizar_grade(grade.id, periodo=form.cleaned_data["periodo"])
        messages.success(request, "Grade atualizada!")
        return redirect("app:grade-list")

    return render(
        request, "app/grade_form.html", {"form": form, "editing": True, "grade": grade}
    )


@login_required
def grade_delete(request, grade_id):
    aluno = _get_aluno(request)
    grade = get_object_or_404(Grade, id=grade_id, aluno=aluno)

    if request.method == "POST":
        service = GradeService()
        service.excluir_grade(grade.id)
        messages.success(request, "Grade excluída!")
        return redirect("app:grade-list")

    return render(request, "app/grade_confirm_delete.html", {"grade": grade})


# ---------------------------------------------------------------------------
# Simulações (B4)
# ---------------------------------------------------------------------------


@login_required
def simulacao_list(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    simulacoes = Simulacao.objects.filter(aluno=aluno).order_by("-periodo")
    return render(request, "app/simulacao_list.html", {"simulacoes": simulacoes})


@login_required
def simulacao_create(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    form = SimulacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = SimulacaoService()
        service.criar_simulacao(periodo=form.cleaned_data["periodo"], aluno=aluno)
        messages.success(request, "Simulação criada!")
        return redirect("app:simulacao-list")

    return render(
        request, "app/simulacao_form.html", {"form": form, "editing": False}
    )


@login_required
def simulacao_edit(request, simulacao_id):
    aluno = _get_aluno(request)
    simulacao = get_object_or_404(Simulacao, id=simulacao_id, aluno=aluno)

    form = SimulacaoForm(
        request.POST or None, initial={"periodo": simulacao.periodo}
    )
    if request.method == "POST" and form.is_valid():
        service = SimulacaoService()
        service.atualizar_simulacao(
            simulacao.id, periodo=form.cleaned_data["periodo"]
        )
        messages.success(request, "Simulação atualizada!")
        return redirect("app:simulacao-list")

    return render(
        request,
        "app/simulacao_form.html",
        {"form": form, "editing": True, "simulacao": simulacao},
    )


@login_required
def simulacao_delete(request, simulacao_id):
    aluno = _get_aluno(request)
    simulacao = get_object_or_404(Simulacao, id=simulacao_id, aluno=aluno)

    if request.method == "POST":
        service = SimulacaoService()
        service.excluir_simulacao(simulacao.id)
        messages.success(request, "Simulação excluída!")
        return redirect("app:simulacao-list")

    return render(
        request, "app/simulacao_confirm_delete.html", {"simulacao": simulacao}
    )


@login_required
def simulacao_confirmar(request, simulacao_id):
    aluno = _get_aluno(request)
    simulacao = get_object_or_404(Simulacao, id=simulacao_id, aluno=aluno)

    if request.method == "POST":
        service = SimulacaoService()
        try:
            service.confirmar_simulacao(simulacao.id)
            messages.success(request, "Simulação confirmada! Nova grade criada.")
        except SimulacaoIncompletaError as e:
            for campo, msg in e.erros.items():
                messages.error(request, f"{campo}: {msg}")
            return redirect("app:simulacao-list")
        return redirect("app:grade-list")

    return render(
        request, "app/simulacao_confirm.html", {"simulacao": simulacao}
    )


# ---------------------------------------------------------------------------
# Avaliações (B5)
# ---------------------------------------------------------------------------


@login_required
def avaliacao_list(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    avaliacoes = aluno.avaliacoes.select_related("professor", "disciplina").order_by(
        "-ano", "-semestre"
    )
    return render(request, "app/avaliacao_list.html", {"avaliacoes": avaliacoes})


@login_required
def avaliacao_create(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    form = AvaliacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = AvaliacaoService()
        service.criar_avaliacao(
            ano=form.cleaned_data["ano"],
            semestre=form.cleaned_data["semestre"],
            nota=form.cleaned_data["nota"],
            aluno=aluno,
            professor=form.cleaned_data["professor"],
            disciplina=form.cleaned_data["disciplina"],
        )
        messages.success(request, "Avaliação registrada!")
        return redirect("app:avaliacao-list")

    return render(
        request, "app/avaliacao_form.html", {"form": form, "editing": False}
    )


@login_required
def avaliacao_edit(request, avaliacao_id):
    aluno = _get_aluno(request)
    avaliacao = get_object_or_404(aluno.avaliacoes, id=avaliacao_id)

    form = AvaliacaoForm(
        request.POST or None,
        initial={
            "ano": avaliacao.ano,
            "semestre": avaliacao.semestre,
            "nota": avaliacao.nota,
            "professor": avaliacao.professor_id,
            "disciplina": avaliacao.disciplina_id,
        },
    )
    if request.method == "POST" and form.is_valid():
        service = AvaliacaoService()
        service.atualizar_avaliacao(
            avaliacao.id,
            ano=form.cleaned_data["ano"],
            semestre=form.cleaned_data["semestre"],
            nota=form.cleaned_data["nota"],
            professor=form.cleaned_data["professor"],
            disciplina=form.cleaned_data["disciplina"],
        )
        messages.success(request, "Avaliação atualizada!")
        return redirect("app:avaliacao-list")

    return render(
        request,
        "app/avaliacao_form.html",
        {"form": form, "editing": True, "avaliacao": avaliacao},
    )


@login_required
def avaliacao_delete(request, avaliacao_id):
    aluno = _get_aluno(request)
    avaliacao = get_object_or_404(aluno.avaliacoes, id=avaliacao_id)

    if request.method == "POST":
        service = AvaliacaoService()
        service.excluir_avaliacao(avaliacao.id)
        messages.success(request, "Avaliação excluída!")
        return redirect("app:avaliacao-list")

    return render(
        request, "app/avaliacao_confirm_delete.html", {"avaliacao": avaliacao}
    )


# ---------------------------------------------------------------------------
# Disciplinas e Professores (B6)
# ---------------------------------------------------------------------------


@login_required
def disciplina_list(request):
    service = DisciplinaService()
    disciplinas = service.listar_disciplinas()
    return render(request, "app/disciplina_list.html", {"disciplinas": disciplinas})


@login_required
def professor_list(request):
    service = ProfessorService()
    professores = service.listar_professores()
    return render(request, "app/professor_list.html", {"professores": professores})


# ---------------------------------------------------------------------------
# Perfil / Configurações (B7)
# ---------------------------------------------------------------------------


@login_required
def perfil(request):
    aluno = _get_aluno(request)
    if not aluno:
        messages.error(request, "Perfil de aluno não encontrado.")
        return redirect("app:home")

    user = request.user
    form = PerfilForm(
        request.POST or None,
        initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    )

    if request.method == "POST" and form.is_valid():
        service = AlunoService()
        service.atualizar_aluno(
            aluno.id,
            usuario_campos={
                "first_name": form.cleaned_data["first_name"],
                "last_name": form.cleaned_data["last_name"],
                "email": form.cleaned_data["email"],
            },
        )
        messages.success(request, "Perfil atualizado!")
        return redirect("app:perfil")

    return render(request, "app/perfil.html", {"form": form, "aluno": aluno})


@login_required
def desativar_conta(request):
    aluno = _get_aluno(request)
    if not aluno:
        return redirect("app:home")

    if request.method == "POST":
        service = AlunoService()
        service.desativar_aluno(aluno.id)
        logout(request)
        messages.info(request, "Sua conta foi desativada.")
        return redirect("app:login")

    return render(request, "app/desativar_conta.html", {"aluno": aluno})


def duvidas(request):
    return render(request,"duvidas.html")


def sobre(request):
    return render(request,"sobre.html")