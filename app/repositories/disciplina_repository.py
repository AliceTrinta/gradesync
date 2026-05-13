from app.exceptions import EntidadeNaoEncontrada
from app.models import Disciplina


class DisciplinaRepository:
    def create(self, *, codigo, nome, taxa_de_reprovacao, pre_requisitos=None):
        disciplina = Disciplina(
            codigo=codigo,
            nome=nome,
            taxa_de_reprovacao=taxa_de_reprovacao,
        )
        disciplina.full_clean()
        disciplina.save()
        if pre_requisitos is not None:
            disciplina.pre_requisitos.set(pre_requisitos)
        return self.get(disciplina.id)

    def get(self, disciplina_id):
        try:
            return Disciplina.objects.prefetch_related("pre_requisitos").get(id=disciplina_id)
        except Disciplina.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Disciplina nao encontrada.") from exc

    def list(self):
        return Disciplina.objects.prefetch_related("pre_requisitos").order_by("codigo")

    def update(self, disciplina_id, *, pre_requisitos=None, **campos):
        disciplina = self.get(disciplina_id)
        for campo, valor in campos.items():
            setattr(disciplina, campo, valor)
        disciplina.full_clean()
        disciplina.save()
        if pre_requisitos is not None:
            disciplina.pre_requisitos.set(pre_requisitos)
        return self.get(disciplina.id)
