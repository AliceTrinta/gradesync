from django.urls import path

from app import views


app_name = "app"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/status/", views.api_status, name="api-status"),
]