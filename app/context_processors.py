from django.conf import settings

from app import __version__


NAV_ITEMS = [
    {"url": "app:home", "label": "Início", "icon": "fa-solid fa-house"},
    {"url": "app:grade-list", "label": "Grade", "icon": "fa-regular fa-calendar"},
    {"url": "app:roteiro", "label": "Roteiro", "icon": "fa-solid fa-wand-magic-sparkles"},
    {"url": "app:notificacoes", "label": "Notificações", "icon": "fa-regular fa-bell"},
    {"url": "app:duvidas", "label": "Ajuda", "icon": "fa-regular fa-circle-question"},
    {"url": "app:configuracoes", "label": "Configurações", "icon": "fa-solid fa-gear"},
]


def gradesync_context(request):
    context = {
        "app_name": "GradeSync",
        "app_version": __version__,
        "version": __version__,
        "ia_disponivel": bool(getattr(settings, "AI_API_KEY", "")),
    }

    if not request.user.is_authenticated:
        return context

    aluno = getattr(request.user, "aluno", None)
    context["aluno"] = aluno
    context["nav_items"] = NAV_ITEMS

    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match and resolver_match.namespace and resolver_match.url_name:
        context["active_nav"] = f"{resolver_match.namespace}:{resolver_match.url_name}"

    if aluno is None:
        return context

    from app.services import (
        NotificacaoService,
        PreferenciaAcessibilidadeService,
        PreferenciaContaService,
    )

    context["notificacoes_nao_lidas"] = NotificacaoService().contar_nao_lidas(aluno)
    context["prefs_acessibilidade"] = PreferenciaAcessibilidadeService().obter_do_aluno(aluno)
    context["prefs_conta"] = PreferenciaContaService().obter_do_aluno(aluno)

    return context
