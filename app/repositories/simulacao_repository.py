from app.exceptions import EntidadeNaoEncontrada
from app.models import Simulacao


class SimulacaoRepository:
    def create(self, *, periodo, aluno, turmas=None):
        simulacao = Simulacao(periodo=periodo, aluno=aluno)
        simulacao.full_clean()
        simulacao.save()
        if turmas is not None:
            simulacao.turmas.set(turmas)
        return self.get(simulacao.id)

    def get(self, simulacao_id):
        try:
            return (
                Simulacao.objects.select_related("aluno", "aluno__usuario")
                .prefetch_related("turmas", "turmas__carga_horarias")
                .get(id=simulacao_id)
            )
        except Simulacao.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Simulacao nao encontrada.") from exc

    def list(self):
        return (
            Simulacao.objects.select_related("aluno", "aluno__usuario")
            .prefetch_related("turmas")
            .order_by("periodo", "id")
        )

    def update(self, simulacao_id, *, turmas=None, **campos):
        simulacao = self.get(simulacao_id)
        for campo, valor in campos.items():
            setattr(simulacao, campo, valor)
        simulacao.full_clean()
        simulacao.save()

        if turmas is not None:
            simulacao.turmas.set(turmas)

        return self.get(simulacao.id)

    def delete(self, simulacao_id):
        simulacao = self.get(simulacao_id)
        simulacao.delete()
