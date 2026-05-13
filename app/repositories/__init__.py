from .avaliacao_repository import AvaliacaoRepository
from .aluno_repository import AlunoRepository, UsuarioRepository
from .cargahoraria_repository import CargaHorariaRepository
from .disciplina_repository import DisciplinaRepository
from .grade_repository import GradeRepository
from .professor_repository import ProfessorRepository
from .simulacao_repository import SimulacaoRepository
from .turma_repository import TurmaRepository

__all__ = [
    "AvaliacaoRepository",
    "AlunoRepository",
    "CargaHorariaRepository",
    "DisciplinaRepository",
    "GradeRepository",
    "ProfessorRepository",
    "SimulacaoRepository",
    "TurmaRepository",
    "UsuarioRepository",
]
