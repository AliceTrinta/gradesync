class GradeSyncError(Exception):
    pass


class EntidadeNaoEncontrada(GradeSyncError):
    pass


class SimulacaoIncompletaError(GradeSyncError):
    def __init__(self, erros):
        self.erros = erros
        super().__init__("A simulacao precisa estar completa para ser confirmada.")


class PrerequisitoNaoAtendidoError(GradeSyncError):
    def __init__(self, disciplina, faltantes):
        self.disciplina = disciplina
        self.faltantes = list(faltantes)
        nomes = ", ".join(str(d) for d in self.faltantes)
        super().__init__(
            f"Nao e possivel cursar {disciplina}: pre-requisitos faltantes ({nomes})."
        )


class ConflitoDeHorarioError(GradeSyncError):
    def __init__(self, turma_a, turma_b, carga_a, carga_b):
        self.turma_a = turma_a
        self.turma_b = turma_b
        self.carga_a = carga_a
        self.carga_b = carga_b
        super().__init__(
            f"Conflito de horario entre {turma_a} e {turma_b} "
            f"em {carga_a.dia} ({carga_a.hora_inicio}-{carga_a.hora_final} vs "
            f"{carga_b.hora_inicio}-{carga_b.hora_final})."
        )


class RoteiroSemGradeError(GradeSyncError):
    def __init__(self):
        super().__init__(
            "O roteiro de estudos precisa de uma grade do semestre. "
            "Crie sua grade antes de gerar o roteiro."
        )


class BlocoRoteiroInvalidoError(GradeSyncError):
    pass


class BlocoConflitaComGradeError(GradeSyncError):
    def __init__(self, *, dia, hora_inicio, hora_final, disciplina_codigo):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_final = hora_final
        self.disciplina_codigo = disciplina_codigo
        super().__init__(
            f"O bloco em {dia} ({hora_inicio}-{hora_final}) conflita "
            f"com a disciplina {disciplina_codigo} da sua grade."
        )


class AIProviderError(GradeSyncError):
    """Erro generico do provedor de IA (rede, auth, resposta malformada)."""


class AITimeoutError(AIProviderError):
    def __init__(self, *, provedor, segundos):
        self.provedor = provedor
        self.segundos = segundos
        super().__init__(f"Timeout ({segundos}s) ao consultar {provedor}.")


class AIQuotaExceededError(AIProviderError):
    def __init__(self, *, provedor, motivo=None):
        self.provedor = provedor
        self.motivo = motivo
        base = f"Cota do provedor {provedor} foi excedida."
        if motivo:
            base += f" ({motivo})"
        super().__init__(base)


class AIRespostaInvalidaError(AIProviderError):
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(f"Resposta invalida da IA: {motivo}")
