from django.contrib import admin

from app.models import (
    Aluno,
    Avaliacao,
    CargaHoraria,
    Disciplina,
    Grade,
    Notificacao,
    PreferenciaAcessibilidade,
    PreferenciaConta,
    Professor,
    Roteiro,
    Simulacao,
    Turma,
)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("matricula", "usuario", "ativo")
    search_fields = ("matricula", "usuario__username", "usuario__first_name")
    list_filter = ("ativo",)

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
    search_fields = ("aluno__matricula", "periodo")


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "grade", "disciplina")
    list_filter = ("grade__periodo", "disciplina")
    search_fields = ("codigo", "disciplina__codigo")

@admin.register(Roteiro)
class RoteiroAdmin(admin.ModelAdmin):
    list_display = ("aluno", "titulo", "atualizado_em")
    search_fields = ("aluno__matricula", "titulo")
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "aluno", "tipo", "lida", "criada_em")
    list_filter = ("tipo", "lida", "criada_em")
    search_fields = ("titulo", "mensagem", "aluno__matricula")
    readonly_fields = ("criada_em",)
    actions = ("marcar_como_lidas",)

    def marcar_como_lidas(self, request, queryset):
        queryset.update(lida=True)

    marcar_como_lidas.short_description = "Marcar selecionadas como lidas"


@admin.register(PreferenciaAcessibilidade)
class PreferenciaAcessibilidadeAdmin(admin.ModelAdmin):
    list_display = ("aluno", "tamanho_fonte", "alto_contraste", "reduzir_animacoes")
    list_filter = ("tamanho_fonte", "alto_contraste")


@admin.register(PreferenciaConta)
class PreferenciaContaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "idioma", "tema")
    list_filter = ("idioma", "tema")
