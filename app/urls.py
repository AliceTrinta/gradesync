from django.urls import path

from app import views


app_name = "app"

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),

    # Home / API
    path("", views.home, name="home"),
    path("api/status/", views.api_status, name="api-status"),

    # Grades
    path("grades/", views.grade_list, name="grade-list"),
    path("grades/nova/", views.grade_create, name="grade-create"),
    path("grades/<uuid:grade_id>/editar/", views.grade_edit, name="grade-edit"),
    path("grades/<uuid:grade_id>/excluir/", views.grade_delete, name="grade-delete"),

    # Simulações
    path("simulacoes/", views.simulacao_list, name="simulacao-list"),
    path("simulacoes/nova/", views.simulacao_create, name="simulacao-create"),
    path("simulacoes/<uuid:simulacao_id>/editar/", views.simulacao_edit, name="simulacao-edit"),
    path("simulacoes/<uuid:simulacao_id>/excluir/", views.simulacao_delete, name="simulacao-delete"),
    path("simulacoes/<uuid:simulacao_id>/confirmar/", views.simulacao_confirmar, name="simulacao-confirmar"),

    # Avaliações
    path("avaliacoes/", views.avaliacao_list, name="avaliacao-list"),
    path("avaliacoes/nova/", views.avaliacao_create, name="avaliacao-create"),
    path("avaliacoes/<uuid:avaliacao_id>/editar/", views.avaliacao_edit, name="avaliacao-edit"),
    path("avaliacoes/<uuid:avaliacao_id>/excluir/", views.avaliacao_delete, name="avaliacao-delete"),

    # Catálogo
    path("disciplinas/", views.disciplina_list, name="disciplina-list"),
    path("professores/", views.professor_list, name="professor-list"),

    # Perfil
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/desativar/", views.desativar_conta, name="desativar-conta"),

    # Ajuda
    path("duvidas/", views.duvidas, name="duvidas"),

    # Configuracoes
    path("sobre/", views.sobre, name="sobre"),
]
