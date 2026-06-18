# CLAUDE.md — Guia completo do projeto GradeSync

## Visão geral

GradeSync é um sistema acadêmico de gerenciamento de grades curriculares, construído com Django 5.x. Permite que alunos gerenciem suas grades de horários, simulem futuras escolhas de disciplinas e acompanhem avaliações acadêmicas.

- **Versão atual:** `0.2.0` (definida em `app/__init__.py`)
- **Framework:** Django 5.x
- **Banco de dados:** SQLite (arquivo `db.sqlite3` em dev, in-memory em testes)
- **Linguagem:** Python 3.12+

---

## Estrutura do projeto

```
gradesync/                          ← Raiz do projeto
├── CHANGELOG.md                    ← Histórico versionado de mudanças
├── claude.md                       ← Este arquivo
├── Makefile                        ← Atalhos de desenvolvimento
├── manage.py                       ← Entrypoint Django
├── readme.md                       ← Docs de setup e uso
├── requirements.txt                ← Dependências Python
├── .gitignore                      ← Padrão Django/Python
│
├── app/                            ← Aplicação Django principal
│   ├── __init__.py                 ← __version__ = "0.2.0"
│   ├── admin.py                    ← Django Admin customizado
│   ├── apps.py                     ← GradeSyncConfig (AppConfig)
│   ├── exceptions.py               ← Exceções de domínio
│   ├── urls.py                     ← Rotas da app
│   ├── views.py                    ← Views (templates + JSON API)
│   │
│   ├── models/                     ← Entidades de domínio (Django ORM)
│   │   ├── __init__.py             ← Re-exporta todos os models
│   │   ├── aluno.py
│   │   ├── avaliacao.py
│   │   ├── cargahoraria.py
│   │   ├── disciplina.py
│   │   ├── grade.py
│   │   ├── professor.py
│   │   ├── simulacao.py
│   │   └── turma.py
│   │
│   ├── repositories/               ← Camada de acesso a dados
│   │   ├── __init__.py             ← Re-exporta todos os repositories
│   │   ├── aluno_repository.py     ← UsuarioRepository + AlunoRepository
│   │   ├── avaliacao_repository.py
│   │   ├── cargahoraria_repository.py
│   │   ├── disciplina_repository.py
│   │   ├── grade_repository.py
│   │   ├── professor_repository.py
│   │   ├── simulacao_repository.py
│   │   └── turma_repository.py
│   │
│   ├── services/                   ← Lógica de negócio / casos de uso
│   │   ├── __init__.py             ← Re-exporta todos os services
│   │   ├── aluno_service.py
│   │   ├── avaliacao_service.py
│   │   ├── cargahoraria_service.py
│   │   ├── disciplina_service.py
│   │   ├── grade_service.py
│   │   ├── professor_service.py
│   │   ├── simulacao_service.py
│   │   └── turma_service.py
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   └── 0002_aluno_ativo_e_avaliacao_protect.py
│   │
│   ├── templates/app/              ← Templates HTML
│   │   ├── base.html               ← Layout master (Inter + FontAwesome + CSS)
│   │   ├── home.html               ← Página base/landing
│   │   ├── cadastro.html
│   │   ├── config.html
│   │   ├── roteiro.html
│   │   ├── dispositivos.html
│   │   ├── notificacoes.html
│   │   └── acessibilidade.html
│   │
│   ├── static/app/
│   │   └── styles.css              ← Stylesheet principal
│   │
│   └── tests/                      ← Suite de testes automatizados
│       ├── __init__.py
│       ├── test_models.py          ← Validação de models
│       ├── test_services.py        ← Testes unitários com mocks
│       ├── test_flows.py           ← Testes de integração (CRUD completo)
│       └── test_web.py             ← Testes de endpoints HTTP
│
└── gradesync/                      ← Pacote de configuração Django
    ├── __init__.py
    ├── settings.py                 ← Configurações (DB switch, i18n, etc.)
    ├── urls.py                     ← Roteamento raiz
    ├── wsgi.py
    └── asgi.py
```

---

## Arquitetura em camadas

| Camada | Local | Responsabilidade |
|--------|-------|------------------|
| **Models** | `app/models/` | Entidades ORM, validação de campos, constraints |
| **Repositories** | `app/repositories/` | Abstração de acesso a dados (CRUD, queries, transações) |
| **Services** | `app/services/` | Regras de negócio, orquestração, coordenação de use-cases |
| **Views** | `app/views.py` | Interface HTTP (renderização de templates + API JSON) |
| **Exceptions** | `app/exceptions.py` | Hierarquia de erros de domínio |

### Padrões adotados

- **Repository Pattern** — Cada entidade possui seu Repository encapsulando queries ORM, `select_related`/`prefetch_related`, e `full_clean()` antes do `save()`.
- **Service Layer** — Cada Service depende de um ou mais Repositories (injetados via construtor). Services orquestram operações multi-step e aplicam regras de negócio.
- **Injeção de dependência via construtor** — Services aceitam parâmetros opcionais de repository, com defaults para implementações reais. Permite mock completo nos testes.
- **Transações atômicas** — Operações críticas usam `@transaction.atomic` (criação/atualização/desativação de aluno, confirmação de simulação, criação de grade).
- **Deleção lógica** — `Aluno` nunca é fisicamente deletado; `deactivate()` seta `ativo=False`, desativa o User Django vinculado, e remove Grades/Simulações.
- **Integridade histórica** — `Avaliacao.aluno` usa `PROTECT` para impedir deleção de alunos com avaliações.
- **UUIDs** como PKs em todos os models.
- **Normalização textual** — Todos os `clean()` fazem strip antes de validar.

---

## Models de domínio

### Aluno
- **PK:** UUID
- **Campos:** `usuario` (OneToOne → User, CASCADE), `matricula` (unique, max 32), `ativo` (bool, default True)
- **Validação:** matricula não pode ser vazia (após strip)
- **`__str__`:** nome + matrícula, ou "(DESATIVADO)" se inativo

### Avaliacao
- **PK:** UUID
- **Campos:** `ano` (PositiveInt, min 2000), `semestre` (1 ou 2), `nota` (Decimal 0–10), `aluno` (FK → Aluno, **PROTECT**), `professor` (FK → Professor, **PROTECT**), `disciplina` (FK → Disciplina, **PROTECT**)
- **Regra:** Todos os 3 FKs são obrigatórios; PROTECT em todos impede deleção das entidades referenciadas
- **Sem conceito de "rascunho"** — avaliações são sempre criadas completas

### CargaHoraria
- **PK:** UUID
- **Campos:** `dia` (CharField max 16), `hora_inicio` (TimeField), `hora_fim` (TimeField)
- **Validação:** dia não pode ser vazio; `hora_fim` deve ser posterior a `hora_inicio`

### Disciplina
- **PK:** UUID
- **Campos:** `codigo` (unique, max 32), `nome` (max 255), `creditos` (Decimal 0–100), `pre_requisitos` (M2M self, assimétrico)
- **Validação:** codigo e nome não podem ser vazios

### Grade
- **PK:** UUID
- **Campos:** `periodo` (max 16), `aluno` (FK → Aluno, CASCADE)
- **Validação:** periodo não pode ser vazio

### Professor
- **PK:** UUID
- **Campos:** `nome` (max 255), `avaliacao` (Decimal 0–10)
- **Validação:** nome não pode ser vazio

### Simulacao
- **PK:** UUID
- **Campos:** `periodo` (max 16), `aluno` (FK → Aluno, CASCADE), `turmas` (M2M → Turma, blank)
- **Validação:** periodo não pode ser vazio

### Turma
- **PK:** UUID
- **Campos:** `codigo` (max 32), `grade` (FK → Grade, CASCADE), `disciplina` (FK → Disciplina, CASCADE), `carga_horarias` (M2M → CargaHoraria, blank)
- **Constraint:** `unique_together` de (grade, disciplina)
- **Validação:** codigo não pode ser vazio

---

## Regras de negócio

### Aluno
- **Criação** — Atômica. Cria um Django User (via UsuarioRepository), depois cria o Aluno. Faz rollback do User se validação da matrícula falhar.
- **Atualização** — Atômica. Atualiza campos do aluno e/ou do user. Rollback completo se qualquer validação falhar.
- **Desativação** (`desativar_aluno`) — Chama `AlunoRepository.deactivate()` que: deleta todas as Grades e Simulações, seta `ativo=False`, e desativa (`is_active=False`) o User vinculado. **Avaliações são preservadas.**

### Simulação
- **Confirmação** (`confirmar_simulacao`) — Atômica. Valida que a simulação está "completa" (tem periodo, aluno, e ≥1 turma). Cria uma nova Grade com as turmas copiadas, depois deleta a simulação (o "rascunho" é consumido).
- Erros de validação são coletados num dict dentro de `SimulacaoIncompletaError`.

### Grade
- Criação e atualização com turmas: objetos Turma são **copiados** (novas instâncias), não movidos.

### Avaliação
- Sem conceito de rascunho.
- `PROTECT` nos FKs garante integridade histórica.

---

## Exceções customizadas

```python
class GradeSyncError(Exception):                # Base de todas as exceções do domínio
class EntidadeNaoEncontrada(GradeSyncError):     # Entidade não encontrada (404-like)
class SimulacaoIncompletaError(GradeSyncError):  # Validação falhou na confirmação
    def __init__(self, erros: dict): ...         # erros = {campo: mensagem}
```

---

## Configuração e infraestrutura

### settings.py
- **Banco:** SQLite — arquivo `db.sqlite3` em desenvolvimento, in-memory para testes (automático quando `test` está em `sys.argv`).
- **Idioma:** `pt-br`, timezone `America/Sao_Paulo`, USE_TZ=True.
- **Static:** `/static/` via `AppDirectoriesFinder`.
- **Sem variáveis de ambiente obrigatórias** — tudo funciona com valores padrão.

### requirements.txt
| Pacote | Versão |
|--------|--------|
| Django | ≥5.0, <6.0 |
| coverage | ≥7.6, <8.0 |
| ruff | ≥0.11, <0.12 |

### Makefile

| Target | O que faz |
|--------|-----------|
| `make setup` | Cria venv, instala deps, aplica migrations |
| `make run` | `python manage.py runserver` |
| `make migrate` | `python manage.py migrate` |
| `make lint` | `ruff check .` |
| `make tests` | `python manage.py test` |
| `make coverage` | Coverage run + report |

---

## Rotas (URLs)

| Path | View | Name |
|------|------|------|
| `/` | `home` | `app:home` |
| `/api/status/` | `api_status` | `app:api-status` |
| `/cadastro/` | `cadastro` | `app:cadastro` |
| `/roteiro/` | `roteiro` | `app:roteiro` |
| `/config/` | `config` | `app:config` |
| `/dispositivos/` | `dispositivos` | `app:dispositivos` |
| `/notificacoes/` | `notificacoes` | `app:notificacoes` |
| `/acessibilidade/` | `acessibilidade` | `app:acessibilidade` |
| `/admin/` | Django Admin | `admin:index` |

O namespace da app é `app`. A view `api_status` retorna JSON com `status`, `app`, `version` e `endpoints`.

---

## Frontend / Templates

- **base.html** — Layout master com Google Fonts (Inter), FontAwesome 6.5.1, CSS customizado. Header com logo (graduation-cap) + link para admin. Block `content` para herança.
- **home.html** — Extends base. Cartão centralizado com eyebrow, título, subtítulo, version pill, code block com fetch dinâmico do status da API, e botões de ação.
- **Demais templates** (cadastro, config, roteiro, etc.) — Protótipos de UI para futuras telas.

### CSS (`app/static/app/styles.css`)
- Variáveis CSS no `:root` (cores, sombra, border).
- Tipografia Inter, font-smoothing.
- Layout: `.page-shell` (min-height 100vh), `.topbar` (72px, flex), `.container` (max 960px).
- Componentes: `.base-preview-card`, `.version-pill`, `.primary`/`.secondary` buttons, `.eyebrow`.
- Responsivo: breakpoint 900px com stacking.

---

## Testes

| Arquivo | Tipo | Técnica |
|---------|------|---------|
| `test_models.py` | Validação de models | Instanciação direta + `full_clean()` + assertions |
| `test_services.py` | Unitários | `unittest.mock.patch` + `MagicMock` nos repositories |
| `test_flows.py` | Integração | DB real (SQLite), services com repositories reais |
| `test_web.py` | Endpoints HTTP | Django test client, status codes + JSON |

### Cenários testados incluem:
- Hash de senha (sem plaintext)
- Rejeição de nota fora do range
- Intervalos inválidos de CargaHoraria
- Normalização de campos (strip)
- Simulação sem turmas rejeitada na confirmação
- Confirmação de simulação cria Grade + remove draft
- CRUD completo para todas as entidades
- Rollback atômico em dados inválidos
- Cascata de desativação do aluno
- Update de senha usa `set_password` (hash)

---

## Django Admin

Todos os 8 models registrados com `ModelAdmin` customizado:
- **Aluno, Professor, Disciplina:** `has_delete_permission = False` (deleção física bloqueada).
- **Aluno:** list display com matrícula/usuário/ativo; searchable.
- **Avaliacao:** filtrável por ano/semestre/disciplina/professor.
- **Grade, Simulacao:** filtrável por período; searchable.
- **Turma:** searchable por código/disciplina.

---

## Convenções e regras para contribuição

1. **Naming:** Código de domínio (models, exceptions, services, repositories) usa nomes em **português**. Idioms Python/Django em inglês.
2. **IDs:** Sempre UUID v4, auto-gerado, não-editável.
3. **Validação:** Sempre via `full_clean()` antes de `save()` nos repositories.
4. **Sem delete físico** para Aluno, Professor, Disciplina.
5. **Exports explícitos** nos `__init__.py` de cada pacote (models, repositories, services).
6. **Keyword-only arguments** (`*`) nos métodos create/update de repositories e services.
7. **`select_related`/`prefetch_related`** usados consistentemente nos repositories.
8. **Versão** rastreada em `app/__init__.py` e refletida no CHANGELOG.
9. **Linter:** ruff (sem warnings tolerados).
10. **Testes:** Toda nova feature precisa de testes correspondentes nos 3 níveis (model, service/unit, integration/flow).

---

## Comandos essenciais

```bash
# Setup inicial (venv + deps + migrate)
make setup
.venv\Scripts\activate

# Iniciar servidor de desenvolvimento
make run

# Rodar testes
make tests

# Lint
make lint

# Coverage
make coverage

# Migrate manual (se necessário)
make migrate
```

---

## Migrations

1. **`0001_initial`** — Cria todas as 8 tabelas com definições completas de campos, validators, FKs, M2M, e constraint `unique_turma_por_grade_disciplina`.
2. **`0002_aluno_ativo_e_avaliacao_protect`** — Adiciona campo `ativo` ao Aluno; altera FK `Avaliacao.aluno` de CASCADE para PROTECT.

**Ao criar novos models ou alterar fields existentes**, gere a migration com:
```bash
python manage.py makemigrations
```

---

## Fluxo de trabalho recomendado para alterações

1. Entenda a camada afetada (model → repository → service → view).
2. Faça a alteração no model se necessário (gere migration).
3. Adapte o repository para expor a nova operação.
4. Implemente a regra no service.
5. Exponha via view/URL se for funcionalidade web.
6. Escreva testes nos 3 níveis.
7. Rode `make lint` e `make tests`.
8. Atualize `CHANGELOG.md` e bumpe `__version__` se for release.
