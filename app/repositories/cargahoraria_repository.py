from app.exceptions import EntidadeNaoEncontrada
from app.models import CargaHoraria


class CargaHorariaRepository:
    def create(self, *, dia, hora_inicio, hora_final):
        carga_horaria = CargaHoraria(
            dia=dia,
            hora_inicio=hora_inicio,
            hora_final=hora_final,
        )
        carga_horaria.full_clean()
        carga_horaria.save()
        return self.get(carga_horaria.id)

    def get(self, carga_horaria_id):
        try:
            return CargaHoraria.objects.get(id=carga_horaria_id)
        except CargaHoraria.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Carga horaria nao encontrada.") from exc

    def list(self):
        return CargaHoraria.objects.order_by("dia", "hora_inicio", "id")

    def update(self, carga_horaria_id, **campos):
        carga_horaria = self.get(carga_horaria_id)
        for campo, valor in campos.items():
            setattr(carga_horaria, campo, valor)
        carga_horaria.full_clean()
        carga_horaria.save()
        return self.get(carga_horaria.id)

    def delete(self, carga_horaria_id):
        carga_horaria = self.get(carga_horaria_id)
        carga_horaria.delete()
