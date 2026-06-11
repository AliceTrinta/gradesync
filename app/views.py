from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from app import __version__


def home(request):
    context = {
        "app_name": "GradeSync",
        "version": __version__,
        "api_status_url": reverse("app:api-status"),
        "admin_url": reverse("admin:index"),
    }
    return render(request, "app/home.html", context)


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

def cadastro(request):
    return render(request, "app/cadastro.html")

def configuracoes(request):
    return render(request, "app/config.html")

def roteiro(request):
    return render(request, "app/roteiro.html")

def dispositivos(request):
    return render(request, "app/dispositivos.html")

def notificacoes(request):
    return render(request, "app/notificacoes.html")

def acessibilidade(request):
    return render(request, "app/acessibilidade.html")