from django.urls import path

from app import views


app_name = "app"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/status/", views.api_status, name="api-status"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("roteiro/", views.roteiro, name="roteiro"),
    path("dispositivos/", views.dispositivos, name="dispositivos"),
    path("notificacoes/", views.notificacoes, name="notificacoes"),
    path("acessibilidade/", views.acessibilidade, name="acessibilidade"),
]