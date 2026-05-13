from django.contrib.auth import get_user_model
from django.db import transaction

from app.exceptions import EntidadeNaoEncontrada
from app.models import Aluno, Grade, Simulacao


class UsuarioRepository:
    def create_user(
        self,
        *,
        username,
        password,
        email="",
        first_name="",
        last_name="",
    ):
        return get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    def update(self, usuario, **campos):
        for campo, valor in campos.items():
            if campo == "password":
                usuario.set_password(valor)
                continue
            setattr(usuario, campo, valor)
        usuario.full_clean()
        usuario.save()
        return usuario


class AlunoRepository:
    def create(self, *, usuario, matricula):
        aluno = Aluno(usuario=usuario, matricula=matricula)
        aluno.full_clean()
        aluno.save()
        return aluno

    def get(self, aluno_id):
        try:
            return Aluno.objects.select_related("usuario").get(id=aluno_id)
        except Aluno.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Aluno nao encontrado.") from exc

    def list(self):
        return (
            Aluno.objects.select_related("usuario")
            .filter(ativo=True)
            .order_by("matricula")
        )

    def update(self, aluno_id, **campos):
        aluno = self.get(aluno_id)
        for campo, valor in campos.items():
            setattr(aluno, campo, valor)
        aluno.full_clean()
        aluno.save()
        return aluno

    @transaction.atomic
    def deactivate(self, aluno_id):
        aluno = self.get(aluno_id)
        Grade.objects.filter(aluno=aluno).delete()
        Simulacao.objects.filter(aluno=aluno).delete()
        aluno.ativo = False
        aluno.full_clean()
        aluno.save(update_fields=["ativo"])

        usuario = aluno.usuario
        usuario.is_active = False
        usuario.full_clean()
        usuario.save(update_fields=["is_active"])

        return aluno
