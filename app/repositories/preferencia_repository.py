from app.models import PreferenciaAcessibilidade, PreferenciaConta


class PreferenciaAcessibilidadeRepository:
    def get_or_create_for(self, aluno):
        prefs, _ = PreferenciaAcessibilidade.objects.get_or_create(aluno=aluno)
        return prefs

    def update_for(self, aluno, **campos):
        prefs = self.get_or_create_for(aluno)
        for campo, valor in campos.items():
            setattr(prefs, campo, valor)
        prefs.full_clean()
        prefs.save()
        return prefs


class PreferenciaContaRepository:
    def get_or_create_for(self, aluno):
        prefs, _ = PreferenciaConta.objects.get_or_create(aluno=aluno)
        return prefs

    def update_for(self, aluno, **campos):
        prefs = self.get_or_create_for(aluno)
        for campo, valor in campos.items():
            setattr(prefs, campo, valor)
        prefs.full_clean()
        prefs.save()
        return prefs
