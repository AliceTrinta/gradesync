from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from types import SimpleNamespace as SimpleNamespaceMock

from app import __version__
from app.cursos import periodo_atual_permitido
from app.models import (
    Aluno,
    CargaHoraria,
    Disciplina,
    Grade,
    Notificacao,
    PreferenciaAcessibilidade,
    PreferenciaConta,
    Professor,
    Roteiro,
)
from app.services import AlunoService, GradeService, NotificacaoService


User = get_user_model()


class WebAuthTests(TestCase):
    """Cobertura de login, logout e cadastro."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026001",
            username="aluno_auth",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
            last_name="Auth",
        )

    def test_login_com_credenciais_validas_redireciona_home(self):
        response = self.client.post(
            reverse("app:login"),
            {"username": "aluno_auth", "password": "senha-forte-123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:home"))

    def test_login_com_senha_errada_mostra_erro(self):
        response = self.client.post(
            reverse("app:login"),
            {"username": "aluno_auth", "password": "errada"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invalidos")

    def test_logout_redireciona_para_login(self):
        self.client.login(username="aluno_auth", password="senha-forte-123")
        response = self.client.get(reverse("app:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:login"))

    def test_cadastro_cria_aluno_e_auto_loga(self):
        response = self.client.post(
            reverse("app:cadastro"),
            {
                "first_name": "Novo",
                "last_name": "Cadastro",
                "email": "novo@example.com",
                "username": "novo_user",
                "matricula": "2026999",
                "password": "outra-senha-123",
                "password_confirm": "outra-senha-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:home"))
        self.assertTrue(User.objects.filter(username="novo_user").exists())
        self.assertTrue(Aluno.objects.filter(matricula="2026999").exists())

    def test_cadastro_com_senhas_diferentes_falha(self):
        response = self.client.post(
            reverse("app:cadastro"),
            {
                "first_name": "Novo",
                "email": "novo@example.com",
                "username": "outro_user",
                "matricula": "2026998",
                "password": "senha1234",
                "password_confirm": "outra1234",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="outro_user").exists())


class WebViewsTests(TestCase):
    """Views basicas (home, api-status, paginas publicas)."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026001",
            username="aluno_teste",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
            last_name="Teste",
        )

    def _login(self):
        self.client.login(username="aluno_teste", password="senha-forte-123")

    def test_home_publica_mostra_landing_para_anonimos(self):
        """Home publica: visitante ve landing com CTAs de entrar/cadastrar."""
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entrar")
        self.assertContains(response, "Criar conta")
        self.assertContains(response, "Seu assistente acadêmico")

    def test_home_renderiza_template_com_sucesso(self):
        """Home autenticada: dashboard com nome do usuario e endpoint da API."""
        self._login()
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GradeSync")
        self.assertContains(response, "GET /api/status/")
        self.assertContains(response, "Roteiro de Estudo")

    def test_api_status_retorna_json_de_status(self):
        response = self.client.get(reverse("app:api-status"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "app": "GradeSync",
                "version": __version__,
                "endpoints": {
                    "home": "/",
                    "admin": "/admin/",
                },
            },
        )

    def test_sobre_e_duvidas_sao_publicas(self):
        for nome in ["app:sobre", "app:duvidas"]:
            with self.subTest(nome=nome):
                response = self.client.get(reverse(nome))
                self.assertEqual(response.status_code, 200)

    def test_paginas_protegidas_exigem_login(self):
        rotas = [
            "app:grade-list",
            "app:grade-criar",
            "app:roteiro",
            "app:notificacoes",
            "app:acessibilidade",
            "app:configuracoes",
            "app:dispositivos",
        ]
        for nome in rotas:
            with self.subTest(nome=nome):
                response = self.client.get(reverse(nome))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("app:login"), response.url)


class RoteiroUITests(TestCase):
    """UI de Roteiro conectada ao model + regra 'exige grade'."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026002",
            username="aluno_roteiro",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_roteiro", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026002")

    def _criar_grade_com_uma_disciplina(self, periodo="2026.1"):
        """Helper: gera uma grade minima para o aluno de teste."""
        from datetime import time
        disciplina = Disciplina.objects.create(
            codigo="CC-101",
            nome="Introducao a Programacao",
            taxa_de_reprovacao=10,
        )
        carga = CargaHoraria.objects.create(
            dia="ter", hora_inicio=time(9, 0), hora_final=time(11, 0)
        )
        return GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo=periodo,
            selecoes=[
                {
                    "disciplina_id": str(disciplina.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )

    def test_roteiro_sem_grade_mostra_cta_para_criar_grade(self):
        response = self.client.get(reverse("app:roteiro"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "monte sua grade")
        self.assertContains(response, reverse("app:grade-criar"))

    def test_roteiro_com_grade_sem_roteiro_mostra_cta_gerar(self):
        self._criar_grade_com_uma_disciplina()
        response = self.client.get(reverse("app:roteiro"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vamos gerar seu roteiro")
        self.assertContains(response, "Criar roteiro")

    def test_criar_roteiro_sem_grade_redireciona_para_grades(self):
        response = self.client.post(reverse("app:roteiro-criar"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:grade-list"))
        self.assertFalse(Roteiro.objects.filter(aluno=self.aluno).exists())

    def test_criar_roteiro_com_grade_gera_slots_e_redireciona(self):
        self._criar_grade_com_uma_disciplina()
        response = self.client.post(reverse("app:roteiro-criar"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:roteiro"))

        self.assertTrue(Roteiro.objects.filter(aluno=self.aluno).exists())

        response = self.client.get(reverse("app:roteiro"))
        self.assertContains(response, "Estudar CC-101")

    def test_excluir_roteiro_remove_do_banco(self):
        self._criar_grade_com_uma_disciplina()
        self.client.post(reverse("app:roteiro-criar"))
        self.assertTrue(Roteiro.objects.filter(aluno=self.aluno).exists())

        response = self.client.post(reverse("app:roteiro-excluir"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Roteiro.objects.filter(aluno=self.aluno).exists())

    def test_roteiro_criar_exige_post(self):
        response = self.client.get(reverse("app:roteiro-criar"))
        self.assertEqual(response.status_code, 405)


class NotificacoesUITests(TestCase):
    """UI de Notificacoes conectada."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026003",
            username="aluno_notif",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_notif", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026003")
        self.service = NotificacaoService()

    def test_lista_vazia_mostra_empty_state(self):
        response = self.client.get(reverse("app:notificacoes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sem notifica\u00e7\u00f5es")

    def test_lista_renderiza_notificacoes_do_aluno(self):
        notif = self.service.sucesso(self.aluno, "Boas-vindas", "Bem-vindo ao GradeSync!")

        response = self.client.get(reverse("app:notificacoes"))
        self.assertContains(response, "Boas-vindas")
        self.assertContains(response, "Bem-vindo ao GradeSync!")
        self.assertContains(response, "Marcar como lida")
        self.assertFalse(notif.lida)

    def test_marcar_uma_como_lida(self):
        notif = self.service.aviso(self.aluno, "Aviso", "Verifique sua grade")

        response = self.client.post(
            reverse("app:notificacoes-marcar-lida", kwargs={"notif_id": notif.id})
        )
        self.assertEqual(response.status_code, 302)
        notif.refresh_from_db()
        self.assertTrue(notif.lida)

    def test_marcar_todas_como_lidas(self):
        self.service.info(self.aluno, "A", "Msg A")
        self.service.info(self.aluno, "B", "Msg B")
        self.service.info(self.aluno, "C", "Msg C")

        response = self.client.post(reverse("app:notificacoes-marcar-todas"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Notificacao.objects.filter(aluno=self.aluno, lida=False).count(), 0
        )

    def test_marcar_lida_exige_post(self):
        notif = self.service.info(self.aluno, "Teste", "Teste")
        response = self.client.get(
            reverse("app:notificacoes-marcar-lida", kwargs={"notif_id": notif.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_badge_de_nao_lidas_no_header(self):
        self.service.info(self.aluno, "A", "Msg A")
        self.service.info(self.aluno, "B", "Msg B")

        response = self.client.get(reverse("app:home"))
        self.assertContains(response, 'class="badge"')
        self.assertContains(response, ">2<")


class PreferenciaAcessibilidadeUITests(TestCase):
    """UI de Acessibilidade conectada."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026004",
            username="aluno_ac",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_ac", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026004")

    def test_get_renderiza_form_com_defaults(self):
        response = self.client.get(reverse("app:acessibilidade"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tamanho do texto")
        self.assertContains(response, "Alto contraste")

    def test_signal_criou_prefs_default(self):
        prefs = PreferenciaAcessibilidade.objects.get(aluno=self.aluno)
        self.assertEqual(prefs.tamanho_fonte, PreferenciaAcessibilidade.FONTE_MEDIO)
        self.assertFalse(prefs.alto_contraste)

    def test_post_salva_preferencias(self):
        response = self.client.post(
            reverse("app:acessibilidade"),
            {
                "tamanho_fonte": "grande",
                "alto_contraste": "on",
                "reduzir_animacoes": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        prefs = PreferenciaAcessibilidade.objects.get(aluno=self.aluno)
        self.assertEqual(prefs.tamanho_fonte, "grande")
        self.assertTrue(prefs.alto_contraste)
        self.assertTrue(prefs.reduzir_animacoes)
        self.assertFalse(prefs.sublinhar_links)

    def test_prefs_aplicadas_no_body_do_base(self):
        self.client.post(
            reverse("app:acessibilidade"),
            {"tamanho_fonte": "muito-grande", "alto_contraste": "on"},
        )

        response = self.client.get(reverse("app:home"))
        self.assertContains(response, "fonte-muito-grande")
        self.assertContains(response, "alto-contraste")

    def test_post_valor_invalido_de_fonte_ignorado(self):
        response = self.client.post(
            reverse("app:acessibilidade"),
            {"tamanho_fonte": "gigantesco"},
        )
        self.assertEqual(response.status_code, 302)
        prefs = PreferenciaAcessibilidade.objects.get(aluno=self.aluno)
        self.assertEqual(prefs.tamanho_fonte, PreferenciaAcessibilidade.FONTE_MEDIO)


class PreferenciaContaUITests(TestCase):
    """UI de Configuracoes conectada."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026005",
            username="aluno_conf",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_conf", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026005")

    def test_get_renderiza_form_com_defaults(self):
        response = self.client.get(reverse("app:configuracoes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Idioma")
        self.assertContains(response, "Tema")

    def test_post_salva_tema_e_idioma(self):
        response = self.client.post(
            reverse("app:configuracoes"),
            {"idioma": "en-US", "tema": "escuro"},
        )
        self.assertEqual(response.status_code, 302)

        prefs = PreferenciaConta.objects.get(aluno=self.aluno)
        self.assertEqual(prefs.idioma, "en-US")
        self.assertEqual(prefs.tema, "escuro")

    def test_tema_aplicado_no_data_theme_do_html(self):
        self.client.post(
            reverse("app:configuracoes"),
            {"idioma": "pt-BR", "tema": "escuro"},
        )
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, 'data-theme="escuro"')

    def test_post_valores_invalidos_sao_ignorados(self):
        response = self.client.post(
            reverse("app:configuracoes"),
            {"idioma": "klingon", "tema": "neon"},
        )
        self.assertEqual(response.status_code, 302)

        prefs = PreferenciaConta.objects.get(aluno=self.aluno)
        self.assertEqual(prefs.idioma, PreferenciaConta.IDIOMA_PT_BR)
        self.assertEqual(prefs.tema, PreferenciaConta.TEMA_CLARO)


class RotasLegadasTests(TestCase):
    """Rotas de CRUD legadas devem retornar 404."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026006",
            username="aluno_legado",
            password="senha-forte-123",
            email="aluno@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_legado", password="senha-forte-123")

    def test_rotas_desativadas_retornam_404(self):
        rotas_off = [
            "/simulacoes/",
            "/avaliacoes/",
            "/disciplinas/",
            "/professores/",
            "/perfil/",
            "/perfil/desativar/",
        ]
        for url in rotas_off:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)


class GradeUITests(TestCase):
    """UI de Grade (list, wizard, detalhe, excluir)."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026010",
            username="aluno_grade",
            password="senha-forte-123",
            email="aluno_grade@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_grade", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026010")

        call_command("seed_dados", verbosity=0)

    def test_grade_list_vazia_mostra_cta(self):
        response = self.client.get(reverse("app:grade-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Criar minha primeira grade")

    def test_grade_form_passo1_lista_cursos(self):
        response = self.client.get(reverse("app:grade-criar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administra\u00e7\u00e3o")
        self.assertContains(response, "Ci\u00eancia da Computa\u00e7\u00e3o")

    def test_grade_form_passo2_lista_disciplinas_do_curso(self):
        response = self.client.get(reverse("app:grade-criar") + "?curso=CC")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CC-101")
        self.assertNotContains(response, "ADM-101")

    def test_criar_grade_com_selecoes_valida_e_redireciona(self):
        disc = Disciplina.objects.filter(codigo__istartswith="CC-").first()
        carga = CargaHoraria.objects.first()
        periodo = periodo_atual_permitido()

        response = self.client.post(
            reverse("app:grade-criar"),
            {
                "curso": "CC",
                f"disciplina_{disc.id}": "on",
                f"cargas_{disc.id}": [str(carga.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Grade.objects.filter(aluno=self.aluno, periodo=periodo).exists())

        grade = Grade.objects.get(aluno=self.aluno, periodo=periodo)
        self.assertEqual(grade.turmas.count(), 1)
        self.assertEqual(grade.turmas.first().disciplina_id, disc.id)

    def test_criar_grade_com_conflito_de_horario_mostra_erro(self):
        disc_a, disc_b = list(
            Disciplina.objects.filter(codigo__istartswith="CC-").order_by("codigo")[:2]
        )
        carga = CargaHoraria.objects.first()

        response = self.client.post(
            reverse("app:grade-criar"),
            {
                "curso": "CC",
                f"disciplina_{disc_a.id}": "on",
                f"cargas_{disc_a.id}": [str(carga.id)],
                f"disciplina_{disc_b.id}": "on",
                f"cargas_{disc_b.id}": [str(carga.id)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Grade.objects.filter(aluno=self.aluno).exists())
        self.assertContains(response, "Conflito de hor")

    def test_criar_grade_exige_ao_menos_uma_disciplina(self):
        response = self.client.post(
            reverse("app:grade-criar"),
            {"curso": "CC"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Grade.objects.filter(aluno=self.aluno).exists())
        self.assertContains(response, "ao menos uma disciplina")

    def test_grade_detalhe_mostra_disciplinas(self):
        disc = Disciplina.objects.filter(codigo__istartswith="CC-").first()
        carga = CargaHoraria.objects.first()
        grade = GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo="2026.1",
            selecoes=[
                {
                    "disciplina_id": str(disc.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )

        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, disc.codigo)
        self.assertContains(response, "Gerar roteiro")

    def test_grade_de_outro_aluno_retorna_para_lista(self):
        outro = AlunoService().criar_aluno(
            matricula="2026011",
            username="outro_aluno",
            password="senha-forte-123",
            email="outro@example.com",
            first_name="Outro",
        )
        disc = Disciplina.objects.filter(codigo__istartswith="CC-").first()
        carga = CargaHoraria.objects.first()
        grade_do_outro = GradeService().criar_grade_do_aluno(
            aluno=outro,
            periodo="2026.1",
            selecoes=[
                {
                    "disciplina_id": str(disc.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )

        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade_do_outro.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:grade-list"))

    def test_excluir_grade_via_post(self):
        disc = Disciplina.objects.filter(codigo__istartswith="CC-").first()
        carga = CargaHoraria.objects.first()
        grade = GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo="2026.1",
            selecoes=[
                {
                    "disciplina_id": str(disc.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )

        response = self.client.post(
            reverse("app:grade-excluir", kwargs={"grade_id": grade.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:grade-list"))
        self.assertFalse(Grade.objects.filter(id=grade.id).exists())

    def test_grade_no_navbar(self):
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, reverse("app:grade-list"))
        self.assertContains(response, ">Grade<")


class SeedDadosCommandTests(TestCase):
    """Comando seed_dados popula catalogo dos 2 cursos."""

    def test_seed_cria_professores_cargas_e_disciplinas(self):
        self.assertEqual(Professor.objects.count(), 0)
        self.assertEqual(CargaHoraria.objects.count(), 0)
        self.assertEqual(Disciplina.objects.count(), 0)

        call_command("seed_dados", verbosity=0)

        self.assertGreater(Professor.objects.count(), 0)
        self.assertGreater(CargaHoraria.objects.count(), 0)
        self.assertGreater(
            Disciplina.objects.filter(codigo__istartswith="ADM-").count(), 0
        )
        self.assertGreater(
            Disciplina.objects.filter(codigo__istartswith="CC-").count(), 0
        )

    def test_seed_e_idempotente(self):
        call_command("seed_dados", verbosity=0)
        professores_1 = Professor.objects.count()
        cargas_1 = CargaHoraria.objects.count()
        disciplinas_1 = Disciplina.objects.count()

        call_command("seed_dados", verbosity=0)

        self.assertEqual(Professor.objects.count(), professores_1)
        self.assertEqual(CargaHoraria.objects.count(), cargas_1)
        self.assertEqual(Disciplina.objects.count(), disciplinas_1)


class PeriodoAtualPermitidoTests(TestCase):
    """Regra do periodo automatico derivado da data corrente."""

    def test_janeiro_a_abril_retorna_ano_ponto_1(self):
        from datetime import date

        for mes in (1, 2, 3, 4):
            with self.subTest(mes=mes):
                self.assertEqual(
                    periodo_atual_permitido(date(2026, mes, 15)),
                    "2026.1",
                )

    def test_maio_a_novembro_retorna_ano_ponto_2(self):
        from datetime import date

        for mes in (5, 6, 7, 8, 9, 10, 11):
            with self.subTest(mes=mes):
                self.assertEqual(
                    periodo_atual_permitido(date(2026, mes, 15)),
                    "2026.2",
                )

    def test_dezembro_libera_semestre_1_do_ano_seguinte(self):
        from datetime import date

        self.assertEqual(
            periodo_atual_permitido(date(2026, 12, 5)),
            "2027.1",
        )


class GradeDuplicataTests(TestCase):
    """Impede criacao de duas grades para o mesmo periodo."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026099",
            username="aluno_dup",
            password="senha-forte-123",
            email="dup@example.com",
            first_name="Dup",
        )
        self.client.login(username="aluno_dup", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026099")
        call_command("seed_dados", verbosity=0)

    def test_segunda_grade_no_mesmo_periodo_e_rejeitada(self):
        disc = Disciplina.objects.filter(codigo__istartswith="CC-").first()
        carga = CargaHoraria.objects.first()
        periodo = periodo_atual_permitido()

        GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo=periodo,
            selecoes=[
                {
                    "disciplina_id": str(disc.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )

        response = self.client.post(
            reverse("app:grade-criar"),
            {
                "curso": "CC",
                f"disciplina_{disc.id}": "on",
                f"cargas_{disc.id}": [str(carga.id)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Grade.objects.filter(aluno=self.aluno).count(), 1)
        self.assertContains(response, "ja tem uma grade")


class GradeDetalheGridTests(TestCase):
    """Bug fix: cards de 2h agora ocupam 2 slots do grid, nao 1."""

    def setUp(self):
        from datetime import time

        AlunoService().criar_aluno(
            matricula="2026200",
            username="aluno_grid",
            password="senha-forte-123",
            email="grid@example.com",
            first_name="Grid",
        )
        self.client.login(username="aluno_grid", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026200")

        self.disc_seg = Disciplina.objects.create(
            codigo="CC-201",
            nome="Algoritmos II",
            taxa_de_reprovacao=10,
        )
        self.disc_quinta = Disciplina.objects.create(
            codigo="CC-202",
            nome="Estruturas de Dados",
            taxa_de_reprovacao=10,
        )
        self.carga_seg_8_10 = CargaHoraria.objects.create(
            dia="segunda", hora_inicio=time(8, 0), hora_final=time(10, 0)
        )
        self.carga_qui_16_18 = CargaHoraria.objects.create(
            dia="quinta", hora_inicio=time(16, 0), hora_final=time(18, 0)
        )

    def _criar_grade(self, selecoes):
        return GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo=periodo_atual_permitido(),
            selecoes=selecoes,
        )

    def _contar_slots(self, html):
        return html.count('class="slot-pill ')

    def _contar_continuas(self, html):
        return html.count("slot-pill--continua")

    def _contar_joined(self, html):
        return html.count("slot-pill--joined-bottom")

    def test_bloco_de_2_horas_renderiza_2_slot_pills(self):
        grade = self._criar_grade(
            [
                {
                    "disciplina_id": str(self.disc_seg.id),
                    "carga_horaria_ids": [str(self.carga_seg_8_10.id)],
                }
            ]
        )
        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade.id})
        )
        html = response.content.decode()

        self.assertEqual(self._contar_slots(html), 2)
        self.assertEqual(self._contar_continuas(html), 1)
        self.assertEqual(self._contar_joined(html), 1)

    def test_horario_ate_18h_aparece_no_grid(self):
        grade = self._criar_grade(
            [
                {
                    "disciplina_id": str(self.disc_quinta.id),
                    "carga_horaria_ids": [str(self.carga_qui_16_18.id)],
                }
            ]
        )
        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade.id})
        )
        html = response.content.decode()

        self.assertIn(">16:00<", html)
        self.assertIn(">17:00<", html)
        self.assertEqual(self._contar_slots(html), 2)

    def test_head_mostra_codigo_uma_vez_e_continua_nao_mostra(self):
        grade = self._criar_grade(
            [
                {
                    "disciplina_id": str(self.disc_seg.id),
                    "carga_horaria_ids": [str(self.carga_seg_8_10.id)],
                }
            ]
        )
        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade.id})
        )
        html = response.content.decode()

        self.assertEqual(html.count("<small>08:00\u201310:00</small>"), 1)
        self.assertEqual(self._contar_slots(html), 2)
        self.assertEqual(self._contar_continuas(html), 1)

    def test_grade_completa_dois_dias_gera_4_slots(self):
        grade = self._criar_grade(
            [
                {
                    "disciplina_id": str(self.disc_seg.id),
                    "carga_horaria_ids": [str(self.carga_seg_8_10.id)],
                },
                {
                    "disciplina_id": str(self.disc_quinta.id),
                    "carga_horaria_ids": [str(self.carga_qui_16_18.id)],
                },
            ]
        )
        response = self.client.get(
            reverse("app:grade-detalhe", kwargs={"grade_id": grade.id})
        )
        html = response.content.decode()

        self.assertEqual(self._contar_slots(html), 4)
        self.assertEqual(self._contar_continuas(html), 2)
        self.assertEqual(self._contar_joined(html), 2)
        self.assertEqual(html.count("<small>08:00\u201310:00</small>"), 1)
        self.assertEqual(html.count("<small>16:00\u201318:00</small>"), 1)


class RoteiroEditorUITests(TestCase):
    """Editor de blocos do roteiro (adicionar/editar/remover) via HTTP."""

    def setUp(self):
        from datetime import time

        AlunoService().criar_aluno(
            matricula="2026300",
            username="aluno_editor",
            password="senha-forte-123",
            email="editor@example.com",
            first_name="Aluno",
        )
        self.client.login(username="aluno_editor", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2026300")

        disciplina = Disciplina.objects.create(
            codigo="CC-101",
            nome="Programacao I",
            taxa_de_reprovacao=10,
        )
        carga = CargaHoraria.objects.create(
            dia="ter", hora_inicio=time(9, 0), hora_final=time(11, 0)
        )
        GradeService().criar_grade_do_aluno(
            aluno=self.aluno,
            periodo=periodo_atual_permitido(),
            selecoes=[
                {
                    "disciplina_id": str(disciplina.id),
                    "carga_horaria_ids": [str(carga.id)],
                }
            ],
        )
        self.client.post(reverse("app:roteiro-criar"))
        self.roteiro = Roteiro.objects.get(aluno=self.aluno)
        self.assertGreater(len(self.roteiro.slots), 0)
        self.assertIn("id", self.roteiro.slots[0])

    def _post_adicionar(self, **overrides):
        data = {
            "dia": "sex",
            "hora_inicio": "13:00",
            "hora_final": "14:00",
            "titulo": "Revisar prova",
            "cor": "blue",
        }
        data.update(overrides)
        return self.client.post(reverse("app:roteiro-bloco-adicionar"), data)

    def test_adicionar_bloco_valido_grava_e_redireciona(self):
        antes = len(self.roteiro.slots)
        response = self._post_adicionar(titulo="Estudo livre")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:roteiro"))

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), antes + 1)
        titulos = [s["titulo"] for s in self.roteiro.slots]
        self.assertIn("Estudo livre", titulos)

    def test_adicionar_bloco_conflitante_com_grade_bloqueia(self):
        antes = len(self.roteiro.slots)
        response = self._post_adicionar(
            dia="ter", hora_inicio="10:00", hora_final="11:00", titulo="Conflitou"
        )
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), antes)
        titulos = [s["titulo"] for s in self.roteiro.slots]
        self.assertNotIn("Conflitou", titulos)

    def test_adicionar_bloco_com_dia_invalido_nao_altera_roteiro(self):
        antes = len(self.roteiro.slots)
        response = self._post_adicionar(dia="zzz")
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), antes)

    def test_editar_bloco_altera_titulo_e_horario(self):
        bloco_id = self.roteiro.slots[0]["id"]
        response = self.client.post(
            reverse("app:roteiro-bloco-editar", kwargs={"bloco_id": bloco_id}),
            {
                "dia": "sab",
                "hora_inicio": "15:00",
                "hora_final": "17:00",
                "titulo": "Revisao editada",
                "cor": "purple",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        editado = next(s for s in self.roteiro.slots if s["id"] == bloco_id)
        self.assertEqual(editado["dia"], "sab")
        self.assertEqual(editado["hora_inicio"], "15:00")
        self.assertEqual(editado["hora_final"], "17:00")
        self.assertEqual(editado["titulo"], "Revisao editada")
        self.assertEqual(editado["cor"], "purple")

    def test_editar_bloco_id_inexistente_nao_altera(self):
        antes = list(self.roteiro.slots)
        response = self.client.post(
            reverse("app:roteiro-bloco-editar", kwargs={"bloco_id": "nao-existe"}),
            {
                "dia": "seg",
                "hora_inicio": "08:00",
                "hora_final": "09:00",
                "titulo": "Nada",
                "cor": "blue",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), len(antes))

    def test_remover_bloco_apaga_do_json(self):
        bloco_id = self.roteiro.slots[0]["id"]
        antes = len(self.roteiro.slots)
        response = self.client.post(
            reverse("app:roteiro-bloco-remover", kwargs={"bloco_id": bloco_id})
        )
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), antes - 1)
        self.assertFalse(any(s["id"] == bloco_id for s in self.roteiro.slots))

    def test_remover_bloco_id_inexistente_nao_altera(self):
        antes = len(self.roteiro.slots)
        response = self.client.post(
            reverse("app:roteiro-bloco-remover", kwargs={"bloco_id": "nao-existe"})
        )
        self.assertEqual(response.status_code, 302)

        self.roteiro.refresh_from_db()
        self.assertEqual(len(self.roteiro.slots), antes)

    def test_rotas_de_bloco_exigem_post(self):
        bloco_id = self.roteiro.slots[0]["id"]
        rotas = [
            reverse("app:roteiro-bloco-adicionar"),
            reverse("app:roteiro-bloco-editar", kwargs={"bloco_id": bloco_id}),
            reverse("app:roteiro-bloco-remover", kwargs={"bloco_id": bloco_id}),
        ]
        for url in rotas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 405)

    def test_rotas_de_bloco_exigem_login(self):
        self.client.logout()
        bloco_id = self.roteiro.slots[0]["id"]

        response = self.client.post(
            reverse("app:roteiro-bloco-adicionar"),
            {"dia": "seg", "hora_inicio": "08:00",
             "hora_final": "09:00", "titulo": "X", "cor": "blue"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("app:login"), response.url)

        response = self.client.post(
            reverse("app:roteiro-bloco-remover", kwargs={"bloco_id": bloco_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("app:login"), response.url)

    def test_editor_renderiza_lista_de_blocos_e_botoes(self):
        response = self.client.get(reverse("app:roteiro"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seus blocos de estudo")
        self.assertContains(response, "Adicionar bloco")
        self.assertContains(response, "Editar")
        self.assertContains(response, "Remover")


class CadastroLabelsPtBrTests(TestCase):
    def test_labels_pt_br_aparecem_no_form(self):
        response = self.client.get(reverse("app:cadastro"))
        self.assertEqual(response.status_code, 200)
        for label in ("Nome", "Sobrenome", "E-mail", "Usu\u00e1rio",
                      "Matr\u00edcula", "Senha", "Confirme a senha"):
            with self.subTest(label=label):
                self.assertContains(response, label)
        self.assertNotContains(response, "First name")
        self.assertNotContains(response, "Password confirm")

    def test_login_labels_pt_br(self):
        response = self.client.get(reverse("app:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usu\u00e1rio")
        self.assertContains(response, "Senha")


class SublinharLinksTests(TestCase):
    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026901",
            username="aluno_subl",
            password="senha-forte-123",
            email="a@example.com",
            first_name="A",
        )
        self.client.login(username="aluno_subl", password="senha-forte-123")

    def test_ativar_sublinhar_aplica_classe_no_body(self):
        self.client.post(
            reverse("app:acessibilidade"),
            {"tamanho_fonte": "medio", "sublinhar_links": "on"},
        )
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, "sublinhar-links")

    def test_sem_sublinhar_nao_adiciona_classe(self):
        response = self.client.get(reverse("app:home"))
        self.assertNotContains(response, "sublinhar-links")


class HtmlLangDinamicoTests(TestCase):
    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026902",
            username="aluno_lang",
            password="senha-forte-123",
            email="a@example.com",
            first_name="A",
        )
        self.client.login(username="aluno_lang", password="senha-forte-123")

    def test_idioma_default_pt_br_no_html_lang(self):
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, 'lang="pt-BR"')

    def test_idioma_en_us_aplicado_no_html_lang(self):
        self.client.post(
            reverse("app:configuracoes"),
            {"idioma": "en-US", "tema": "claro"},
        )
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, 'lang="en-US"')


class PrivacidadeUITests(TestCase):
    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026903",
            username="aluno_priv",
            password="senha-forte-123",
            email="a@example.com",
            first_name="A",
        )

    def test_privacidade_exige_login(self):
        response = self.client.get(reverse("app:privacidade"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("app:login"), response.url)

    def test_privacidade_renderiza_para_aluno_logado(self):
        self.client.login(username="aluno_priv", password="senha-forte-123")
        response = self.client.get(reverse("app:privacidade"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacidade")
        self.assertContains(response, "Perfil")
        self.assertContains(response, "Grade e roteiro")

    def test_config_link_privacidade_nao_aponta_mais_para_admin(self):
        self.client.login(username="aluno_priv", password="senha-forte-123")
        response = self.client.get(reverse("app:configuracoes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("app:privacidade"))
        priv_index = response.content.decode().find(">Privacidade<")
        self.assertGreater(priv_index, 0)
        trecho = response.content.decode()[max(0, priv_index - 400):priv_index]
        self.assertNotIn("/admin/", trecho)


class EsqueceuSenhaTests(TestCase):
    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026904",
            username="aluno_reset",
            password="senha-forte-123",
            email="reset@example.com",
            first_name="A",
        )

    def test_login_page_tem_link_esqueceu_senha(self):
        response = self.client.get(reverse("app:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esqueceu a sua senha")
        self.assertContains(response, reverse("password_reset"))

    def test_form_de_reset_renderiza(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-mail")

    def test_post_email_valido_envia_mensagem_e_redireciona(self):
        from django.core import mail

        response = self.client.post(
            reverse("password_reset"),
            {"email": "reset@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("GradeSync", mail.outbox[0].subject)

    def test_pagina_done_renderiza(self):
        response = self.client.get(reverse("password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verifique seu e-mail")

    def test_pagina_complete_renderiza(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "atualizada")


class GradeFormEmptyStateTests(TestCase):
    def setUp(self):
        AlunoService().criar_aluno(
            matricula="2026905",
            username="aluno_empty",
            password="senha-forte-123",
            email="a@example.com",
            first_name="A",
        )
        self.client.login(username="aluno_empty", password="senha-forte-123")

    def test_curso_sem_disciplinas_mostra_painel_e_dica_de_seed(self):
        response = self.client.get(reverse("app:grade-criar") + "?curso=CC")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhuma disciplina cadastrada")
        self.assertContains(response, "seed_dados")
        self.assertNotContains(response, "Criar grade")


class DuvidasPageTests(TestCase):
    def test_pagina_renderiza_com_chips(self):
        response = self.client.get(reverse("app:duvidas"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Como criar uma grade?", html)
        self.assertIn("Como editar meu roteiro?", html)
        self.assertIn("O que s\u00e3o pr\u00e9-requisitos?", html)

    def test_form_aponta_para_endpoint_ajax_com_csrf(self):
        response = self.client.get(reverse("app:duvidas"))
        html = response.content.decode()
        self.assertIn("csrfmiddlewaretoken", html)
        self.assertIn(reverse("app:duvidas-perguntar"), html)

    def test_form_expoe_flag_ia_disponivel(self):
        response = self.client.get(reverse("app:duvidas"))
        html = response.content.decode()
        self.assertIn("data-ia-disponivel", html)


class RoteiroCriarIATests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        AlunoService().criar_aluno(
            matricula="2027001",
            username="aluno_ia_rot",
            password="senha-forte-123",
            email="a@example.com",
            first_name="AlunoIA",
        )
        self.client.login(username="aluno_ia_rot", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2027001")

    def _criar_grade_minima(self, periodo="2026.1"):
        from datetime import time
        disciplina = Disciplina.objects.create(
            codigo="CC-777", nome="Disciplina Teste", taxa_de_reprovacao=5,
        )
        carga = CargaHoraria.objects.create(
            dia="ter", hora_inicio=time(9, 0), hora_final=time(11, 0)
        )
        return GradeService().criar_grade_do_aluno(
            aluno=self.aluno, periodo=periodo,
            selecoes=[{
                "disciplina_id": str(disciplina.id),
                "carga_horaria_ids": [str(carga.id)],
            }],
        )

    def test_get_no_endpoint_devolve_405(self):
        response = self.client.get(reverse("app:roteiro-criar-ia"))
        self.assertEqual(response.status_code, 405)

    def test_sem_grade_redireciona_para_grade_list_com_erro(self):
        response = self.client.post(reverse("app:roteiro-criar-ia"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:grade-list"))
        self.assertFalse(Roteiro.objects.filter(aluno=self.aluno).exists())

    def test_exige_login(self):
        self.client.logout()
        response = self.client.post(reverse("app:roteiro-criar-ia"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("app:login"), response.url)

    def test_ia_com_sucesso_salva_roteiro_com_prompt_marcado_como_ia(self):
        from unittest.mock import patch
        self._criar_grade_minima()

        roteiro_falso = SimpleNamespaceMock(
            slots=[
                {"dia": "seg", "hora_inicio": "14:00", "hora_final": "16:00",
                 "titulo": "X", "cor": "blue"},
                {"dia": "qua", "hora_inicio": "10:00", "hora_final": "12:00",
                 "titulo": "Y", "cor": "green"},
                {"dia": "qui", "hora_inicio": "16:00", "hora_final": "18:00",
                 "titulo": "Z", "cor": "red"},
                {"dia": "sex", "hora_inicio": "08:00", "hora_final": "10:00",
                 "titulo": "W", "cor": "orange"},
            ],
            prompt_usado="[IA] via mock",
        )
        with patch(
            "app.services.RoteiroService.sugerir_roteiro_via_ia",
            return_value=roteiro_falso,
        ):
            response = self.client.post(reverse("app:roteiro-criar-ia"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("app:roteiro"))

    def test_ia_indisponivel_cai_no_gerador_padrao_com_warning(self):
        from unittest.mock import patch
        from app.exceptions import AIProviderError
        self._criar_grade_minima()

        with patch(
            "app.services.RoteiroService.sugerir_roteiro_via_ia",
            side_effect=AIProviderError("boom"),
        ):
            response = self.client.post(
                reverse("app:roteiro-criar-ia"), follow=True,
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Roteiro.objects.filter(aluno=self.aluno).exists())

    def test_ia_devolve_fallback_mostra_mensagem_info(self):
        from unittest.mock import patch
        self._criar_grade_minima()

        roteiro_fallback = SimpleNamespaceMock(
            slots=[{"dia": "seg", "hora_inicio": "08:00",
                    "hora_final": "10:00", "titulo": "X", "cor": "blue"}],
            prompt_usado="[fallback determinístico apos IA devolver 2 slots]",
        )
        with patch(
            "app.services.RoteiroService.sugerir_roteiro_via_ia",
            return_value=roteiro_fallback,
        ):
            response = self.client.post(
                reverse("app:roteiro-criar-ia"), follow=True,
            )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("gerador padr", html)


class DuvidasPerguntarTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        AlunoService().criar_aluno(
            matricula="2027002",
            username="aluno_chat",
            password="senha-forte-123",
            email="c@example.com",
            first_name="Chat",
        )
        self.client.login(username="aluno_chat", password="senha-forte-123")
        self.aluno = Aluno.objects.get(matricula="2027002")

    def test_get_no_endpoint_devolve_405(self):
        response = self.client.get(reverse("app:duvidas-perguntar"))
        self.assertEqual(response.status_code, 405)

    def test_exige_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("app:duvidas-perguntar"),
            {"pergunta": "oi"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("app:login"), response.url)

    def test_pergunta_vazia_devolve_fonte_fallback_e_200(self):
        response = self.client.post(
            reverse("app:duvidas-perguntar"),
            {"pergunta": "  "},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fonte"], "fallback")
        self.assertIn("pergunta", data["resposta"].lower())

    def test_pergunta_muito_longa_devolve_fallback(self):
        response = self.client.post(
            reverse("app:duvidas-perguntar"),
            {"pergunta": "x" * 501},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fonte"], "fallback")
        self.assertIn("500", data["resposta"])

    def test_ia_com_sucesso_devolve_texto_e_fonte_ia(self):
        from unittest.mock import patch
        with patch(
            "app.services.AIService.responder_duvida",
            return_value="Resposta gerada pela IA de mentira",
        ):
            response = self.client.post(
                reverse("app:duvidas-perguntar"),
                {"pergunta": "Como criar uma grade?"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fonte"], "ia")
        self.assertEqual(data["resposta"], "Resposta gerada pela IA de mentira")
        self.assertEqual(data["restantes"], 9)

    def test_ia_indisponivel_devolve_fallback_sem_consumir_cota(self):
        from unittest.mock import patch
        from app.exceptions import AIProviderError
        with patch(
            "app.services.AIService.responder_duvida",
            side_effect=AIProviderError("sem chave"),
        ):
            response = self.client.post(
                reverse("app:duvidas-perguntar"),
                {"pergunta": "qualquer coisa"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fonte"], "fallback")
        self.assertEqual(data["restantes"], 10)

    def test_rate_limit_bloqueia_apos_10_perguntas_bem_sucedidas(self):
        from unittest.mock import patch
        with patch(
            "app.services.AIService.responder_duvida",
            return_value="ok",
        ):
            for i in range(10):
                r = self.client.post(
                    reverse("app:duvidas-perguntar"),
                    {"pergunta": f"pergunta {i}"},
                )
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()["fonte"], "ia")
            r = self.client.post(
                reverse("app:duvidas-perguntar"),
                {"pergunta": "estourou"},
            )
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data["fonte"], "fallback")
            self.assertEqual(data["restantes"], 0)
            self.assertIn("limite", data["resposta"].lower())
