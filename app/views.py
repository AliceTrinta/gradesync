from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from app import __version__
from app.cursos import CURSOS, CURSOS_DICT, periodo_atual_permitido
from app.exceptions import (
    AIProviderError,
    BlocoConflitaComGradeError,
    BlocoRoteiroInvalidoError,
    ConflitoDeHorarioError,
    EntidadeNaoEncontrada,
)
from app.forms import CadastroForm, LoginForm
from app.models import (
    CargaHoraria,
    PreferenciaAcessibilidade,
    PreferenciaConta,
)
from app.services import (
    AlunoService,
    DisciplinaService,
    GradeService,
    NotificacaoService,
    PreferenciaAcessibilidadeService,
    PreferenciaContaService,
    RoteiroService,
)
from app.services.roteiro_service import CORES


DIAS_ORDEM = ["seg", "ter", "qua", "qui", "sex", "sab"]
HORAS_GRADE = [f"{h:02d}:00" for h in range(8, 18)]


def _hora_do_valor(valor):
    if hasattr(valor, "hour"):
        return valor.hour
    if not valor:
        return 0
    return int(str(valor).split(":", 1)[0])


def _horas_no_intervalo(inicio, fim):
    h_inicio = _hora_do_valor(inicio)
    h_fim = _hora_do_valor(fim)
    if h_fim <= h_inicio:
        return [f"{h_inicio:02d}:00"]
    return [f"{h:02d}:00" for h in range(h_inicio, h_fim)]


def _require_aluno(request):
    aluno = getattr(request.user, "aluno", None)
    if aluno is None:
        messages.error(request, "Perfil de aluno nao encontrado.")
        return None, redirect("app:home")
    return aluno, None


def _obter_grade_do_aluno(aluno, grade_id):
    try:
        grade = GradeService().obter_grade(grade_id)
    except (EntidadeNaoEncontrada, ValueError):
        return None
    if grade.aluno_id != aluno.id:
        return None
    return grade


def _montar_grid_semanal(cells_por_chave):
    return [
        {
            "hora": hora,
            "cells": [cells_por_chave.get((hora, dia)) for dia in DIAS_ORDEM],
        }
        for hora in HORAS_GRADE
    ]


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
            next_url = request.GET.get("next") or reverse("app:home")
            return redirect(next_url)
        messages.error(request, "Usuario ou senha invalidos.")

    return render(request, "app/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("app:login")


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
                    messages.error(request, f"{field}: {err}")
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


def home(request):
    context = {
        "app_name": "GradeSync",
        "version": __version__,
        "api_status_url": reverse("app:api-status"),
        "admin_url": reverse("admin:index"),
    }
    return render(request, "app/home.html", context)


def recuperasenha(request):
    return render(request, "app/recuperasenha.html")


def recuperasenha(request):
    return render(request, "app/recuperasenha.html")


def duvidas(request):
    return render(request, "app/duvidas.html")


_DUVIDAS_JANELA_SEG = 60 * 60
_DUVIDAS_MAX_POR_JANELA = 10


@login_required
@require_POST
def duvidas_perguntar(request):
    """Endpoint AJAX do chatbot. Sempre HTTP 200 com JSON
    {resposta, fonte: ia|fallback, restantes}."""
    import time

    from app.services import AIService, GradeService, RoteiroService

    aluno, redir = _require_aluno(request)
    if redir:
        return JsonResponse(
            {"resposta": "Sessão encerrada. Faça login novamente.",
             "fonte": "fallback", "restantes": 0},
            status=200,
        )

    pergunta = (request.POST.get("pergunta") or "").strip()
    if not pergunta:
        return JsonResponse(
            {"resposta": "Envie uma pergunta.", "fonte": "fallback",
             "restantes": _DUVIDAS_MAX_POR_JANELA},
            status=200,
        )
    if len(pergunta) > 500:
        return JsonResponse(
            {"resposta": "Pergunta muito longa (máximo 500 caracteres).",
             "fonte": "fallback", "restantes": _DUVIDAS_MAX_POR_JANELA},
            status=200,
        )

    agora = int(time.time())
    inicio_janela = request.session.get("ai_duvidas_janela_ini", 0)
    contador = request.session.get("ai_duvidas_contador", 0)
    if agora - inicio_janela > _DUVIDAS_JANELA_SEG:
        inicio_janela = agora
        contador = 0
    if contador >= _DUVIDAS_MAX_POR_JANELA:
        return JsonResponse(
            {"resposta": (
                "⏳ Voce atingiu o limite de perguntas para a IA nesta "
                "hora. Tente novamente em breve ou use as sugestoes."
            ),
             "fonte": "fallback", "restantes": 0},
            status=200,
        )

    grade = GradeService().listar_do_aluno(aluno).first()
    roteiro = RoteiroService().obter_do_aluno(aluno)
    prefs_conta = PreferenciaContaService().obter_do_aluno(aluno)
    tela_atual = request.POST.get("tela") or request.META.get("HTTP_REFERER", "")

    try:
        resposta = AIService().responder_duvida(
            aluno=aluno,
            pergunta=pergunta,
            tela_atual=tela_atual,
            grade=grade,
            roteiro=roteiro,
            prefs_conta=prefs_conta,
        )
        fonte = "ia"
    except AIProviderError as exc:
        return JsonResponse(
            {"resposta": (
                f"🤖 IA indisponível no momento ({exc}). "
                "Voce pode usar as sugestoes ou tentar de novo."
            ),
             "fonte": "fallback",
             "restantes": _DUVIDAS_MAX_POR_JANELA - contador},
            status=200,
        )

    contador += 1
    request.session["ai_duvidas_janela_ini"] = inicio_janela
    request.session["ai_duvidas_contador"] = contador

    return JsonResponse(
        {"resposta": resposta, "fonte": fonte,
         "restantes": _DUVIDAS_MAX_POR_JANELA - contador},
        status=200,
    )


def sobre(request):
    return render(request, "app/sobre.html")


@login_required
def privacidade(request):
    return render(request, "app/privacidade.html")


@login_required
def dispositivos(request):
    return render(request, "app/dispositivos.html")


def _grid_do_roteiro(roteiro):
    if not roteiro or not roteiro.slots:
        return []
    por_celula = {}
    for slot in roteiro.slots:
        dia = slot.get("dia", "")
        horas = _horas_no_intervalo(
            slot.get("hora_inicio", ""),
            slot.get("hora_final", ""),
        )
        for idx, hora in enumerate(horas):
            por_celula[(hora, dia)] = {
                **slot,
                "is_head": idx == 0,
                "is_tail": idx == len(horas) - 1,
            }
    return _montar_grid_semanal(por_celula)


@login_required
def roteiro(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    roteiro_obj = RoteiroService().obter_do_aluno(aluno)
    grades = list(GradeService().listar_do_aluno(aluno))
    context = {
        "roteiro": roteiro_obj,
        "slots_grid": _grid_do_roteiro(roteiro_obj),
        "grades": grades,
        "tem_grade": bool(grades),
    }
    return render(request, "app/roteiro.html", context)


@login_required
@require_POST
def roteiro_criar(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    grades = list(GradeService().listar_do_aluno(aluno))
    if not grades:
        messages.error(
            request,
            "Voce precisa criar uma grade do semestre antes de gerar o roteiro.",
        )
        return redirect("app:grade-list")

    grade_id = request.POST.get("grade_id")
    grade = _obter_grade_do_aluno(aluno, grade_id) if grade_id else None
    if grade is None:
        grade = grades[0]

    RoteiroService().gerar_roteiro_padrao(aluno=aluno, grade=grade)
    messages.success(request, f"Roteiro gerado com base na grade {grade.periodo}!")
    return redirect("app:roteiro")


@login_required
@require_POST
def roteiro_criar_ia(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    grades = list(GradeService().listar_do_aluno(aluno))
    if not grades:
        messages.error(
            request,
            "Voce precisa criar uma grade do semestre antes de gerar o roteiro.",
        )
        return redirect("app:grade-list")

    grade_id = request.POST.get("grade_id")
    grade = _obter_grade_do_aluno(aluno, grade_id) if grade_id else None
    if grade is None:
        grade = grades[0]

    try:
        roteiro = RoteiroService().sugerir_roteiro_via_ia(
            aluno=aluno, grade=grade
        )
    except AIProviderError as exc:
        messages.warning(
            request,
            f"IA indisponível ({exc}). Geramos um roteiro padrão para voce.",
        )
        RoteiroService().gerar_roteiro_padrao(aluno=aluno, grade=grade)
        return redirect("app:roteiro")

    if (roteiro.prompt_usado or "").startswith("[IA]"):
        messages.success(
            request,
            f"Roteiro sugerido pela IA com base na grade {grade.periodo}! ✨",
        )
    else:
        messages.info(
            request,
            f"A IA não devolveu blocos suficientes; usamos o gerador padrão "
            f"para a grade {grade.periodo}.",
        )
    return redirect("app:roteiro")


@login_required
@require_POST
def roteiro_excluir(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    if RoteiroService().excluir_do_aluno(aluno):
        messages.info(request, "Roteiro removido.")
    return redirect("app:roteiro")


def _extrair_bloco_do_post(request):
    return {
        "dia": (request.POST.get("dia") or "").strip(),
        "hora_inicio": (request.POST.get("hora_inicio") or "").strip(),
        "hora_final": (request.POST.get("hora_final") or "").strip(),
        "titulo": (request.POST.get("titulo") or "").strip(),
        "cor": (request.POST.get("cor") or "blue").strip(),
    }


@login_required
@require_POST
def roteiro_bloco_adicionar(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    try:
        RoteiroService().adicionar_bloco(aluno, **_extrair_bloco_do_post(request))
        messages.success(request, "Bloco adicionado ao roteiro.")
    except (BlocoConflitaComGradeError, BlocoRoteiroInvalidoError) as exc:
        messages.error(request, str(exc))
    return redirect("app:roteiro")


@login_required
@require_POST
def roteiro_bloco_editar(request, bloco_id):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    try:
        RoteiroService().editar_bloco(
            aluno, bloco_id=bloco_id, **_extrair_bloco_do_post(request)
        )
        messages.success(request, "Bloco atualizado.")
    except (BlocoConflitaComGradeError, BlocoRoteiroInvalidoError) as exc:
        messages.error(request, str(exc))
    return redirect("app:roteiro")


@login_required
@require_POST
def roteiro_bloco_remover(request, bloco_id):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    try:
        RoteiroService().remover_bloco(aluno, bloco_id=bloco_id)
        messages.info(request, "Bloco removido.")
    except BlocoRoteiroInvalidoError as exc:
        messages.error(request, str(exc))
    return redirect("app:roteiro")


def _listar_cargas_ordenadas():
    ordem_dias = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5}
    todas = list(CargaHoraria.objects.all())
    todas.sort(
        key=lambda c: (
            ordem_dias.get((c.dia or "").strip().lower()[:3], 99),
            c.hora_inicio,
        )
    )
    return [
        (
            str(carga.id),
            f"{carga.dia.capitalize()} · "
            f"{carga.hora_inicio.strftime('%H:%M')} - "
            f"{carga.hora_final.strftime('%H:%M')}",
        )
        for carga in todas
    ]


def _extrair_selecoes(request, disciplinas):
    selecoes = []
    for disciplina in disciplinas:
        if request.POST.get(f"disciplina_{disciplina.id}") != "on":
            continue
        cargas_ids = request.POST.getlist(f"cargas_{disciplina.id}")
        if not cargas_ids:
            return None, disciplina.codigo
        selecoes.append(
            {
                "disciplina_id": str(disciplina.id),
                "carga_horaria_ids": cargas_ids,
            }
        )
    return selecoes, None


def _grid_da_grade(grade):
    if not grade:
        return []
    cor_por_disciplina = {}
    por_celula = {}
    for turma in grade.turmas.all():
        disc_id = turma.disciplina_id
        if disc_id not in cor_por_disciplina:
            cor_por_disciplina[disc_id] = CORES[
                len(cor_por_disciplina) % len(CORES)
            ]
        cor = cor_por_disciplina[disc_id]
        for carga in turma.carga_horarias.all():
            dia_slug = (carga.dia or "").strip().lower()[:3]
            hora_inicio_str = carga.hora_inicio.strftime("%H:%M")
            hora_final_str = carga.hora_final.strftime("%H:%M")
            horas = _horas_no_intervalo(carga.hora_inicio, carga.hora_final)
            for idx, hora in enumerate(horas):
                por_celula[(hora, dia_slug)] = {
                    "codigo": turma.disciplina.codigo,
                    "nome": turma.disciplina.nome,
                    "cor": cor,
                    "hora_inicio": hora_inicio_str,
                    "hora_final": hora_final_str,
                    "is_head": idx == 0,
                    "is_tail": idx == len(horas) - 1,
                }
    return _montar_grid_semanal(por_celula)


@login_required
def grade_list(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    grades = list(GradeService().listar_do_aluno(aluno))
    return render(request, "app/grade_list.html", {"grades": grades})


@login_required
def grade_criar(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    curso = (request.GET.get("curso") or request.POST.get("curso") or "").upper()
    disciplinas = []
    disciplinas_com_cargas = []
    if curso in CURSOS_DICT:
        disciplinas = list(
            DisciplinaService().listar_por_curso(curso).order_by("codigo")
        )
        cargas = _listar_cargas_ordenadas()
        disciplinas_com_cargas = [
            {"disciplina": d, "cargas": cargas} for d in disciplinas
        ]

    if request.method == "POST":
        redir = _processar_criacao_grade(request, aluno, curso, disciplinas)
        if redir is not None:
            return redir

    context = {
        "cursos": CURSOS,
        "curso_selecionado": curso if curso in CURSOS_DICT else "",
        "nome_curso_selecionado": CURSOS_DICT.get(curso, ""),
        "disciplinas_com_cargas": disciplinas_com_cargas,
        "periodo_atual": periodo_atual_permitido(),
    }
    return render(request, "app/grade_form.html", context)


def _processar_criacao_grade(request, aluno, curso, disciplinas):
    periodo = periodo_atual_permitido()
    if curso not in CURSOS_DICT:
        messages.error(request, "Selecione um curso valido.")
        return None

    if GradeService().listar_do_aluno(aluno).filter(periodo=periodo).exists():
        messages.error(request, f"Voce ja tem uma grade para o periodo {periodo}.")
        return None

    selecoes, codigo_sem_horario = _extrair_selecoes(request, disciplinas)
    if codigo_sem_horario:
        messages.error(
            request,
            f"Selecione ao menos um horario para {codigo_sem_horario}.",
        )
        return None
    if not selecoes:
        messages.error(
            request, "Selecione ao menos uma disciplina para montar a grade."
        )
        return None

    try:
        grade = GradeService().criar_grade_do_aluno(
            aluno=aluno, periodo=periodo, selecoes=selecoes
        )
    except ConflitoDeHorarioError as e:
        messages.error(request, str(e))
        return None
    except ValidationError as e:
        for field, errs in e.message_dict.items():
            for err in errs:
                messages.error(request, f"{field}: {err}")
        return None

    messages.success(request, f"Grade {grade.periodo} criada com sucesso!")
    return redirect("app:grade-detalhe", grade_id=grade.id)


@login_required
def grade_detalhe(request, grade_id):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    grade = _obter_grade_do_aluno(aluno, grade_id)
    if grade is None:
        messages.error(request, "Grade nao encontrada.")
        return redirect("app:grade-list")

    context = {
        "grade": grade,
        "turmas": list(grade.turmas.select_related("disciplina").all()),
        "slots_grid": _grid_da_grade(grade),
    }
    return render(request, "app/grade_detalhe.html", context)


@login_required
def grade_excluir(request, grade_id):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    grade = _obter_grade_do_aluno(aluno, grade_id)
    if grade is None:
        messages.error(request, "Grade nao encontrada.")
        return redirect("app:grade-list")

    if request.method == "POST":
        GradeService().excluir_grade(grade.id)
        messages.info(request, "Grade removida.")
        return redirect("app:grade-list")

    return render(request, "app/grade_confirm_delete.html", {"grade": grade})


@login_required
def notificacoes(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    service = NotificacaoService()
    context = {
        "notificacoes": list(service.listar_do_aluno(aluno)),
        "nao_lidas": service.contar_nao_lidas(aluno),
    }
    return render(request, "app/notificacoes.html", context)


@login_required
@require_POST
def notificacao_marcar_lida(request, notif_id):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    try:
        NotificacaoService().marcar_como_lida(notif_id, aluno)
    except EntidadeNaoEncontrada:
        messages.error(request, "Notificacao nao encontrada.")
    return redirect("app:notificacoes")


@login_required
@require_POST
def notificacao_marcar_todas(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    total = NotificacaoService().marcar_todas_como_lidas(aluno)
    if total:
        messages.success(request, f"{total} notificacao(oes) marcada(s) como lida(s).")
    return redirect("app:notificacoes")


@login_required
def acessibilidade(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    service = PreferenciaAcessibilidadeService()
    prefs = service.obter_do_aluno(aluno)

    if request.method == "POST":
        tamanho_fonte = request.POST.get("tamanho_fonte", prefs.tamanho_fonte)
        validos = {v for v, _ in PreferenciaAcessibilidade.TAMANHOS_FONTE}
        if tamanho_fonte not in validos:
            tamanho_fonte = prefs.tamanho_fonte

        try:
            service.atualizar(
                aluno,
                tamanho_fonte=tamanho_fonte,
                alto_contraste="alto_contraste" in request.POST,
                reduzir_animacoes="reduzir_animacoes" in request.POST,
                sublinhar_links="sublinhar_links" in request.POST,
            )
            messages.success(request, "Preferencias de acessibilidade salvas!")
        except ValidationError as e:
            for field, errs in e.message_dict.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return redirect("app:acessibilidade")

    context = {
        "prefs_acessibilidade": prefs,
        "tamanhos_fonte": PreferenciaAcessibilidade.TAMANHOS_FONTE,
    }
    return render(request, "app/acessibilidade.html", context)


@login_required
def configuracoes(request):
    aluno, redir = _require_aluno(request)
    if redir:
        return redir

    service = PreferenciaContaService()
    prefs = service.obter_do_aluno(aluno)

    if request.method == "POST":
        idioma = request.POST.get("idioma", prefs.idioma)
        tema = request.POST.get("tema", prefs.tema)

        idiomas_validos = {v for v, _ in PreferenciaConta.IDIOMAS}
        temas_validos = {v for v, _ in PreferenciaConta.TEMAS}
        if idioma not in idiomas_validos:
            idioma = prefs.idioma
        if tema not in temas_validos:
            tema = prefs.tema

        try:
            service.atualizar(aluno, idioma=idioma, tema=tema)
            messages.success(request, "Preferencias de conta salvas!")
        except ValidationError as e:
            for field, errs in e.message_dict.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return redirect("app:configuracoes")

    context = {
        "prefs_conta": prefs,
        "idiomas": PreferenciaConta.IDIOMAS,
        "temas": PreferenciaConta.TEMAS,
    }
    return render(request, "app/config.html", context)
