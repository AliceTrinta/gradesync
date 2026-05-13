class GradeSyncError(Exception):
    """Erro base das regras de negocio do GradeSync."""


class EntidadeNaoEncontrada(GradeSyncError):
    pass


class SimulacaoIncompletaError(GradeSyncError):
    def __init__(self, erros):
        self.erros = erros
        super().__init__("A simulacao precisa estar completa para ser confirmada.")
