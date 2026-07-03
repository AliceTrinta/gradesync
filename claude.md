# CLAUDE.md — Guia completo do projeto GradeSync

## Visão geral

GradeSync é um sistema acadêmico de gerenciamento de grades curriculares, construído com Django 5.x. Permite que alunos gerenciem suas grades de horários, simulem futuras escolhas de disciplinas e acompanhem avaliações acadêmicas.

- **Versão atual:** `0.4.0` (definida em `app/__init__.py`)
- **Framework:** Django 5.x
- **Banco de dados:** SQLite (arquivo `db.sqlite3` em dev, in-memory em testes)
- **Linguagem:** Python 3.12+
- **Gestão de env:** `python-decouple` (ler `.env` opcional)

> **Estado atual:** os CRUDs web legados de Simulação, Avaliação,
> Disciplina, Professor e Perfil foram removidos — use `/admin/`. As 7
> páginas standalone (roteiro, notificações, acessibilidade, config,
> dispositivos, dúvidas, sobre) foram migradas para `base.html`. Estão
> em produção: Roteiro dinâmico com **editor de blocos** (adicionar,
> editar, remover blocos livres com detecção de conflito contra a
> grade), Notificações, Preferências de Acessibilidade e Conta,
> regras de negócio (CR, pré-req, conflito de horário),
> **Grade do Semestre** (wizard em 2 passos com período automático,
> bloqueio de duplicata, colapso condicional dos horários via CSS
> `:has()`) e comando `seed_dados` idempotente com catálogo mockado
> de ADM + CC. **138 testes verdes.**

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
├── .env.example                    ← Template de variáveis de ambiente
├── LICENSE                         ← MIT
│
├── app/                            ← Aplicação Django principal
│   ├── __init__.py                 ← __version__ = "0.4.0"
│   ├── admin.py                    ← Django Admin customizado
│   ├── apps.py                     ← GradeSyncConfig (registra signals)
│   ├── context_processors.py       ← Injeta app_version, nav_items, prefs, badges
│   ├── cursos.py                   ← Cursos disponíveis (ADM, CC)
│   ├── exceptions.py               ← Exceções de domínio
│   ├── forms.py                    ← LoginForm + CadastroForm
│   ├── signals.py                  ← post_save Aluno → cria prefs default
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
│   │   ├── notificacao.py
│   │   ├── preferencia_acessibilidade.py
│   │   ├── preferencia_conta.py
│   │   ├── professor.py
│   │   ├── roteiro.py
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
│   │   ├── notificacao_repository.py
│   │   ├── preferencia_repository.py
│   │   ├── professor_repository.py
│   │   ├── roteiro_repository.py
│   │   ├── simulacao_repository.py
│   │   └── turma_repository.py
│   │
│   ├── services/                   ← Lógica de negócio / casos de uso
│   │   ├── __init__.py             ← Re-exporta todos os services
│   │   ├── aluno_service.py
│   │   ├── avaliacao_service.py
│   │   ├── cargahoraria_service.py
│   │   ├── desempenho_service.py           ← CR / CRA / média
│   │   ├── disciplina_service.py
│   │   ├── grade_service.py
│   │   ├── notificacao_service.py
│   │   ├── preferencia_service.py
│   │   ├── professor_service.py
│   │   ├── roteiro_service.py
│   │   ├── simulacao_service.py            ← + pré-req + conflito de horário
│   │   └── turma_service.py
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   ├── 0002_aluno_ativo_e_avaliacao_protect.py
│   │   └── 0003_roteiro_notificacao_preferencias.py
│   │
│   ├── management/commands/
│   │   └── seed_dados.py            ← catálogo mockado idempotente
│   │
│   ├── templates/
│   │   ├── 404.html                ← Handler global
│   │   ├── 500.html                ← Handler global
│   │   └── app/                    ← Templates da aplicação
│   │       ├── base.html           ← Layout master (Inter + FontAwesome + blocks)
│   │       ├── home.html
│   │       ├── login.html
│   │       ├── cadastro.html
│   │       ├── sobre.html
│   │       ├── duvidas.html
│   │       ├── config.html         ← Preferências de Conta
│   │       ├── acessibilidade.html ← Preferências de acessibilidade
│   │       ├── notificacoes.html   ← Lista real
│   │       ├── roteiro.html        ← Grid semanal + editor de blocos
│   │       ├── _bloco_form_fields.html ← Partial reusado por add/edit bloco
│   │       ├── grade_list.html
│   │       ├── grade_form.html     ← Wizard 2 passos + período automático
│   │       ├── grade_detalhe.html
│   │       ├── grade_confirm_delete.html
│   │       └── dispositivos.html   ← Mock (não conectado)
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
- **Campos:** `dia` (CharField max 16), `hora_inicio` (TimeField), `hora_final` (TimeField)
- **Validação:** dia não pode ser vazio; `hora_final` deve ser posterior a `hora_inicio`

### Disciplina
- **PK:** UUID
- **Campos:** `codigo` (unique, max 32), `nome` (max 255), `taxa_de_reprovacao` (Decimal 0–100, ajuda o aluno a avaliar risco), `prerequisitos` (M2M self, assimétrico)
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
- **Campos:** `codigo` (max 32), `capacidade` (PositiveInt), `grade` (FK → Grade, CASCADE, `related_name="turmas"`), `disciplina` (FK → Disciplina, CASCADE), `cargas` (M2M → CargaHoraria, blank)
- **Constraint:** `unique_turma_por_grade_disciplina` (grade, disciplina)
- **Validação:** codigo não pode ser vazio

---

## Models de preferências, roteiro e notificações

### Roteiro
- **PK:** UUID
- **Relação:** OneToOne com `Aluno` (`related_name="roteiro"`)
- **Campos:** `titulo` (max 120), `slots` (JSONField — lista de dicts com
  `id`, `dia`, `hora_inicio`, `hora_final`, `titulo`, `cor`), `prompt_usado`
  (Text), timestamps
- **Validação:** slots devem ser lista; cada slot precisa de
  dia/hora_inicio/hora_final/titulo. Slots gerados pelo service ganham
  `id = uuid.uuid4().hex` para permitir edição/remoção pontual.

### Notificacao
- **PK:** UUID
- **Relação:** FK → `Aluno` CASCADE (`related_name="notificacoes"`)
- **Campos:** `tipo` (info/sucesso/aviso/erro), `titulo`, `mensagem`, `lida`, `link_acao`, `criada_em`
- **Meta:** `ordering = ("-criada_em",)`

### PreferenciaAcessibilidade
- **Relação:** OneToOne com `Aluno` (`related_name="prefs_acessibilidade"`)
- **Campos:** `tamanho_fonte` (pequeno/medio/grande/muito-grande), `alto_contraste`, `reduzir_animacoes`, `sublinhar_links`
- **Auto-criado** via signal `post_save` no Aluno

### PreferenciaConta
- **Relação:** OneToOne com `Aluno` (`related_name="prefs_conta"`)
- **Campos:** `idioma` (pt-BR/en-US), `tema` (claro/escuro)
- **Auto-criado** via signal `post_save` no Aluno

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

class PrerequisitoNaoAtendidoError(GradeSyncError):  # Falta pré-requisito
    def __init__(self, disciplina, faltantes): ...
class ConflitoDeHorarioError(GradeSyncError):        # Turmas com horário sobreposto
    def __init__(self, turma_a, turma_b, carga_a, carga_b): ...

class RoteiroSemGradeError(GradeSyncError):          # Roteiro pediu grade e não tem
class BlocoRoteiroInvalidoError(GradeSyncError):     # Dia/hora/título/bloco_id inválidos
class BlocoConflitaComGradeError(GradeSyncError):    # Bloco choca com carga da grade
    def __init__(self, *, dia, hora_inicio, hora_final, disciplina_codigo): ...
```

### Regras de desempenho e simulação

- **`DesempenhoService.calcular_media_disciplina(aluno, disciplina)`** — Média
  aritmética simples das notas das avaliações do aluno na disciplina.
- **`DesempenhoService.calcular_cr_periodo(aluno, periodo)`** — Média
  simples do período (todas as disciplinas cursadas naquele período).
- **`DesempenhoService.calcular_cra(aluno)`** — Média simples de todas as
  avaliações do aluno.
- **`SimulacaoService.validar_prerequisitos(simulacao, nova_turma)`** — Bloqueia
  se o aluno nunca cursou os pré-requisitos da disciplina da turma.
- **`SimulacaoService.detectar_conflito_horario(simulacao, nova_turma)`** —
  Bloqueia se qualquer `CargaHoraria` da nova turma sobrepor a de outra
  turma já na simulação (mesmo dia + intervalo intersecta).

---

## Configuração e infraestrutura

### settings.py
- **Banco:** SQLite — arquivo `db.sqlite3` em desenvolvimento, in-memory para testes (automático quando `test` está em `sys.argv`).
- **Idioma:** `pt-br`, timezone `America/Sao_Paulo`, USE_TZ=True.
- **Static:** `STATIC_URL="static/"`, `STATIC_ROOT=BASE_DIR/"staticfiles"`.
- **Env vars via `python-decouple`:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
  (com cast tolerante para bool, defaults funcionam sem `.env`).
- **Context processor customizado:** `app.context_processors.gradesync_context`
  injeta `app_version`, `aluno`, `nav_items`, `notificacoes_nao_lidas`,
  `prefs_acessibilidade`, `prefs_conta`, `active_nav`.
- **Signals:** ao criar um `Aluno`, `PreferenciaAcessibilidade` e
  `PreferenciaConta` default são criadas automaticamente.

### requirements.txt
| Pacote | Versão |
|--------|--------|
| Django | ≥5.0, <6.0 |
| python-decouple | ≥3.8, <4.0 |
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
| `make collectstatic` | `collectstatic --noinput` para `staticfiles/` |

### Comando customizado

| Comando | O que faz |
|---------|-----------|
| `python manage.py seed_dados` | Popula 8 professores, 10 cargas horárias e 25 disciplinas (ADM + CC) com pré-req. Idempotente. Aceita `--limpar`. |

---

## Rotas (URLs) — estado atual v0.4.0

O namespace da app é `app`. A view `api_status` retorna JSON com `status`,
`app`, `version` e `endpoints`.

### Públicas (sem login)

| Path | View | Name |
|------|------|------|
| `/login/` | `login_view` | `app:login` |
| `/logout/` | `logout_view` | `app:logout` |
| `/cadastro/` | `cadastro` | `app:cadastro` |
| `/api/status/` | `api_status` | `app:api-status` |
| `/sobre/` | `sobre` | `app:sobre` |
| `/duvidas/` | `duvidas` | `app:duvidas` |

### Autenticadas (`@login_required`)

| Path | View | Name |
|------|------|------|
| `/` | `home` | `app:home` |
| `/grades/` | `grade_list` | `app:grade-list` |
| `/grades/nova/` | `grade_criar` | `app:grade-criar` |
| `/grades/<uuid>/` | `grade_detalhe` | `app:grade-detalhe` |
| `/grades/<uuid>/excluir/` | `grade_excluir` | `app:grade-excluir` |
| `/roteiro/` | `roteiro` | `app:roteiro` |
| `POST /roteiro/criar/` | `roteiro_criar` | `app:roteiro-criar` |
| `POST /roteiro/excluir/` | `roteiro_excluir` | `app:roteiro-excluir` |
| `POST /roteiro/blocos/adicionar/` | `roteiro_bloco_adicionar` | `app:roteiro-bloco-adicionar` |
| `POST /roteiro/blocos/<id>/editar/` | `roteiro_bloco_editar` | `app:roteiro-bloco-editar` |
| `POST /roteiro/blocos/<id>/remover/` | `roteiro_bloco_remover` | `app:roteiro-bloco-remover` |
| `/notificacoes/` | `notificacoes` | `app:notificacoes` |
| `POST /notificacoes/<uuid>/marcar-lida/` | `notificacao_marcar_lida` | `app:notificacoes-marcar-lida` |
| `POST /notificacoes/marcar-todas/` | `notificacao_marcar_todas` | `app:notificacoes-marcar-todas` |
| `/configuracoes/` | `configuracoes` | `app:configuracoes` |
| `/acessibilidade/` | `acessibilidade` | `app:acessibilidade` |
| `/dispositivos/` | `dispositivos` | `app:dispositivos` |
| `/admin/` | Django Admin | `admin:index` |

### Rotas legadas removidas

Os CRUDs web de Simulação, Avaliação, Disciplina, Professor e Perfil
foram removidos. Use `/admin/` para essas entidades (recuperáveis via
git history se forem retomadas no futuro).

---

## Frontend / Templates

- **base.html** — Layout master com Google Fonts (Inter), FontAwesome 6.5.1,
  CSS customizado. Header com logo (graduation-cap), topnav dinâmico
  consumindo `nav_items`, badge de notificações não lidas, botões
  Admin/Sair. Blocks: `title`, `extra_head`, `content`, `extra_js`.
  Inclui `<meta name="csrf-token">` para AJAX. Classe do `<body>` reflete
  preferências (`fonte-*`, `alto-contraste`, `reduzir-animacoes`) e
  `<html data-theme>` reflete tema.
- **home.html** — Extends base. Cartão landing com version pill dinâmica.
- **login.html / cadastro.html** — Formulários de auth.
- **sobre.html** — Página institucional, usa `{{ app_version }}`.
- **duvidas.html** — Mockup visual de chatbot (preparado para IA futura).
- **config.html** — Form real de idioma/tema, salva `PreferenciaConta`.
- **acessibilidade.html** — Form real de fonte/contraste/animações,
  salva `PreferenciaAcessibilidade`.
- **notificacoes.html** — Lista real da model `Notificacao` com marcar-lida.
- **roteiro.html** — Grid semanal dinâmica do model `Roteiro`.
- **dispositivos.html** — Mock (não conectado a `django.contrib.sessions`).
- **404.html / 500.html** — Handlers globais (fora de `app/`).

### CSS (`app/static/app/`)
- **styles.css** — Stylesheet único. Variáveis CSS (cores, sombra, border),
  topbar, container, topnav, badges, mensagens toast, classes de fonte,
  `data-theme=escuro`, componentes de Grade (`entity-list`,
  `wizard-panel`, `curso-choice`, `discipline-picker`, `confirm-box`,
  `turma-list`) com breakpoints responsivos.
- CSSs individuais (`config.css`, `acessibilidade.css`,
  `notificacoes.css`, `roteiro.css`, `dispositivos.css`, `duvidas.css`,
  `sobre.css`) permanecem em disco apenas como referência histórica —
  não são mais incluídos pelos templates.

---

## Testes — 138 testes passando

| Arquivo | Tipo | Técnica |
|---------|------|---------|
| `test_models.py` | Validação de models | Instanciação direta + `full_clean()` + assertions |
| `test_services.py` | Unitários | `unittest.mock.patch` + `MagicMock` nos repositories |
| `test_flows.py` | Integração | DB real (SQLite), services com repositories reais |
| `test_desempenho.py` | Regras de desempenho | Média/CR/CRA, pré-requisitos, conflito de horário |
| `test_web.py` | Endpoints HTTP | Django test client — auth, home, roteiro, notif, prefs |

### Cenários testados incluem:

**Domínio original:**
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

**Regras de desempenho e preferências:**
- Cálculo de média de disciplina/período/CRA (aluno sem avaliações → 0)
- Detecção de pré-requisito faltante levanta `PrerequisitoNaoAtendidoError`
- Conflito de horário levanta `ConflitoDeHorarioError`
- Login/logout/cadastro fluxo completo
- `@login_required` redireciona para `/login/?next=`
- Roteiro CRUD (criar padrão, excluir, exigir POST)
- Notificações: listagem, marcar-uma-lida, marcar-todas, badge no header
- Preferências de Acessibilidade: form GET/POST, aplicação no `<body>`,
  valores inválidos ignorados
- Preferências de Conta: form GET/POST, aplicação no `<html data-theme>`

**Grade, roteiro e editor de blocos:**
- Wizard de grade: passo 1 lista os cursos, passo 2 lista as disciplinas
  filtradas por prefixo (`ADM-*`, `CC-*`)
- Criação de grade valida horário de cada disciplina e detecta conflito
  (`ConflitoDeHorarioError`), com rollback via `@transaction.atomic`
- Detalhe da grade renderiza schedule + turmas + cores rotativas
- Isolamento: aluno A não vê/exclui grade de aluno B (404)
- Excluir grade via POST
- Item **Grade** aparece no navbar
- `RoteiroService.gerar_roteiro_padrao` sem grade levanta
  `RoteiroSemGradeError`
- `RoteiroService.gerar_roteiro_padrao` com grade vazia salva slots vazios
- Tela `/roteiro/` cobre 3 estados (sem grade / com grade / com roteiro)
- `seed_dados` cria catálogo completo e é idempotente
- Rotas legadas retornam 404
- **`periodo_atual_permitido`** deriva `AAAA.1` / `AAAA.2` / `(AAAA+1).1`
  da data corrente; wizard usa badge readonly e bloqueia duplicata
- **`_horas_no_intervalo`** expande cargas de 2h+ em N horas consecutivas;
  templates de grade e roteiro usam `is_head`/`is_tail` para juntar as
  pills visualmente
- **Editor de blocos do roteiro:** service com `_normalizar_dia`,
  `_normalizar_hora`, `_intervalos_se_sobrepoem`, `adicionar_bloco`,
  `editar_bloco`, `remover_bloco`; conflito com grade levanta
  `BlocoConflitaComGradeError`; rotas HTTP são POST-only, exigem login,
  redirecionam com messages

---

## Django Admin

Todos os **12 models** registrados com `ModelAdmin` customizado:
- **Aluno, Professor, Disciplina:** `has_delete_permission = False` (deleção física bloqueada).
- **Aluno:** list display com matrícula/usuário/ativo; searchable.
- **Avaliacao:** filtrável por ano/semestre/disciplina/professor.
- **Grade, Simulacao:** filtrável por período; searchable.
- **Turma:** searchable por código/disciplina.
- **Roteiro:** list display com aluno/titulo/atualizado_em.
- **Notificacao:** filtrável por tipo/lida; ação em massa
  "marcar como lidas".
- **PreferenciaAcessibilidade, PreferenciaConta:** editáveis pelo
  admin.

**Como os CRUDs web legados foram removidos, o Admin é o principal
caminho para gerenciar Grade, Simulacao, Avaliacao, Disciplina, Professor,
Turma e CargaHoraria.**

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

1. **`0001_initial`** — Cria todas as 8 tabelas originais com definições
   completas de campos, validators, FKs, M2M, e constraint
   `unique_turma_por_grade_disciplina`.
2. **`0002_aluno_ativo_e_avaliacao_protect`** — Adiciona campo `ativo` ao
   Aluno; altera FK `Avaliacao.aluno` de CASCADE para PROTECT.
3. **`0003_roteiro_notificacao_preferencias`** — cria tabelas
   `Roteiro`, `Notificacao`, `PreferenciaAcessibilidade`,
   `PreferenciaConta`.

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
