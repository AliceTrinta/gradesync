from types import SimpleNamespace
from unittest.mock import Mock

from django.test import TestCase

from app.exceptions import SimulacaoIncompletaError
from app.services import AlunoService, GradeService, SimulacaoService


class BusinessRuleUnitTests(TestCase):
    def test_confirmacao_rejeita_simulacao_incompleta_com_repositorios_mockados(self):
        simulacao_repository = Mock()
        grade_repository = Mock()
        simulacao_repository.get.return_value = SimpleNamespace(
            periodo="2026.2",
            aluno=SimpleNamespace(id="aluno-id"),
            turmas=[],
        )
        service = SimulacaoService(
            simulacao_repository=simulacao_repository,
            grade_repository=grade_repository,
        )

        with self.assertRaises(SimulacaoIncompletaError) as contexto:
            service.confirmar_simulacao("simulacao-id")

        self.assertEqual(set(contexto.exception.erros.keys()), {"turmas"})
        grade_repository.create.assert_not_called()
        simulacao_repository.delete.assert_not_called()

    def test_criacao_de_simulacao_exige_aluno_e_periodo_no_servico(self):
        simulacao_repository = Mock()
        aluno = SimpleNamespace(id="aluno-id")
        simulacao_repository.create.return_value = SimpleNamespace(
            id="simulacao-id",
            periodo="2026.2",
            aluno=aluno,
        )
        service = SimulacaoService(simulacao_repository=simulacao_repository)

        resultado = service.criar_simulacao(periodo="2026.2", aluno=aluno)

        simulacao_repository.create.assert_called_once_with(
            periodo="2026.2",
            aluno=aluno,
            turmas=None,
        )
        self.assertEqual(resultado.periodo, "2026.2")

    def test_confirmacao_de_simulacao_remove_rascunho_apos_criar_grade(self):
        simulacao_repository = Mock()
        grade_repository = Mock()
        aluno = SimpleNamespace(id="aluno-id")
        turma = SimpleNamespace()
        simulacao = SimpleNamespace(
            id="simulacao-id",
            periodo="2026.2",
            aluno=aluno,
            turmas=[turma],
        )
        grade = SimpleNamespace(id="grade-id")
        simulacao_repository.get.return_value = simulacao
        grade_repository.create.return_value = grade
        service = SimulacaoService(
            simulacao_repository=simulacao_repository,
            grade_repository=grade_repository,
        )

        resultado = service.confirmar_simulacao(simulacao.id)

        grade_repository.create.assert_called_once_with(
            periodo="2026.2",
            aluno=aluno,
            turmas=[turma],
        )
        simulacao_repository.delete.assert_called_once_with(simulacao.id)
        self.assertEqual(resultado, grade)

    def test_criacao_de_aluno_usa_usuario_existente_ou_cria_usuario_mockado(self):
        usuario = SimpleNamespace(username="aluno1")
        aluno = SimpleNamespace(usuario=usuario, matricula="2026001")
        usuario_repository = Mock()
        aluno_repository = Mock()
        usuario_repository.create_user.return_value = usuario
        aluno_repository.create.return_value = aluno
        service = AlunoService(
            aluno_repository=aluno_repository,
            usuario_repository=usuario_repository,
        )

        resultado = service.criar_aluno(
            matricula="2026001",
            username="aluno1",
            password="senha-forte-de-teste",
        )

        usuario_repository.create_user.assert_called_once_with(
            username="aluno1",
            password="senha-forte-de-teste",
            email="",
            first_name="",
            last_name="",
        )
        aluno_repository.create.assert_called_once_with(
            usuario=usuario,
            matricula="2026001",
        )
        self.assertEqual(resultado.matricula, "2026001")

    def test_desativacao_de_aluno_delega_para_repositorio(self):
        aluno_repository = Mock()
        usuario_repository = Mock()
        service = AlunoService(
            aluno_repository=aluno_repository,
            usuario_repository=usuario_repository,
        )

        service.desativar_aluno("aluno-id")

        aluno_repository.deactivate.assert_called_once_with("aluno-id")

    def test_crud_de_grade_delega_para_repositorio_mockado(self):
        grade_repository = Mock()
        grade_repository.create.return_value = SimpleNamespace(id="grade-id")
        grade_repository.get.return_value = SimpleNamespace(id="grade-id")
        grade_repository.list.return_value = []
        grade_repository.update.return_value = SimpleNamespace(periodo="2026.2")
        service = GradeService(grade_repository=grade_repository)
        aluno = SimpleNamespace(id="aluno-id")

        service.criar_grade(periodo="2026.1", aluno=aluno, turmas=[])
        service.obter_grade("grade-id")
        service.listar_grades()
        resultado = service.atualizar_grade("grade-id", periodo="2026.2")
        service.excluir_grade("grade-id")

        grade_repository.create.assert_called_once_with(
            periodo="2026.1",
            aluno=aluno,
            turmas=[],
        )
        grade_repository.get.assert_called_once_with("grade-id")
        grade_repository.list.assert_called_once_with()
        grade_repository.update.assert_called_once_with(
            "grade-id",
            turmas=None,
            periodo="2026.2",
        )
        grade_repository.delete.assert_called_once_with("grade-id")
        self.assertEqual(resultado.periodo, "2026.2")
