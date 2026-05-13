from django.db import transaction

from app.exceptions import EntidadeNaoEncontrada
from app.models import Grade, Turma


class GradeRepository:
    @transaction.atomic
    def create(self, *, periodo, aluno, turmas=None):
        grade = Grade(periodo=periodo, aluno=aluno)
        grade.full_clean()
        grade.save()
        self._substituir_turmas(grade, turmas or [])
        return self.get(grade.id)

    def get(self, grade_id):
        try:
            return (
                Grade.objects.select_related("aluno", "aluno__usuario")
                .prefetch_related("turmas", "turmas__carga_horarias")
                .get(id=grade_id)
            )
        except Grade.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Grade nao encontrada.") from exc

    def list(self):
        return (
            Grade.objects.select_related("aluno", "aluno__usuario")
            .prefetch_related("turmas")
            .order_by("periodo")
        )

    @transaction.atomic
    def update(self, grade_id, *, turmas=None, **campos):
        grade = self.get(grade_id)
        for campo, valor in campos.items():
            setattr(grade, campo, valor)
        grade.full_clean()
        grade.save()

        if turmas is not None:
            grade.turmas.all().delete()
            self._substituir_turmas(grade, turmas)

        return self.get(grade.id)

    def delete(self, grade_id):
        grade = self.get(grade_id)
        grade.delete()

    def _substituir_turmas(self, grade, turmas):
        for turma in turmas:
            nova_turma = Turma(
                codigo=turma.codigo,
                grade=grade,
                disciplina=turma.disciplina,
            )
            nova_turma.full_clean()
            nova_turma.save()
            nova_turma.carga_horarias.set(turma.carga_horarias.all())
