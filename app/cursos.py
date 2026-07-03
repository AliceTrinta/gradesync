from datetime import date

CURSO_ADM = "ADM"
CURSO_CC = "CC"

CURSOS = [
    (CURSO_ADM, "Administração"),
    (CURSO_CC, "Ciência da Computação"),
]

CURSOS_DICT = dict(CURSOS)


def periodo_atual_permitido(hoje=None):
    hoje = hoje or date.today()
    if hoje.month == 12:
        return f"{hoje.year + 1}.1"
    if hoje.month >= 5:
        return f"{hoje.year}.2"
    return f"{hoje.year}.1"
