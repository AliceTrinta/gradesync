from app.exceptions import EntidadeNaoEncontrada
from app.models import Avaliacao


class AvaliacaoRepository:
    def create(self, *, ano, semestre, nota, aluno, professor, disciplina):
        avaliacao = Avaliacao(
            ano=ano,
            semestre=semestre,
            nota=nota,
            aluno=aluno,
            professor=professor,
            disciplina=disciplina,
        )
        avaliacao.full_clean()
        avaliacao.save()
        return self.get(avaliacao.id)

    def get(self, avaliacao_id):
        try:
            return (
                Avaliacao.objects.select_related("aluno", "professor", "disciplina")
                .get(id=avaliacao_id)
            )
        except Avaliacao.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Avaliacao nao encontrada.") from exc

    def list(self):
        return (
            Avaliacao.objects.select_related("aluno", "professor", "disciplina")
            .order_by("-ano", "-semestre", "id")
        )

    def update(self, avaliacao_id, **campos):
        avaliacao = self.get(avaliacao_id)
        for campo, valor in campos.items():
            setattr(avaliacao, campo, valor)
        avaliacao.full_clean()
        avaliacao.save()
        return self.get(avaliacao.id)

    def delete(self, avaliacao_id):
        avaliacao = self.get(avaliacao_id)
        avaliacao.delete()
