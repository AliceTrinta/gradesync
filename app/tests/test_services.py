from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase

from app.exceptions import (
    BlocoConflitaComGradeError,
    BlocoRoteiroInvalidoError,
    RoteiroSemGradeError,
    SimulacaoIncompletaError,
)
from app.services import AlunoService, GradeService, RoteiroService, SimulacaoService
from app.views import (
    HORAS_GRADE,
    _grid_da_grade,
    _grid_do_roteiro,
    _horas_no_intervalo,
)


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


class RoteiroServiceRegraDeGradeTests(TestCase):
    """Regra de negocio 'roteiro exige grade'."""

    def test_gerar_roteiro_padrao_sem_grade_levanta_erro(self):
        roteiro_repository = Mock()
        service = RoteiroService(roteiro_repository=roteiro_repository)
        aluno = SimpleNamespace(id="aluno-id")

        with self.assertRaises(RoteiroSemGradeError):
            service.gerar_roteiro_padrao(aluno=aluno, grade=None)

        roteiro_repository.upsert_by_aluno.assert_not_called()

    def test_gerar_roteiro_padrao_com_grade_vazia_salva_slots_vazios(self):
        roteiro_repository = Mock()
        service = RoteiroService(roteiro_repository=roteiro_repository)
        aluno = SimpleNamespace(id="aluno-id")

        turmas_manager = Mock()
        turmas_manager.select_related.return_value = turmas_manager
        turmas_manager.all.return_value = []
        grade = SimpleNamespace(periodo="2026.1", turmas=turmas_manager)

        service.gerar_roteiro_padrao(aluno=aluno, grade=grade)

        roteiro_repository.upsert_by_aluno.assert_called_once()
        chamada = roteiro_repository.upsert_by_aluno.call_args
        slots = chamada.kwargs.get("slots")
        self.assertEqual(slots, [])


class HorasNoIntervaloTests(TestCase):
    """Helper que expande um bloco (inicio, fim) nas horas cheias que ele cobre."""

    def test_bloco_de_2_horas_retorna_2_slots(self):
        from datetime import time

        self.assertEqual(
            _horas_no_intervalo(time(8, 0), time(10, 0)),
            ["08:00", "09:00"],
        )

    def test_bloco_de_4_horas_retorna_4_slots(self):
        from datetime import time

        self.assertEqual(
            _horas_no_intervalo(time(14, 0), time(18, 0)),
            ["14:00", "15:00", "16:00", "17:00"],
        )

    def test_bloco_de_1_hora_retorna_1_slot(self):
        from datetime import time

        self.assertEqual(
            _horas_no_intervalo(time(9, 0), time(10, 0)),
            ["09:00"],
        )

    def test_aceita_strings_alem_de_time(self):
        self.assertEqual(
            _horas_no_intervalo("16:00", "18:00"),
            ["16:00", "17:00"],
        )

    def test_intervalo_invalido_retorna_1_hora_inicial(self):
        from datetime import time

        self.assertEqual(_horas_no_intervalo(time(10, 0), time(9, 0)), ["10:00"])
        self.assertEqual(_horas_no_intervalo(time(10, 0), time(10, 0)), ["10:00"])

    def test_horas_grade_cobre_ate_18h(self):
        self.assertIn("08:00", HORAS_GRADE)
        self.assertIn("17:00", HORAS_GRADE)
        self.assertNotIn("18:00", HORAS_GRADE)
        self.assertEqual(len(HORAS_GRADE), 10)


class GridDaGradeTests(TestCase):
    """Pivot semanal do grade_detalhe: cada carga vira N celulas consecutivas."""

    def _mock_grade(self, turmas):
        turmas_manager = Mock()
        turmas_manager.all.return_value = turmas
        return SimpleNamespace(turmas=turmas_manager)

    def _mock_turma(self, codigo, nome, cargas, disc_id="d1"):
        from datetime import time

        cargas_ns = []
        for dia, ini_h, fim_h in cargas:
            cargas_ns.append(
                SimpleNamespace(
                    dia=dia,
                    hora_inicio=time(ini_h, 0),
                    hora_final=time(fim_h, 0),
                )
            )
        cargas_manager = Mock()
        cargas_manager.all.return_value = cargas_ns
        return SimpleNamespace(
            disciplina_id=disc_id,
            disciplina=SimpleNamespace(codigo=codigo, nome=nome),
            carga_horarias=cargas_manager,
        )

    def _celulas_preenchidas(self, grid):
        return [(row["hora"], idx, cell) for row in grid for idx, cell in enumerate(row["cells"]) if cell]

    def test_grade_vazia_retorna_lista_vazia(self):
        self.assertEqual(_grid_da_grade(None), [])

    def test_carga_de_2_horas_ocupa_2_linhas_consecutivas(self):
        turma = self._mock_turma("CC-201", "Algoritmos", [("segunda", 8, 10)])
        grid = _grid_da_grade(self._mock_grade([turma]))

        preenchidas = self._celulas_preenchidas(grid)
        self.assertEqual(len(preenchidas), 2)

        hora_head, col_head, cell_head = preenchidas[0]
        hora_tail, col_tail, cell_tail = preenchidas[1]

        self.assertEqual(hora_head, "08:00")
        self.assertEqual(hora_tail, "09:00")
        self.assertEqual(col_head, 0)
        self.assertEqual(col_tail, 0)

        self.assertTrue(cell_head["is_head"])
        self.assertFalse(cell_head["is_tail"])
        self.assertFalse(cell_tail["is_head"])
        self.assertTrue(cell_tail["is_tail"])

        self.assertEqual(cell_head["hora_inicio"], "08:00")
        self.assertEqual(cell_head["hora_final"], "10:00")
        self.assertEqual(cell_tail["hora_inicio"], "08:00")
        self.assertEqual(cell_tail["hora_final"], "10:00")

    def test_disciplina_com_2_cargas_gera_4_celulas(self):
        turma = self._mock_turma(
            "CC-202",
            "Estrutura",
            [("terca", 8, 10), ("quinta", 16, 18)],
        )
        grid = _grid_da_grade(self._mock_grade([turma]))
        preenchidas = self._celulas_preenchidas(grid)

        self.assertEqual(len(preenchidas), 4)

        cores = {cell["cor"] for _, _, cell in preenchidas}
        self.assertEqual(len(cores), 1, "mesma disciplina => mesma cor em todas as celulas")

        chaves = {(hora, col) for hora, col, _ in preenchidas}
        self.assertEqual(
            chaves,
            {("08:00", 1), ("09:00", 1), ("16:00", 3), ("17:00", 3)},
        )

    def test_quinta_16h_ao_18h_agora_aparece_no_grid(self):
        turma = self._mock_turma("CC-202", "Estrutura", [("quinta", 16, 18)])
        grid = _grid_da_grade(self._mock_grade([turma]))
        chaves = {(row["hora"], idx) for row in grid for idx, c in enumerate(row["cells"]) if c}

        self.assertIn(("16:00", 3), chaves)
        self.assertIn(("17:00", 3), chaves)

    def test_duas_disciplinas_recebem_cores_diferentes(self):
        turma_a = self._mock_turma(
            "CC-201", "Algoritmos", [("segunda", 8, 10)], disc_id="da"
        )
        turma_b = self._mock_turma(
            "CC-202", "Estrutura", [("terca", 8, 10)], disc_id="db"
        )
        grid = _grid_da_grade(self._mock_grade([turma_a, turma_b]))
        preenchidas = self._celulas_preenchidas(grid)

        cor_a = next(c["cor"] for _, _, c in preenchidas if c["codigo"] == "CC-201")
        cor_b = next(c["cor"] for _, _, c in preenchidas if c["codigo"] == "CC-202")
        self.assertNotEqual(cor_a, cor_b)


class GridDoRoteiroTests(TestCase):
    """Pivot semanal do roteiro: slots com hora_inicio/hora_final em string."""

    def test_roteiro_vazio_retorna_lista_vazia(self):
        self.assertEqual(_grid_do_roteiro(None), [])
        self.assertEqual(
            _grid_do_roteiro(SimpleNamespace(slots=[])),
            [],
        )

    def test_slot_de_2_horas_ocupa_2_linhas(self):
        roteiro = SimpleNamespace(
            slots=[
                {
                    "dia": "seg",
                    "hora_inicio": "08:00",
                    "hora_final": "10:00",
                    "titulo": "Estudar CC-201",
                    "cor": "blue",
                }
            ]
        )
        grid = _grid_do_roteiro(roteiro)
        preenchidas = [
            (row["hora"], cell)
            for row in grid
            for cell in row["cells"]
            if cell
        ]
        self.assertEqual(len(preenchidas), 2)

        (h1, c1), (h2, c2) = preenchidas
        self.assertEqual(h1, "08:00")
        self.assertEqual(h2, "09:00")
        self.assertTrue(c1["is_head"])
        self.assertTrue(c2["is_tail"])
        self.assertEqual(c1["titulo"], "Estudar CC-201")
        self.assertEqual(c2["titulo"], "Estudar CC-201")


class NormalizadoresRoteiroTests(TestCase):
    """Helpers de modulo usados pelo editor de blocos do roteiro."""

    def test_normalizar_dia_aceita_prefixo_de_3_letras(self):
        from app.services.roteiro_service import _normalizar_dia
        self.assertEqual(_normalizar_dia("segunda"), "seg")
        self.assertEqual(_normalizar_dia("QUINTA"), "qui")
        self.assertEqual(_normalizar_dia(" sex "), "sex")

    def test_normalizar_dia_vazio_ou_none_retorna_string_vazia(self):
        from app.services.roteiro_service import _normalizar_dia
        self.assertEqual(_normalizar_dia(None), "")
        self.assertEqual(_normalizar_dia(""), "")

    def test_normalizar_hora_aceita_objeto_time(self):
        from datetime import time
        from app.services.roteiro_service import _normalizar_hora
        self.assertEqual(_normalizar_hora(time(8, 0)), "08:00")
        self.assertEqual(_normalizar_hora(time(14, 30)), "14:30")

    def test_normalizar_hora_aceita_string_hhmm(self):
        from app.services.roteiro_service import _normalizar_hora
        self.assertEqual(_normalizar_hora("09:00"), "09:00")
        self.assertEqual(_normalizar_hora(" 15:45 "), "15:45")

    def test_normalizar_hora_rejeita_vazio(self):
        from app.services.roteiro_service import _normalizar_hora
        with self.assertRaises(BlocoRoteiroInvalidoError):
            _normalizar_hora("")
        with self.assertRaises(BlocoRoteiroInvalidoError):
            _normalizar_hora(None)

    def test_normalizar_hora_rejeita_formato_invalido(self):
        from app.services.roteiro_service import _normalizar_hora
        with self.assertRaises(BlocoRoteiroInvalidoError):
            _normalizar_hora("25:99")
        with self.assertRaises(BlocoRoteiroInvalidoError):
            _normalizar_hora("8h")

    def test_intervalos_se_sobrepoem_detecta_overlap_parcial(self):
        from app.services.roteiro_service import _intervalos_se_sobrepoem
        self.assertTrue(_intervalos_se_sobrepoem("08:00", "10:00", "09:00", "11:00"))

    def test_intervalos_se_sobrepoem_detecta_intervalo_contido(self):
        from app.services.roteiro_service import _intervalos_se_sobrepoem
        self.assertTrue(_intervalos_se_sobrepoem("08:00", "12:00", "09:00", "10:00"))

    def test_intervalos_se_sobrepoem_ignora_intervalos_adjacentes(self):
        from app.services.roteiro_service import _intervalos_se_sobrepoem
        self.assertFalse(_intervalos_se_sobrepoem("08:00", "10:00", "10:00", "12:00"))
        self.assertFalse(_intervalos_se_sobrepoem("10:00", "12:00", "08:00", "10:00"))


class RoteiroEditorBlocoUnitTests(TestCase):
    """Editor de blocos do roteiro isolado com repository e Turma mockados."""

    def _service_com_repo(self, slots=None):
        repo = Mock()
        roteiro = SimpleNamespace(id="rot-1", slots=list(slots or []))
        repo.get_by_aluno.return_value = roteiro
        repo.update.side_effect = lambda rid, **kw: SimpleNamespace(
            id=rid, slots=kw.get("slots", roteiro.slots),
        )
        repo.create.side_effect = lambda **kw: SimpleNamespace(
            id="rot-1", slots=kw.get("slots", []),
        )
        service = RoteiroService(roteiro_repository=repo)
        return service, repo, roteiro

    def _stub_sem_turmas(self, turma_mock):
        chain = turma_mock.objects.filter.return_value
        chain.select_related.return_value.prefetch_related.return_value = []

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_valido_grava_slot_com_id(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        service, repo, _ = self._service_com_repo()

        service.adicionar_bloco(
            SimpleNamespace(id="a"),
            dia="seg",
            hora_inicio="14:00",
            hora_final="16:00",
            titulo="Revisar Calculo",
            cor="green",
        )
        repo.update.assert_called_once()
        _, kwargs = repo.update.call_args
        slots = kwargs["slots"]
        self.assertEqual(len(slots), 1)
        bloco = slots[0]
        self.assertTrue(bloco["id"])  # uuid4.hex nao vazio
        self.assertEqual(bloco["dia"], "seg")
        self.assertEqual(bloco["hora_inicio"], "14:00")
        self.assertEqual(bloco["hora_final"], "16:00")
        self.assertEqual(bloco["titulo"], "Revisar Calculo")
        self.assertEqual(bloco["cor"], "green")

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_cria_roteiro_quando_ainda_nao_existe(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        repo = Mock()
        repo.get_by_aluno.return_value = None
        repo.create.return_value = SimpleNamespace(id="rot-novo", slots=[])
        repo.update.return_value = SimpleNamespace(id="rot-novo", slots=[])
        service = RoteiroService(roteiro_repository=repo)

        service.adicionar_bloco(
            SimpleNamespace(id="a"),
            dia="qua",
            hora_inicio="09:00",
            hora_final="10:00",
            titulo="Ler",
        )
        repo.create.assert_called_once()
        repo.update.assert_called_once()

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_com_dia_invalido_levanta_erro(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        service, repo, _ = self._service_com_repo()
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.adicionar_bloco(
                SimpleNamespace(id="a"),
                dia="xyz",
                hora_inicio="08:00",
                hora_final="10:00",
                titulo="X",
            )
        repo.update.assert_not_called()

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_com_titulo_vazio_levanta_erro(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        service, repo, _ = self._service_com_repo()
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.adicionar_bloco(
                SimpleNamespace(id="a"),
                dia="seg",
                hora_inicio="08:00",
                hora_final="10:00",
                titulo="   ",
            )
        repo.update.assert_not_called()

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_com_hora_invertida_levanta_erro(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        service, repo, _ = self._service_com_repo()
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.adicionar_bloco(
                SimpleNamespace(id="a"),
                dia="seg",
                hora_inicio="10:00",
                hora_final="09:00",
                titulo="X",
            )
        repo.update.assert_not_called()

    @patch("app.services.roteiro_service.Turma")
    def test_adicionar_bloco_conflitante_com_carga_da_grade_bloqueia(self, turma_mock):
        from datetime import time
        carga = SimpleNamespace(
            dia="ter",
            hora_inicio=time(9, 0),
            hora_final=time(11, 0),
        )
        turma = SimpleNamespace(
            disciplina=SimpleNamespace(codigo="CC-101"),
            carga_horarias=SimpleNamespace(all=lambda: [carga]),
        )
        chain = turma_mock.objects.filter.return_value
        chain.select_related.return_value.prefetch_related.return_value = [turma]

        service, repo, _ = self._service_com_repo()
        with self.assertRaises(BlocoConflitaComGradeError) as ctx:
            service.adicionar_bloco(
                SimpleNamespace(id="a"),
                dia="ter",
                hora_inicio="10:00",
                hora_final="12:00",
                titulo="Estudar",
            )
        self.assertIn("CC-101", str(ctx.exception))
        repo.update.assert_not_called()

    @patch("app.services.roteiro_service.Turma")
    def test_editar_bloco_atualiza_slot_pelo_id_preservando_outros(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        slots_iniciais = [
            {"id": "abc", "dia": "seg", "hora_inicio": "08:00", "hora_final": "09:00",
             "titulo": "Antigo", "cor": "blue"},
            {"id": "xyz", "dia": "qua", "hora_inicio": "10:00", "hora_final": "11:00",
             "titulo": "Outro", "cor": "green"},
        ]
        service, repo, _ = self._service_com_repo(slots=slots_iniciais)

        service.editar_bloco(
            SimpleNamespace(id="a"),
            bloco_id="abc",
            dia="seg",
            hora_inicio="08:00",
            hora_final="10:00",
            titulo="Novo titulo",
            cor="amber",
        )
        _, kwargs = repo.update.call_args
        slots = kwargs["slots"]
        self.assertEqual(len(slots), 2)
        editado = next(s for s in slots if s["id"] == "abc")
        self.assertEqual(editado["titulo"], "Novo titulo")
        self.assertEqual(editado["hora_final"], "10:00")
        self.assertEqual(editado["cor"], "amber")
        outro = next(s for s in slots if s["id"] == "xyz")
        self.assertEqual(outro["titulo"], "Outro")

    @patch("app.services.roteiro_service.Turma")
    def test_editar_bloco_id_inexistente_levanta_erro(self, turma_mock):
        self._stub_sem_turmas(turma_mock)
        service, repo, _ = self._service_com_repo(
            slots=[{"id": "abc", "dia": "seg", "hora_inicio": "08:00",
                    "hora_final": "09:00", "titulo": "T", "cor": "blue"}]
        )
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.editar_bloco(
                SimpleNamespace(id="a"),
                bloco_id="INEXISTENTE",
                dia="seg",
                hora_inicio="08:00",
                hora_final="09:00",
                titulo="Novo",
            )
        repo.update.assert_not_called()

    def test_editar_bloco_sem_roteiro_existente_levanta_erro(self):
        repo = Mock()
        repo.get_by_aluno.return_value = None
        service = RoteiroService(roteiro_repository=repo)
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.editar_bloco(
                SimpleNamespace(id="a"),
                bloco_id="qualquer",
                dia="seg",
                hora_inicio="08:00",
                hora_final="09:00",
                titulo="X",
            )

    def test_remover_bloco_filtra_slot_pelo_id(self):
        slots = [
            {"id": "aaa", "dia": "seg", "hora_inicio": "08:00", "hora_final": "09:00",
             "titulo": "A", "cor": "blue"},
            {"id": "bbb", "dia": "ter", "hora_inicio": "10:00", "hora_final": "11:00",
             "titulo": "B", "cor": "green"},
        ]
        service, repo, _ = self._service_com_repo(slots=slots)

        service.remover_bloco(SimpleNamespace(id="a"), bloco_id="aaa")
        _, kwargs = repo.update.call_args
        restantes = kwargs["slots"]
        self.assertEqual(len(restantes), 1)
        self.assertEqual(restantes[0]["id"], "bbb")

    def test_remover_bloco_id_inexistente_levanta_erro(self):
        service, repo, _ = self._service_com_repo(
            slots=[{"id": "aaa", "dia": "seg", "hora_inicio": "08:00",
                    "hora_final": "09:00", "titulo": "A", "cor": "blue"}]
        )
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.remover_bloco(SimpleNamespace(id="a"), bloco_id="nao-existe")
        repo.update.assert_not_called()

    def test_remover_bloco_sem_roteiro_existente_levanta_erro(self):
        repo = Mock()
        repo.get_by_aluno.return_value = None
        service = RoteiroService(roteiro_repository=repo)
        with self.assertRaises(BlocoRoteiroInvalidoError):
            service.remover_bloco(SimpleNamespace(id="a"), bloco_id="qualquer")
