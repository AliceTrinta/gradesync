from app.exceptions import EntidadeNaoEncontrada
from app.models import Turma


class TurmaRepository:
    def create(self, *, codigo, grade, disciplina, carga_horarias=None):
        turma = Turma(codigo=codigo, grade=grade, disciplina=disciplina)
        turma.full_clean()
        turma.save()
        if carga_horarias is not None:
            turma.carga_horarias.set(carga_horarias)
        return self.get(turma.id)

    def get(self, turma_id):
        try:
            return (
                Turma.objects.select_related("grade", "disciplina")
                .prefetch_related("carga_horarias")
                .get(id=turma_id)
            )
        except Turma.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Turma nao encontrada.") from exc

    def list(self):
        return (
            Turma.objects.select_related("grade", "disciplina")
            .prefetch_related("carga_horarias")
            .order_by("codigo", "id")
        )

    def update(self, turma_id, *, carga_horarias=None, **campos):
        turma = self.get(turma_id)
        for campo, valor in campos.items():
            setattr(turma, campo, valor)
        turma.full_clean()
        turma.save()
        if carga_horarias is not None:
            turma.carga_horarias.set(carga_horarias)
        return self.get(turma.id)

    def delete(self, turma_id):
        turma = self.get(turma_id)
        turma.delete()
