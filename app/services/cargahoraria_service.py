from app.repositories import CargaHorariaRepository


class CargaHorariaService:
    def __init__(self, carga_horaria_repository=None):
        self.carga_horaria_repository = (
            carga_horaria_repository or CargaHorariaRepository()
        )

    def criar_carga_horaria(self, *, dia, hora_inicio, hora_final):
        return self.carga_horaria_repository.create(
            dia=dia,
            hora_inicio=hora_inicio,
            hora_final=hora_final,
        )

    def obter_carga_horaria(self, carga_horaria_id):
        return self.carga_horaria_repository.get(carga_horaria_id)

    def listar_cargas_horarias(self):
        return self.carga_horaria_repository.list()

    def atualizar_carga_horaria(
        self,
        carga_horaria_id,
        *,
        dia=None,
        hora_inicio=None,
        hora_final=None,
    ):
        campos = {}
        if dia is not None:
            campos["dia"] = dia
        if hora_inicio is not None:
            campos["hora_inicio"] = hora_inicio
        if hora_final is not None:
            campos["hora_final"] = hora_final
        return self.carga_horaria_repository.update(carga_horaria_id, **campos)

    def excluir_carga_horaria(self, carga_horaria_id):
        return self.carga_horaria_repository.delete(carga_horaria_id)
