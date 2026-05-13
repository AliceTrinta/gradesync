from django.core.exceptions import ValidationError
from django.db import transaction

from app.repositories import AlunoRepository, UsuarioRepository


class AlunoService:
    def __init__(self, aluno_repository=None, usuario_repository=None):
        self.aluno_repository = aluno_repository or AlunoRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    @transaction.atomic
    def criar_aluno(
        self,
        *,
        matricula,
        usuario=None,
        username=None,
        password=None,
        email="",
        first_name="",
        last_name="",
    ):
        if usuario is None:
            if not username or not password:
                raise ValidationError(
                    {
                        "usuario": (
                            "Informe um usuario existente ou username e password "
                            "para criar o usuario do aluno."
                        )
                    }
                )
            usuario = self.usuario_repository.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )

        return self.aluno_repository.create(usuario=usuario, matricula=matricula)

    def obter_aluno(self, aluno_id):
        return self.aluno_repository.get(aluno_id)

    def listar_alunos(self):
        return self.aluno_repository.list()

    @transaction.atomic
    def atualizar_aluno(self, aluno_id, *, matricula=None, usuario_campos=None):
        aluno_campos = {}
        if matricula is not None:
            aluno_campos["matricula"] = matricula

        aluno = self.aluno_repository.update(aluno_id, **aluno_campos)

        if usuario_campos:
            self.usuario_repository.update(aluno.usuario, **usuario_campos)
            aluno = self.aluno_repository.get(aluno_id)

        return aluno

    def desativar_aluno(self, aluno_id):
        return self.aluno_repository.deactivate(aluno_id)
