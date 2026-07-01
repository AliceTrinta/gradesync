"""DesempenhoService — cálculo de médias, CR e CRA (média aritmética simples).

Fórmula: media = soma_notas / quantidade_avaliacoes
"""
from decimal import Decimal

from app.models import Avaliacao


class DesempenhoService:
    """Calcula indicadores de desempenho academico do aluno."""

    def calcular_media_disciplina(self, *, aluno, disciplina):
        """Media aritmetica simples das notas do aluno numa disciplina.

        Retorna Decimal com 2 casas ou None se nao houver avaliacoes.
        """
        qs = Avaliacao.objects.filter(aluno=aluno, disciplina=disciplina)
        return self._media_de(qs)

    def calcular_cr_periodo(self, *, aluno, ano, semestre):
        """CR do periodo: media aritmetica das notas em ano/semestre."""
        qs = Avaliacao.objects.filter(aluno=aluno, ano=ano, semestre=semestre)
        return self._media_de(qs)

    def calcular_cra(self, *, aluno):
        """CRA: media aritmetica de todas as avaliacoes do aluno."""
        qs = Avaliacao.objects.filter(aluno=aluno)
        return self._media_de(qs)

    def listar_medias_por_disciplina(self, *, aluno):
        """Lista de dicts {disciplina, media, qtd_avaliacoes} do aluno."""
        avaliacoes = (
            Avaliacao.objects.filter(aluno=aluno)
            .select_related("disciplina")
        )
        agregado = {}
        for a in avaliacoes:
            key = a.disciplina_id
            if key not in agregado:
                agregado[key] = {
                    "disciplina": a.disciplina,
                    "notas": [],
                }
            agregado[key]["notas"].append(a.nota)

        resultado = []
        for _key, info in agregado.items():
            notas = info["notas"]
            media = sum(notas) / Decimal(len(notas))
            resultado.append(
                {
                    "disciplina": info["disciplina"],
                    "media": media.quantize(Decimal("0.01")),
                    "qtd_avaliacoes": len(notas),
                }
            )
        return sorted(resultado, key=lambda r: r["disciplina"].codigo)

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _media_de(self, queryset):
        notas = list(queryset.values_list("nota", flat=True))
        if not notas:
            return None
        total = sum(notas)
        media = total / Decimal(len(notas))
        return media.quantize(Decimal("0.01"))
