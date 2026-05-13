from django.contrib import admin

from app.models import (
    Aluno,
    Avaliacao,
    CargaHoraria,
    Disciplina,
    Grade,
    Professor,
    Simulacao,
    Turma,
)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("matricula", "usuario", "ativo")
    search_fields = ("matricula", "usuario__username", "usuario__first_name")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "disciplina", "professor", "ano", "semestre", "nota")
    list_filter = ("ano", "semestre", "disciplina", "professor")
    search_fields = ("aluno__matricula", "disciplina__codigo", "professor__nome")


@admin.register(CargaHoraria)
class CargaHorariaAdmin(admin.ModelAdmin):
    list_display = ("dia", "hora_inicio", "hora_final")
    list_filter = ("dia",)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "taxa_de_reprovacao")
    search_fields = ("codigo", "nome")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("aluno", "periodo")
    list_filter = ("periodo",)
    search_fields = ("aluno__matricula", "aluno__usuario__username", "periodo")


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("nome", "avaliacao")
    search_fields = ("nome",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Simulacao)
class SimulacaoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "periodo")
    list_filter = ("periodo",)
    search_fields = ("aluno__matricula", "aluno__usuario__username", "periodo")


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "disciplina", "grade")
    search_fields = ("codigo", "disciplina__codigo", "disciplina__nome")
