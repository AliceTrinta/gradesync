from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy


urlpatterns = [
    path(
        "senha/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="app/password_reset_form.html",
            email_template_name="app/password_reset_email.html",
            subject_template_name="app/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "senha/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="app/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="app/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "senha/redefinida/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="app/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),

    path("", include("app.urls")),
    path("admin/", admin.site.urls),
]
