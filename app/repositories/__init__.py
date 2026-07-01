from .aluno_repository import AlunoRepository, UsuarioRepository
from .avaliacao_repository import AvaliacaoRepository
from .cargahoraria_repository import CargaHorariaRepository
from .disciplina_repository import DisciplinaRepository
from .grade_repository import GradeRepository
from .notificacao_repository import NotificacaoRepository
from .preferencia_repository import (
    PreferenciaAcessibilidadeRepository,
    PreferenciaContaRepository,
)
from .professor_repository import ProfessorRepository
from .roteiro_repository import RoteiroRepository
from .simulacao_repository import SimulacaoRepository
from .turma_repository import TurmaRepository

__all__ = [
    "AlunoRepository",
    "AvaliacaoRepository",
    "CargaHorariaRepository",
    "DisciplinaRepository",
    "GradeRepository",
    "NotificacaoRepository",
    "PreferenciaAcessibilidadeRepository",
    "PreferenciaContaRepository",
    "ProfessorRepository",
    "RoteiroRepository",
    "SimulacaoRepository",
    "TurmaRepository",
    "UsuarioRepository",
]
