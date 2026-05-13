from app.exceptions import EntidadeNaoEncontrada
from app.models import Professor


class ProfessorRepository:
    def create(self, *, nome, avaliacao):
        professor = Professor(nome=nome, avaliacao=avaliacao)
        professor.full_clean()
        professor.save()
        return self.get(professor.id)

    def get(self, professor_id):
        try:
            return Professor.objects.get(id=professor_id)
        except Professor.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Professor nao encontrado.") from exc

    def list(self):
        return Professor.objects.order_by("nome", "id")

    def update(self, professor_id, **campos):
        professor = self.get(professor_id)
        for campo, valor in campos.items():
            setattr(professor, campo, valor)
        professor.full_clean()
        professor.save()
        return self.get(professor.id)
