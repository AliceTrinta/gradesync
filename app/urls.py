from django.urls import path

from app import views


app_name = "app"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("recuperasenha/", views.recuperasenha, name="recuperasenha"),

    path("", views.home, name="home"),
    path("api/status/", views.api_status, name="api-status"),

    path("grades/", views.grade_list, name="grade-list"),
    path("grades/nova/", views.grade_criar, name="grade-criar"),
    path("grades/<uuid:grade_id>/", views.grade_detalhe, name="grade-detalhe"),
    path(
        "grades/<uuid:grade_id>/excluir/",
        views.grade_excluir,
        name="grade-excluir",
    ),

    path("roteiro/", views.roteiro, name="roteiro"),
    path("roteiro/criar/", views.roteiro_criar, name="roteiro-criar"),
    path("roteiro/excluir/", views.roteiro_excluir, name="roteiro-excluir"),
    path(
        "roteiro/blocos/adicionar/",
        views.roteiro_bloco_adicionar,
        name="roteiro-bloco-adicionar",
    ),
    path(
        "roteiro/blocos/<str:bloco_id>/editar/",
        views.roteiro_bloco_editar,
        name="roteiro-bloco-editar",
    ),
    path(
        "roteiro/blocos/<str:bloco_id>/remover/",
        views.roteiro_bloco_remover,
        name="roteiro-bloco-remover",
    ),

    path("notificacoes/", views.notificacoes, name="notificacoes"),
    path(
        "notificacoes/<uuid:notif_id>/marcar-lida/",
        views.notificacao_marcar_lida,
        name="notificacoes-marcar-lida",
    ),
    path(
        "notificacoes/marcar-todas/",
        views.notificacao_marcar_todas,
        name="notificacoes-marcar-todas",
    ),

    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("acessibilidade/", views.acessibilidade, name="acessibilidade"),
    path("dispositivos/", views.dispositivos, name="dispositivos"),

    path("duvidas/", views.duvidas, name="duvidas"),
    path("sobre/", views.sobre, name="sobre"),
    path("idiomas/", views.idiomas, name="idiomas"),
]

