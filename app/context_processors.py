def gradesync_context(request):
    """Injeta dados globais do GradeSync em todos os templates."""
    context = {
        "app_name": "GradeSync",
    }

    if request.user.is_authenticated:
        aluno = getattr(request.user, "aluno", None)
        context["aluno"] = aluno

        context["nav_items"] = [
            {"url": "app:home", "label": "Início", "icon": "fa-solid fa-house"},
            {"url": "app:grade-list", "label": "Grades", "icon": "fa-solid fa-calendar-days"},
            {"url": "app:simulacao-list", "label": "Simulações", "icon": "fa-solid fa-flask"},
            {"url": "app:avaliacao-list", "label": "Avaliações", "icon": "fa-solid fa-star"},
            {"url": "app:disciplina-list", "label": "Disciplinas", "icon": "fa-solid fa-book"},
            {"url": "app:professor-list", "label": "Professores", "icon": "fa-solid fa-chalkboard-user"},
            {"url": "app:perfil", "label": "Perfil", "icon": "fa-solid fa-user"},
        ]

    return context
