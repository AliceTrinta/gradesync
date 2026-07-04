"""
Teste de integracao REAL com o provedor de IA (Gemini).

So roda quando AI_API_KEY esta definida no ambiente. Em CI/pull request
sem chave, o teste e pulado (nao falha). Ideal para rodar localmente
apos configurar o .env com make ai-ping garantindo conectividade.

Como rodar:
    export AI_API_KEY="sua-chave-real"
    python manage.py test app.tests.test_ai_integration -v 2

Como pular explicitamente:
    unset AI_API_KEY
    python manage.py test app -v 2

Ou apenas:
    python manage.py test app
"""
import os
from unittest import skipUnless

from django.core.cache import cache
from django.test import TestCase


_HAS_KEY = bool(os.getenv("AI_API_KEY"))


@skipUnless(_HAS_KEY, "requer variavel de ambiente AI_API_KEY configurada")
class AIIntegrationTests(TestCase):
    """Testes que efetivamente batem no endpoint do Gemini."""

    def setUp(self):
        cache.clear()

    def test_chamar_gemini_direto_devolve_texto_nao_vazio(self):
        from app.services import AIService

        service = AIService()
        texto = service._chamar_gemini(
            "Responda apenas com a palavra ok em minusculas, sem pontuacao.",
            esperar_json=False,
            tag="integration_test",
        )
        self.assertIsInstance(texto, str)
        self.assertTrue(len(texto) > 0)

    def test_responder_duvida_devolve_string_com_conteudo(self):
        from types import SimpleNamespace
        from app.services import AIService

        service = AIService()
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="TesteInt"))
        resposta = service.responder_duvida(
            aluno=aluno,
            pergunta="Explique em uma frase o que e o GradeSync.",
            use_cache=False,
        )
        self.assertIsInstance(resposta, str)
        self.assertGreater(len(resposta), 10)

    def test_sugerir_roteiro_devolve_json_com_slots(self):
        from types import SimpleNamespace
        from app.services import AIService

        service = AIService()
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="TesteInt"))
        grade = SimpleNamespace(periodo="2026.1")
        blocos_livres = [
            ("seg", "14:00", "16:00"),
            ("qua", "10:00", "12:00"),
            ("qui", "16:00", "18:00"),
            ("sex", "08:00", "10:00"),
        ]
        disciplinas_meta = [
            {"codigo": "CC-201", "nome": "Estruturas de Dados",
             "carga_horaria": 60,
             "horarios_de_aula": [("ter", "08:00", "10:00")],
             "pre_requisitos": []},
            {"codigo": "MAT-201", "nome": "Calculo I",
             "carga_horaria": 90,
             "horarios_de_aula": [("qua", "14:00", "16:00")],
             "pre_requisitos": []},
        ]
        resultado = service.sugerir_roteiro(
            aluno=aluno, grade=grade,
            blocos_livres=blocos_livres,
            disciplinas_meta=disciplinas_meta,
            use_cache=False,
        )
        self.assertIn("slots", resultado)
        self.assertIsInstance(resultado["slots"], list)
        self.assertGreater(len(resultado["slots"]), 0)
