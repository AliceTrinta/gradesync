from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from app.models import Aluno, Avaliacao, CargaHoraria, Disciplina, Grade, Professor, Simulacao


class EntityValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aluno1",
            email="aluno1@example.com",
            password="senha-forte-de-teste",
        )
        self.aluno = Aluno.objects.create(usuario=self.user, matricula="2026001")
        self.disciplina = Disciplina.objects.create(
            codigo="INF1039",
            nome="Projeto de Software",
            taxa_de_reprovacao=0,
        )
        self.professor = Professor.objects.create(nome="Professor Teste", avaliacao=8)
        self.grade = Grade.objects.create(periodo="2026.1", aluno=self.aluno)

    def test_aluno_usa_senha_do_usuario_django(self):
        self.assertFalse(hasattr(self.aluno, "senha"))
        self.assertTrue(self.user.check_password("senha-forte-de-teste"))

    def test_avaliacao_rejeita_nota_fora_da_escala(self):
        avaliacao = Avaliacao(
            ano=2026,
            semestre=1,
            nota=11,
            aluno=self.aluno,
            professor=self.professor,
            disciplina=self.disciplina,
        )

        with self.assertRaises(ValidationError):
            avaliacao.full_clean()

    def test_avaliacao_exige_professor_e_disciplina(self):
        avaliacao = Avaliacao(
            ano=2026,
            semestre=1,
            nota=8,
            aluno=self.aluno,
        )

        with self.assertRaises(ValidationError):
            avaliacao.full_clean()

    def test_carga_horaria_rejeita_intervalo_invalido(self):
        carga_horaria = CargaHoraria(
            dia="segunda",
            hora_inicio=time(10, 0),
            hora_final=time(9, 0),
        )

        with self.assertRaises(ValidationError):
            carga_horaria.full_clean()

    def test_campos_textuais_sao_normalizados(self):
        disciplina = Disciplina(
            codigo="  INF2000  ",
            nome="  Testes de Software  ",
            taxa_de_reprovacao=10,
        )
        carga_horaria = CargaHoraria(
            dia="  quarta  ",
            hora_inicio=time(8, 0),
            hora_final=time(10, 0),
        )

        disciplina.full_clean()
        carga_horaria.full_clean()

        self.assertEqual(disciplina.codigo, "INF2000")
        self.assertEqual(disciplina.nome, "Testes de Software")
        self.assertEqual(carga_horaria.dia, "quarta")

    def test_simulacao_rascunho_exige_aluno_e_periodo_mas_nao_turmas(self):
        simulacao = Simulacao.objects.create(periodo="2026.2", aluno=self.aluno)

        self.assertEqual(simulacao.periodo, "2026.2")
        self.assertEqual(simulacao.aluno, self.aluno)
        self.assertEqual(simulacao.turmas.count(), 0)

    def test_simulacao_rejeita_periodo_vazio(self):
        simulacao = Simulacao(periodo="", aluno=self.aluno)

        with self.assertRaises(ValidationError):
            simulacao.full_clean()
