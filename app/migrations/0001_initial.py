import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Aluno",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("matricula", models.CharField(max_length=32, unique=True)),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aluno",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "aluno",
                "verbose_name_plural": "alunos",
            },
        ),
        migrations.CreateModel(
            name="CargaHoraria",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("dia", models.CharField(max_length=16)),
                ("hora_inicio", models.TimeField()),
                ("hora_final", models.TimeField()),
            ],
            options={
                "verbose_name": "carga horaria",
                "verbose_name_plural": "cargas horarias",
            },
        ),
        migrations.CreateModel(
            name="Disciplina",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("codigo", models.CharField(max_length=32, unique=True)),
                ("nome", models.CharField(max_length=255)),
                (
                    "taxa_de_reprovacao",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "pre_requisitos",
                    models.ManyToManyField(
                        blank=True,
                        related_name="dependentes",
                        symmetrical=False,
                        to="app.disciplina",
                    ),
                ),
            ],
            options={
                "verbose_name": "disciplina",
                "verbose_name_plural": "disciplinas",
            },
        ),
        migrations.CreateModel(
            name="Grade",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("periodo", models.CharField(max_length=16)),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="app.aluno",
                    ),
                ),
            ],
            options={
                "verbose_name": "grade",
                "verbose_name_plural": "grades",
            },
        ),
        migrations.CreateModel(
            name="Professor",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=255)),
                (
                    "avaliacao",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
            ],
            options={
                "verbose_name": "professor",
                "verbose_name_plural": "professores",
            },
        ),
        migrations.CreateModel(
            name="Turma",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("codigo", models.CharField(max_length=32)),
                (
                    "disciplina",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="turmas",
                        to="app.disciplina",
                    ),
                ),
                (
                    "grade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="turmas",
                        to="app.grade",
                    ),
                ),
                (
                    "carga_horarias",
                    models.ManyToManyField(
                        blank=True,
                        related_name="turmas",
                        to="app.cargahoraria",
                    ),
                ),
            ],
            options={
                "verbose_name": "turma",
                "verbose_name_plural": "turmas",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("codigo", "grade", "disciplina"),
                        name="unique_turma_por_grade_disciplina",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Avaliacao",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("ano", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(2000)])),
                (
                    "semestre",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(2),
                        ],
                    ),
                ),
                (
                    "nota",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="avaliacoes",
                        to="app.aluno",
                    ),
                ),
                (
                    "disciplina",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="avaliacoes",
                        to="app.disciplina",
                    ),
                ),
                (
                    "professor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="avaliacoes_recebidas",
                        to="app.professor",
                    ),
                ),
            ],
            options={
                "verbose_name": "avaliacao",
                "verbose_name_plural": "avaliacoes",
            },
        ),
        migrations.CreateModel(
            name="Simulacao",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("periodo", models.CharField(max_length=16)),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="simulacoes",
                        to="app.aluno",
                    ),
                ),
                (
                    "turmas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="simulacoes",
                        to="app.turma",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulacao",
                "verbose_name_plural": "simulacoes",
            },
        ),
    ]
