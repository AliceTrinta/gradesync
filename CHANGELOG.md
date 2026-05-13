# Changelog

Todas as mudancas relevantes deste projeto serao documentadas neste arquivo.

## [Unreleased]

### Added

- Espaco reservado para as proximas funcionalidades, ajustes e correcoes.

## [0.2.0] - 2026-05-06

### Added

- CRUDs de servico e repositorio para `Avaliacao`, `CargaHoraria`, `Disciplina`, `Professor` e `Turma`.
- Cobertura de testes para os novos CRUDs, regras de dominio de simulacao e desativacao de aluno.
- Campo `ativo` em `Aluno` para suportar desativacao logica e preservacao de historico.
- Nova migration `app.0002_aluno_ativo_e_avaliacao_protect`.
- `Makefile` com atalhos para `lint`, `tests`, `coverage`, `run-api` e `down-api`.
- Dependencias de qualidade e cobertura adicionadas ao projeto: `ruff` e `coverage`.

### Changed

- Reorganizacao da arquitetura do app para o padrao Django, removendo a antiga estrutura `domain/`.
- Separacao definitiva entre `models/`, `services/`, `repositories/` e `exceptions.py`.
- Regras de dominio de `Simulacao` ajustadas: ao confirmar, a `Grade` e criada e o rascunho e removido.
- Regras de dominio de `Avaliacao` ajustadas: nao existe mais rascunho; `professor` e `disciplina` sao obrigatorios.
- `Avaliacao.aluno` passou a usar `PROTECT` para preservar o historico quando o aluno for desativado.
- Exclusao de `Aluno` substituida por desativacao logica via `desativar_aluno()` e `deactivate()`.
- `AlunoRepository.list()` passou a listar apenas alunos ativos.
- Atualizacao de senha de usuario passou a usar `set_password()` corretamente.
- Operacoes criticas de `Aluno` e confirmacao de `Simulacao` ficaram protegidas por transacoes.
- Campos textuais principais passaram a ser normalizados com `strip()` nas validacoes dos modelos.
- Django Admin melhorado com `ModelAdmin`, filtros, busca e bloqueio de delete para `Aluno`, `Professor` e `Disciplina`.
- Suite de testes reorganizada em pacote `app/tests/` com separacao por responsabilidade (`test_models`, `test_services`, `test_flows`).
- `readme.md` ampliado com estrutura do projeto e secao de uso do `Makefile`.

### Removed

- Estrutura legada `app/domain/`.
- Arquivo legado `app/tests.py`.
- Campo `avaliacao_completa` de `Avaliacao`.

### Security

- Preservacao de integridade historica de `Avaliacao` com protecao contra remocao fisica de entidades relacionadas essenciais.
- Desativacao do usuario Django vinculado ao aluno quando o aluno e desativado.

### Validations

- Validacao explicita para impedir `CargaHoraria` com `dia` vazio.
- Validacao mantida e reforcada para coerencia de periodo, codigo, nome e intervalos de horario.
- Validacao de `Avaliacao` cobrindo obrigatoriedade de `aluno`, `professor` e `disciplina`.

### Verified

- `python manage.py test` executado com sucesso apos a reorganizacao estrutural.
- `python manage.py test` executado com sucesso apos o ajuste das regras de dominio.
- `python manage.py test` executado com sucesso apos a reorganizacao dos testes.
- `python manage.py test` executado com sucesso apos a expansao dos CRUDs e da desativacao de aluno.
- `docker compose up -d --build` executado com sucesso.
- `docker compose run --rm --no-deps -e GRADESYNC_SQLITE=True web sh -lc "ruff check ."` executado com sucesso.
- `docker compose run --rm --no-deps -e GRADESYNC_SQLITE=True web sh -lc "python manage.py test"` executado com sucesso.
- `docker compose run --rm --no-deps -e GRADESYNC_SQLITE=True web sh -lc "coverage run --source=app,gradesync manage.py test && coverage report -m"` executado com sucesso.
- `docker compose down` executado com sucesso.

## [0.1.0] - 2026-05-04

### Added

- Criacao da base inicial do projeto GradeSync com Django.
- Configuracao minima do projeto Django em `gradesync/`.
- Configuracao da aplicacao `app` com `AppConfig`, `models`, `admin`, `tests` e migrations.
- Configuracao de PostgreSQL como banco principal via variaveis de ambiente.
- Configuracao de Docker e Docker Compose para subir:
  - aplicacao Django no servico `web`;
  - banco PostgreSQL no servico `db`.
- Criacao da migration inicial `app.0001_initial`.
- Registro das entidades no Django Admin.
- Criacao de testes automatizados para validacoes essenciais.
- Documentacao no `readme.md` com requisitos, comandos para subir a aplicacao, rodar migrations, checks e testes.

### Changed


### Security

- Remocao do armazenamento direto de senha em `Aluno`.
- Uso do sistema de autenticacao do Django para gerenciamento de senha com hash.

### Validations


### Verified

- `docker compose config` executado com sucesso.
- `docker compose up -d --build` executado com sucesso.
- `python manage.py check` executado com sucesso dentro do container.
- `python manage.py makemigrations --check --dry-run` executado com sucesso dentro do container.
- `python manage.py migrate` executado com sucesso dentro do container.
- `python manage.py test -v 2` executado com sucesso dentro do container.
