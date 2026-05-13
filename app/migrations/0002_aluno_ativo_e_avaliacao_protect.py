import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aluno",
            name="ativo",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="avaliacao",
            name="aluno",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="avaliacoes",
                to="app.aluno",
            ),
        ),
    ]
