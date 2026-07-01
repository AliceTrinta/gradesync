from decimal import Decimal
from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import CargaHoraria, Disciplina, Professor


PROFESSORES = [
    ("Ana Souza", Decimal("8.7")),
    ("Bruno Lima", Decimal("7.9")),
    ("Carla Nogueira", Decimal("9.1")),
    ("Diego Ramos", Decimal("6.8")),
    ("Eduarda Alves", Decimal("8.2")),
    ("Felipe Torres", Decimal("7.4")),
    ("Gabriela Prado", Decimal("9.3")),
    ("Henrique Dias", Decimal("7.0")),
]

CARGAS_HORARIAS = [
    ("segunda", time(8, 0), time(10, 0)),
    ("segunda", time(10, 0), time(12, 0)),
    ("terca", time(8, 0), time(10, 0)),
    ("terca", time(14, 0), time(16, 0)),
    ("quarta", time(10, 0), time(12, 0)),
    ("quarta", time(14, 0), time(16, 0)),
    ("quinta", time(8, 0), time(10, 0)),
    ("quinta", time(16, 0), time(18, 0)),
    ("sexta", time(10, 0), time(12, 0)),
    ("sexta", time(14, 0), time(16, 0)),
]

DISCIPLINAS_ADM = [
    ("ADM-101", "Introducao a Administracao", Decimal("12.5"), []),
    ("ADM-102", "Matematica Financeira", Decimal("22.0"), []),
    ("ADM-103", "Contabilidade Basica", Decimal("18.0"), []),
    ("ADM-104", "Economia I", Decimal("15.5"), []),
    ("ADM-201", "Teoria Geral da Administracao", Decimal("14.0"), ["ADM-101"]),
    ("ADM-202", "Estatistica Aplicada", Decimal("25.0"), ["ADM-102"]),
    ("ADM-203", "Marketing I", Decimal("11.0"), ["ADM-101"]),
    ("ADM-204", "Gestao de Pessoas", Decimal("9.0"), ["ADM-201"]),
    ("ADM-301", "Financas Corporativas", Decimal("21.0"), ["ADM-102", "ADM-103"]),
    ("ADM-302", "Direito Empresarial", Decimal("16.5"), ["ADM-101"]),
    ("ADM-303", "Logistica e Operacoes", Decimal("13.0"), ["ADM-201"]),
    ("ADM-401", "Estrategia Empresarial", Decimal("10.0"), ["ADM-203", "ADM-301"]),
]

DISCIPLINAS_CC = [
    ("CC-101", "Introducao a Computacao", Decimal("10.0"), []),
    ("CC-102", "Algoritmos e Programacao", Decimal("28.0"), []),
    ("CC-103", "Matematica Discreta", Decimal("26.5"), []),
    ("CC-104", "Calculo I", Decimal("32.0"), []),
    ("CC-201", "Estrutura de Dados", Decimal("24.0"), ["CC-102"]),
    ("CC-202", "Programacao Orientada a Objetos", Decimal("18.0"), ["CC-102"]),
    ("CC-203", "Banco de Dados I", Decimal("16.0"), ["CC-102"]),
    ("CC-204", "Arquitetura de Computadores", Decimal("22.0"), ["CC-101"]),
    ("CC-301", "Sistemas Operacionais", Decimal("20.0"), ["CC-201", "CC-204"]),
    ("CC-302", "Engenharia de Software", Decimal("12.5"), ["CC-202"]),
    ("CC-303", "Redes de Computadores", Decimal("18.5"), ["CC-204"]),
    ("CC-304", "Inteligencia Artificial", Decimal("14.0"), ["CC-201", "CC-103"]),
    ("CC-401", "Compiladores", Decimal("30.0"), ["CC-301", "CC-302"]),
]


class Command(BaseCommand):
    help = "Popula dados mockados para os cursos de Administracao e Ciencia da Computacao."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpar",
            action="store_true",
            help="Remove dados existentes antes de recriar.",
        )

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)
        limpar = options.get("limpar", False)

        with transaction.atomic():
            if limpar:
                Disciplina.objects.all().delete()
                CargaHoraria.objects.all().delete()
                Professor.objects.all().delete()

            self._popular_professores(verbosity)
            self._popular_cargas(verbosity)
            self._popular_disciplinas(verbosity)

        if verbosity >= 1:
            self.stdout.write(self.style.SUCCESS("Seed concluido."))

    def _popular_professores(self, verbosity):
        criados = 0
        for nome, avaliacao in PROFESSORES:
            _, created = Professor.objects.get_or_create(
                nome=nome,
                defaults={"avaliacao": avaliacao},
            )
            criados += int(created)
        if verbosity >= 1:
            self.stdout.write(f"Professores: {criados} criados / {len(PROFESSORES)} totais.")

    def _popular_cargas(self, verbosity):
        criados = 0
        for dia, inicio, final in CARGAS_HORARIAS:
            _, created = CargaHoraria.objects.get_or_create(
                dia=dia,
                hora_inicio=inicio,
                hora_final=final,
            )
            criados += int(created)
        if verbosity >= 1:
            self.stdout.write(f"Cargas horarias: {criados} criados / {len(CARGAS_HORARIAS)} totais.")

    def _popular_disciplinas(self, verbosity):
        todas = DISCIPLINAS_ADM + DISCIPLINAS_CC
        criados = 0
        for codigo, nome, taxa, _ in todas:
            _, created = Disciplina.objects.get_or_create(
                codigo=codigo,
                defaults={"nome": nome, "taxa_de_reprovacao": taxa},
            )
            criados += int(created)

        for codigo, _, _, pre_reqs in todas:
            if not pre_reqs:
                continue
            disciplina = Disciplina.objects.get(codigo=codigo)
            for cod_pre in pre_reqs:
                try:
                    pre = Disciplina.objects.get(codigo=cod_pre)
                except Disciplina.DoesNotExist:
                    continue
                disciplina.pre_requisitos.add(pre)

        if verbosity >= 1:
            self.stdout.write(f"Disciplinas: {criados} criados / {len(todas)} totais.")
