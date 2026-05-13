from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from app.models import (
    Aluno,
    Avaliacao,
    CargaHoraria,
    Disciplina,
    Grade,
    Professor,
    Simulacao,
    Turma,
)
from app.services import (
    AlunoService,
    AvaliacaoService,
    CargaHorariaService,
    DisciplinaService,
    GradeService,
    ProfessorService,
    SimulacaoService,
    TurmaService,
)


class BusinessFlowIntegrationTests(TestCase):
    def setUp(self):
        self.aluno_service = AlunoService()
        self.avaliacao_service = AvaliacaoService()
        self.carga_horaria_service = CargaHorariaService()
        self.disciplina_service = DisciplinaService()
        self.grade_service = GradeService()
        self.professor_service = ProfessorService()
        self.simulacao_service = SimulacaoService()
        self.turma_service = TurmaService()
        self.aluno = self.aluno_service.criar_aluno(
            matricula="2026002",
            username="aluno2",
            email="aluno2@example.com",
            password="senha-forte-de-teste",
        )
        self.professor = Professor.objects.create(nome="Professor Base", avaliacao=7)
        self.disciplina = Disciplina.objects.create(
            codigo="INF1040",
            nome="Arquitetura de Software",
            taxa_de_reprovacao=5,
        )
        self.carga_horaria = CargaHoraria.objects.create(
            dia="terca",
            hora_inicio=time(9, 0),
            hora_final=time(11, 0),
        )
        self.grade_origem = Grade.objects.create(periodo="2026.1", aluno=self.aluno)
        self.turma = Turma.objects.create(
            codigo="3WA",
            grade=self.grade_origem,
            disciplina=self.disciplina,
        )
        self.turma.carga_horarias.set([self.carga_horaria])

    def test_crud_completo_de_aluno(self):
        aluno = self.aluno_service.criar_aluno(
            matricula="2026003",
            username="aluno3",
            email="aluno3@example.com",
            password="senha-forte-de-teste",
        )

        obtido = self.aluno_service.obter_aluno(aluno.id)
        atualizada = self.aluno_service.atualizar_aluno(
            aluno.id,
            matricula="2026003A",
            usuario_campos={"first_name": "Maria"},
        )
        avaliacao = self.avaliacao_service.criar_avaliacao(
            ano=2026,
            semestre=1,
            nota=8.5,
            aluno=aluno,
            professor=self.professor,
            disciplina=self.disciplina,
        )
        grade = self.grade_service.criar_grade(
            periodo="2026.8",
            aluno=aluno,
            turmas=[self.turma],
        )
        simulacao = self.simulacao_service.criar_simulacao(
            periodo="2026.9",
            aluno=aluno,
            turmas=[self.turma],
        )
        alunos = list(self.aluno_service.listar_alunos())
        desativado = self.aluno_service.desativar_aluno(aluno.id)

        self.assertEqual(obtido.matricula, "2026003")
        self.assertEqual(atualizada.matricula, "2026003A")
        self.assertEqual(atualizada.usuario.first_name, "Maria")
        self.assertIn(self.aluno, alunos)
        self.assertFalse(desativado.ativo)
        self.assertEqual(str(desativado), "(DESATIVADO)")
        self.assertFalse(Aluno.objects.filter(id=aluno.id, ativo=True).exists())
        self.assertFalse(get_user_model().objects.get(id=aluno.usuario_id).is_active)
        self.assertFalse(Grade.objects.filter(id=grade.id).exists())
        self.assertFalse(Simulacao.objects.filter(id=simulacao.id).exists())
        self.assertTrue(Avaliacao.objects.filter(id=avaliacao.id, aluno=aluno).exists())

    def test_criacao_de_aluno_e_atomica_quando_a_matricula_e_invalida(self):
        with self.assertRaises(ValidationError):
            self.aluno_service.criar_aluno(
                matricula="   ",
                username="usuario-invalido",
                email="usuario-invalido@example.com",
                password="senha-forte-de-teste",
            )

        self.assertFalse(
            get_user_model().objects.filter(username="usuario-invalido").exists()
        )

    def test_atualizacao_de_aluno_e_atomica_quando_usuario_e_invalido(self):
        matricula_original = self.aluno.matricula

        with self.assertRaises(ValidationError):
            self.aluno_service.atualizar_aluno(
                self.aluno.id,
                matricula="2026999",
                usuario_campos={"username": ""},
            )

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.matricula, matricula_original)

    def test_atualizacao_de_senha_do_usuario_usa_hash_do_django(self):
        self.aluno_service.atualizar_aluno(
            self.aluno.id,
            usuario_campos={"password": "nova-senha-forte"},
        )

        self.aluno.usuario.refresh_from_db()
        self.assertTrue(self.aluno.usuario.check_password("nova-senha-forte"))

    def test_crud_completo_de_simulacao_rascunho(self):
        simulacao = self.simulacao_service.criar_simulacao(
            periodo="2026.2",
            aluno=self.aluno,
        )
        atualizada = self.simulacao_service.atualizar_simulacao(
            simulacao.id,
            periodo="2026.3",
            turmas=[self.turma],
        )
        obtida = self.simulacao_service.obter_simulacao(simulacao.id)
        simulacoes = list(self.simulacao_service.listar_simulacoes())
        self.simulacao_service.excluir_simulacao(simulacao.id)

        self.assertEqual(atualizada.periodo, "2026.3")
        self.assertEqual(list(obtida.turmas.all()), [self.turma])
        self.assertIn(obtida, simulacoes)
        self.assertFalse(Simulacao.objects.filter(id=simulacao.id).exists())

    def test_crud_completo_de_avaliacao(self):
        avaliacao = self.avaliacao_service.criar_avaliacao(
            ano=2026,
            semestre=1,
            nota=7.5,
            aluno=self.aluno,
            professor=self.professor,
            disciplina=self.disciplina,
        )
        atualizada = self.avaliacao_service.atualizar_avaliacao(
            avaliacao.id,
            nota=9.0,
        )
        obtida = self.avaliacao_service.obter_avaliacao(avaliacao.id)
        avaliacoes = list(self.avaliacao_service.listar_avaliacoes())
        self.avaliacao_service.excluir_avaliacao(avaliacao.id)

        self.assertEqual(atualizada.nota, 9.0)
        self.assertEqual(obtida.professor, self.professor)
        self.assertIn(obtida, avaliacoes)
        self.assertFalse(Avaliacao.objects.filter(id=avaliacao.id).exists())

    def test_crud_completo_de_carga_horaria(self):
        carga_horaria = self.carga_horaria_service.criar_carga_horaria(
            dia="quinta",
            hora_inicio=time(13, 0),
            hora_final=time(15, 0),
        )
        atualizada = self.carga_horaria_service.atualizar_carga_horaria(
            carga_horaria.id,
            dia="sexta",
        )
        obtida = self.carga_horaria_service.obter_carga_horaria(carga_horaria.id)
        cargas_horarias = list(self.carga_horaria_service.listar_cargas_horarias())
        self.carga_horaria_service.excluir_carga_horaria(carga_horaria.id)

        self.assertEqual(atualizada.dia, "sexta")
        self.assertEqual(obtida.hora_inicio, time(13, 0))
        self.assertIn(obtida, cargas_horarias)
        self.assertFalse(CargaHoraria.objects.filter(id=carga_horaria.id).exists())

    def test_crud_completo_de_disciplina_sem_delete(self):
        pre_requisito = self.disciplina_service.criar_disciplina(
            codigo="INF1000",
            nome="Fundamentos",
            taxa_de_reprovacao=12,
        )
        disciplina = self.disciplina_service.criar_disciplina(
            codigo="INF2001",
            nome="Qualidade",
            taxa_de_reprovacao=18,
            pre_requisitos=[pre_requisito],
        )
        atualizada = self.disciplina_service.atualizar_disciplina(
            disciplina.id,
            nome="Qualidade de Software",
            pre_requisitos=[],
        )
        obtida = self.disciplina_service.obter_disciplina(disciplina.id)
        disciplinas = list(self.disciplina_service.listar_disciplinas())

        self.assertEqual(atualizada.nome, "Qualidade de Software")
        self.assertEqual(list(obtida.pre_requisitos.all()), [])
        self.assertIn(obtida, disciplinas)

    def test_crud_completo_de_professor_sem_delete(self):
        professor = self.professor_service.criar_professor(
            nome="Professor CRUD",
            avaliacao=6.5,
        )
        atualizada = self.professor_service.atualizar_professor(
            professor.id,
            avaliacao=8.5,
        )
        obtido = self.professor_service.obter_professor(professor.id)
        professores = list(self.professor_service.listar_professores())

        self.assertEqual(atualizada.avaliacao, 8.5)
        self.assertEqual(obtido.nome, "Professor CRUD")
        self.assertIn(obtido, professores)

    def test_confirmacao_de_simulacao_cria_grade_com_turmas_copiadas(self):
        simulacao = self.simulacao_service.criar_simulacao(
            periodo="2026.2",
            aluno=self.aluno,
            turmas=[self.turma],
        )

        grade = self.simulacao_service.confirmar_simulacao(simulacao.id)
        turma_copiada = grade.turmas.get()

        self.assertEqual(grade.periodo, "2026.2")
        self.assertEqual(grade.aluno, self.aluno)
        self.assertNotEqual(turma_copiada.id, self.turma.id)
        self.assertEqual(turma_copiada.codigo, self.turma.codigo)
        self.assertEqual(turma_copiada.disciplina, self.disciplina)
        self.assertEqual(list(turma_copiada.carga_horarias.all()), [self.carga_horaria])
        self.assertFalse(Simulacao.objects.filter(id=simulacao.id).exists())

    def test_crud_completo_de_grade(self):
        grade = self.grade_service.criar_grade(
            periodo="2026.3",
            aluno=self.aluno,
            turmas=[self.turma],
        )
        atualizada = self.grade_service.atualizar_grade(
            grade.id,
            periodo="2026.4",
            turmas=[],
        )
        obtida = self.grade_service.obter_grade(grade.id)
        grades = list(self.grade_service.listar_grades())
        self.grade_service.excluir_grade(grade.id)

        self.assertEqual(atualizada.periodo, "2026.4")
        self.assertEqual(obtida.turmas.count(), 0)
        self.assertIn(obtida, grades)
        self.assertFalse(Grade.objects.filter(id=grade.id).exists())

    def test_crud_completo_de_turma(self):
        grade_destino = Grade.objects.create(periodo="2027.1", aluno=self.aluno)
        nova_carga_horaria = self.carga_horaria_service.criar_carga_horaria(
            dia="sabado",
            hora_inicio=time(8, 0),
            hora_final=time(10, 0),
        )
        turma = self.turma_service.criar_turma(
            codigo="4WB",
            grade=grade_destino,
            disciplina=self.disciplina,
            carga_horarias=[self.carga_horaria],
        )
        atualizada = self.turma_service.atualizar_turma(
            turma.id,
            codigo="4WC",
            carga_horarias=[nova_carga_horaria],
        )
        obtida = self.turma_service.obter_turma(turma.id)
        turmas = list(self.turma_service.listar_turmas())
        self.turma_service.excluir_turma(turma.id)

        self.assertEqual(atualizada.codigo, "4WC")
        self.assertEqual(list(obtida.carga_horarias.all()), [nova_carga_horaria])
        self.assertIn(obtida, turmas)
        self.assertFalse(Turma.objects.filter(id=turma.id).exists())
