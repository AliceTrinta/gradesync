from .ai_service import AIService
from .aluno_service import AlunoService
from .avaliacao_service import AvaliacaoService
from .cargahoraria_service import CargaHorariaService
from .desempenho_service import DesempenhoService
from .disciplina_service import DisciplinaService
from .grade_service import GradeService
from .notificacao_service import NotificacaoService
from .preferencia_service import (
    PreferenciaAcessibilidadeService,
    PreferenciaContaService,
)
from .professor_service import ProfessorService
from .roteiro_service import RoteiroService
from .simulacao_service import SimulacaoService
from .turma_service import TurmaService

__all__ = [
    "AIService",
    "AlunoService",
    "AvaliacaoService",
    "CargaHorariaService",
    "DesempenhoService",
    "DisciplinaService",
    "GradeService",
    "NotificacaoService",
    "PreferenciaAcessibilidadeService",
    "PreferenciaContaService",
    "ProfessorService",
    "RoteiroService",
    "SimulacaoService",
    "TurmaService",
]
