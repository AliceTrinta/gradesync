from app.exceptions import EntidadeNaoEncontrada
from app.models import Roteiro


class RoteiroRepository:
    def create(self, *, aluno, titulo=None, slots=None, prompt_usado=""):
        roteiro = Roteiro(
            aluno=aluno,
            titulo=titulo or "Meu roteiro semanal",
            slots=list(slots or []),
            prompt_usado=prompt_usado,
        )
        roteiro.full_clean()
        roteiro.save()
        return roteiro

    def get(self, roteiro_id):
        try:
            return Roteiro.objects.select_related("aluno").get(id=roteiro_id)
        except Roteiro.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Roteiro nao encontrado.") from exc

    def get_by_aluno(self, aluno):
        return Roteiro.objects.filter(aluno=aluno).first()

    def update(self, roteiro_id, **campos):
        roteiro = self.get(roteiro_id)
        for campo, valor in campos.items():
            setattr(roteiro, campo, valor)
        roteiro.full_clean()
        roteiro.save()
        return roteiro

    def upsert_by_aluno(self, *, aluno, titulo=None, slots=None, prompt_usado=""):
        """Cria ou atualiza o roteiro do aluno."""
        existente = self.get_by_aluno(aluno)
        if existente is None:
            return self.create(
                aluno=aluno,
                titulo=titulo,
                slots=slots,
                prompt_usado=prompt_usado,
            )
        return self.update(
            existente.id,
            titulo=titulo or existente.titulo,
            slots=list(slots or []),
            prompt_usado=prompt_usado or existente.prompt_usado,
        )

    def delete(self, roteiro_id):
        roteiro = self.get(roteiro_id)
        roteiro.delete()
        return True
