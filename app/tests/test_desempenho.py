"""Testes das regras de negocio: desempenho, pre-requisitos, conflito."""
from datetime import time
from decimal import Decimal

from django.test import TestCase

from app.exceptions import (
    ConflitoDeHorarioError,
    PrerequisitoNaoAtendidoError,
)
from app.models import (
    Avaliacao,
    CargaHoraria,
    Disciplina,
    Grade,
    Professor,
    Turma,
)
from app.services import (
    AlunoService,
    DesempenhoService,
    SimulacaoService,
)


class DesempenhoServiceTests(TestCase):
    def setUp(self):
        self.aluno = AlunoService().criar_aluno(
            matricula="D001",
            username="d_aluno",
            password="senha-forte-999",
            email="d@example.com",
            first_name="D",
        )
        self.professor = Professor.objects.create(nome="Prof X", avaliacao=Decimal("9.0"))
        self.calc = Disciplina.objects.create(
            codigo="MAC101",
            nome="Calculo I",
            taxa_de_reprovacao=Decimal("30.00"),
        )
        self.alg = Disciplina.objects.create(
            codigo="MAC102",
            nome="Algebra",
            taxa_de_reprovacao=Decimal("20.00"),
        )
        self.service = DesempenhoService()

    def _criar_avaliacao(self, disciplina, nota, ano=2026, semestre=1):
        return Avaliacao.objects.create(
            aluno=self.aluno,
            professor=self.professor,
            disciplina=disciplina,
            nota=Decimal(str(nota)),
            ano=ano,
            semestre=semestre,
        )

    def test_media_disciplina_com_multiplas_avaliacoes(self):
        self._criar_avaliacao(self.calc, 6)
        self._criar_avaliacao(self.calc, 8)
        self._criar_avaliacao(self.calc, 7)

        media = self.service.calcular_media_disciplina(
            aluno=self.aluno, disciplina=self.calc
        )
        self.assertEqual(media, Decimal("7.00"))

    def test_media_disciplina_sem_avaliacoes_retorna_none(self):
        media = self.service.calcular_media_disciplina(
            aluno=self.aluno, disciplina=self.calc
        )
        self.assertIsNone(media)

    def test_cr_periodo_media_do_semestre(self):
        self._criar_avaliacao(self.calc, 8, semestre=1)
        self._criar_avaliacao(self.alg, 6, semestre=1)
        self._criar_avaliacao(self.calc, 10, semestre=2)

        cr = self.service.calcular_cr_periodo(
            aluno=self.aluno, ano=2026, semestre=1
        )
        self.assertEqual(cr, Decimal("7.00"))

    def test_cra_media_geral(self):
        self._criar_avaliacao(self.calc, 5)
        self._criar_avaliacao(self.alg, 9)

        cra = self.service.calcular_cra(aluno=self.aluno)
        self.assertEqual(cra, Decimal("7.00"))

    def test_listar_medias_por_disciplina(self):
        self._criar_avaliacao(self.calc, 6)
        self._criar_avaliacao(self.calc, 8)
        self._criar_avaliacao(self.alg, 9)

        resultado = self.service.listar_medias_por_disciplina(aluno=self.aluno)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]["disciplina"], self.calc)
        self.assertEqual(resultado[0]["media"], Decimal("7.00"))
        self.assertEqual(resultado[0]["qtd_avaliacoes"], 2)
        self.assertEqual(resultado[1]["disciplina"], self.alg)
        self.assertEqual(resultado[1]["media"], Decimal("9.00"))


class SimulacaoPrerequisitoTests(TestCase):
    def setUp(self):
        self.aluno = AlunoService().criar_aluno(
            matricula="P001",
            username="p_aluno",
            password="senha-forte-999",
            email="p@example.com",
            first_name="P",
        )
        self.professor = Professor.objects.create(nome="Prof", avaliacao=Decimal("8"))
        self.calc1 = Disciplina.objects.create(
            codigo="CALC1", nome="Calc I", taxa_de_reprovacao=Decimal("30")
        )
        self.calc2 = Disciplina.objects.create(
            codigo="CALC2", nome="Calc II", taxa_de_reprovacao=Decimal("40")
        )
        self.calc2.pre_requisitos.add(self.calc1)
        self.service = SimulacaoService()

    def test_prerequisito_atendido_passa_sem_erro(self):
        Avaliacao.objects.create(
            aluno=self.aluno,
            professor=self.professor,
            disciplina=self.calc1,
            nota=Decimal("7"),
            ano=2025,
            semestre=2,
        )
        self.service.validar_prerequisitos(aluno=self.aluno, disciplina=self.calc2)

    def test_prerequisito_nao_atendido_levanta_excecao(self):
        with self.assertRaises(PrerequisitoNaoAtendidoError) as ctx:
            self.service.validar_prerequisitos(aluno=self.aluno, disciplina=self.calc2)

        self.assertEqual(ctx.exception.disciplina, self.calc2)
        self.assertIn(self.calc1, ctx.exception.faltantes)

    def test_prerequisito_reprovado_levanta_excecao(self):
        Avaliacao.objects.create(
            aluno=self.aluno,
            professor=self.professor,
            disciplina=self.calc1,
            nota=Decimal("3"),
            ano=2025,
            semestre=2,
        )
        with self.assertRaises(PrerequisitoNaoAtendidoError):
            self.service.validar_prerequisitos(aluno=self.aluno, disciplina=self.calc2)

    def test_disciplina_sem_prerequisitos_passa(self):
        self.service.validar_prerequisitos(aluno=self.aluno, disciplina=self.calc1)


class SimulacaoConflitoHorarioTests(TestCase):
    def setUp(self):
        self.aluno = AlunoService().criar_aluno(
            matricula="C001",
            username="c_aluno",
            password="senha-forte-999",
            email="c@example.com",
            first_name="C",
        )
        self.grade = Grade.objects.create(periodo="2026.1", aluno=self.aluno)
        self.d1 = Disciplina.objects.create(
            codigo="D1", nome="Um", taxa_de_reprovacao=Decimal("10")
        )
        self.d2 = Disciplina.objects.create(
            codigo="D2", nome="Dois", taxa_de_reprovacao=Decimal("10")
        )
        self.service = SimulacaoService()

    def _turma_com_horario(self, disciplina, codigo, dia, hi, hf):
        turma = Turma.objects.create(
            codigo=codigo,
            grade=self.grade,
            disciplina=disciplina,
        )
        carga = CargaHoraria.objects.create(
            dia=dia, hora_inicio=hi, hora_final=hf
        )
        turma.carga_horarias.add(carga)
        return turma

    def test_sem_conflito_horarios_diferentes(self):
        t1 = self._turma_com_horario(self.d1, "T1", "seg", time(8), time(10))
        t2 = self._turma_com_horario(self.d2, "T2", "seg", time(10), time(12))
        self.service.detectar_conflito_horario(turmas=[t1, t2])

    def test_sem_conflito_dias_diferentes(self):
        t1 = self._turma_com_horario(self.d1, "T1", "seg", time(8), time(10))
        t2 = self._turma_com_horario(self.d2, "T2", "ter", time(8), time(10))
        self.service.detectar_conflito_horario(turmas=[t1, t2])

    def test_conflito_sobreposicao_parcial(self):
        t1 = self._turma_com_horario(self.d1, "T1", "seg", time(8), time(10))
        t2 = self._turma_com_horario(self.d2, "T2", "seg", time(9), time(11))
        with self.assertRaises(ConflitoDeHorarioError):
            self.service.detectar_conflito_horario(turmas=[t1, t2])

    def test_conflito_sobreposicao_total(self):
        t1 = self._turma_com_horario(self.d1, "T1", "qua", time(14), time(18))
        t2 = self._turma_com_horario(self.d2, "T2", "qua", time(15), time(17))
        with self.assertRaises(ConflitoDeHorarioError):
            self.service.detectar_conflito_horario(turmas=[t1, t2])

    def test_dias_case_insensitive(self):
        t1 = self._turma_com_horario(self.d1, "T1", "Sexta", time(8), time(10))
        t2 = self._turma_com_horario(self.d2, "T2", "sexta", time(9), time(11))
        with self.assertRaises(ConflitoDeHorarioError):
            self.service.detectar_conflito_horario(turmas=[t1, t2])
