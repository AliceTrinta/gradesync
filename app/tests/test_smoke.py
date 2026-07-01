"""Smoke test — verifica se todas as páginas retornam 200 sem crashar."""
from django.test import TestCase
from django.urls import reverse

from app.services import AlunoService


class SmokeTest(TestCase):
    """Testa que cada URL registrada renderiza sem crashar."""

    def setUp(self):
        AlunoService().criar_aluno(
            matricula='SMK001',
            username='smoke',
            password='senha-teste-forte-42',
            email='smoke@test.com',
            first_name='Smoke',
            last_name='Test',
        )
        self.client.login(username='smoke', password='senha-teste-forte-42')

    def _get(self, name):
        r = self.client.get(reverse(name))
        return r.status_code

    def test_paginas_carregam_sem_crashar(self):
        for name in [
            'app:home',
            'app:sobre',
            'app:duvidas',
            'app:configuracoes',
            'app:acessibilidade',
            'app:notificacoes',
            'app:dispositivos',
            'app:roteiro',
        ]:
            with self.subTest(name=name):
                status = self._get(name)
                self.assertEqual(status, 200, f'{name} retornou {status}')
