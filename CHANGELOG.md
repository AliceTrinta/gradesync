# Changelog

Todas as mudancas relevantes deste projeto sao documentadas neste arquivo.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e versionamento semantico ([SemVer](https://semver.org/lang/pt-BR/)).

## [Unreleased]

### Added

- **Editor de blocos do roteiro.** Depois de gerar o roteiro padrao, o
  aluno pode adicionar, editar e remover blocos livremente. Cada slot
  do roteiro ganha um `id` estavel (`uuid.uuid4().hex`) para permitir
  edicao/remocao pontual sem depender de posicao no array.
- **Deteccao de conflito bloco-x-grade.** Antes de gravar qualquer bloco
  (novo ou editado), o service verifica sobreposicao com as cargas
  horarias da grade do aluno e levanta `BlocoConflitaComGradeError`
  com o codigo da disciplina em conflito.
- **Novas rotas** `roteiro/blocos/adicionar/`,
  `roteiro/blocos/<id>/editar/` e `roteiro/blocos/<id>/remover/`
  (todas `@login_required` + `require_POST`).
- **Novas exceptions** `BlocoRoteiroInvalidoError` e
  `BlocoConflitaComGradeError`.
- **`app.cursos.periodo_atual_permitido(hoje=None)`** deriva o periodo
  academico da data corrente (Jan-Abr -> `AAAA.1`, Mai-Nov -> `AAAA.2`,
  Dez -> `(AAAA+1).1`, liberando cadastro do proximo semestre um mes
  antes).
- **Partial `templates/app/_bloco_form_fields.html`** reutilizado pelos
  forms de adicionar e editar bloco (titulo, dia, horas, cor).
- **31 novos testes** cobrindo o editor de blocos:
  - Helpers de modulo (`_normalizar_dia`, `_normalizar_hora`,
    `_intervalos_se_sobrepoem`).
  - Service com `RoteiroRepository` e `Turma` mockados (sucesso, dia
    invalido, titulo vazio, hora invertida, conflito com grade,
    bloco/roteiro inexistente).
  - Integracao HTTP nas 3 rotas do editor (sucesso, conflito,
    dados invalidos, exigencia de POST/login, render da UI).
- **Total: 138 testes passando** (+31 sobre a baseline anterior de 107).

### Changed

- **Slots do roteiro passam a incluir `id`.** O gerador padrao
  `RoteiroService._montar_slots` injeta `uuid.uuid4().hex` em cada
  slot novo. Roteiros pre-existentes continuam sendo renderizados,
  mas so podem ser editados/removidos apos regeneracao.
- **Wizard de grade nao aceita mais periodo digitado.** O input livre
  virou uma badge readonly com o valor derivado de
  `periodo_atual_permitido`, impedindo grades de semestres futuros ou
  passados. Duplicata no mesmo periodo tambem e bloqueada com mensagem
  clara.
- **UI do roteiro reorganizada:** a antiga `.schedule-actions` foi
  substituida por `.roteiro-toolbar` acima do grid, com o select em
  uma pill e botoes `Recriar` / `Excluir` (ghost-danger) alinhados a
  direita. Abaixo do grid vem a nova secao `.bloco-editor` com a
  lista de blocos + botoes editar/remover.
- **`RoteiroService` enxuto:** unificacao das constantes de cor
  (`CORES` — lista de 5 valores, as que a UI oferece), remocao dos
  helpers triviais `_indice_do_bloco` e `_salvar_slots`, e import de
  `Turma` movido para o topo do modulo.
- **Views do editor** capturam ambas as exceptions do bloco em uma
  unica clausula (`except (BlocoConflitaComGradeError,
  BlocoRoteiroInvalidoError)`).

### Fixed

- **Wizard de grade: horarios so aparecem se a disciplina estiver
  marcada.** O `.discipline-picker-cargas` fica colapsado por default
  e aparece via CSS `:has()` quando o checkbox da disciplina esta
  marcado. Um hint textual ocupa o espaco no estado colapsado.
- **Grade renderiza blocos multi-hora corretamente.** `_grid_da_grade`
  e `_grid_do_roteiro` expandem cada carga nas horas cheias que ela
  cobre, com flags `is_head`/`is_tail` para o template exibir codigo +
  horario so no topo e cor conectada nas continuacoes
  (`slot-pill--continua`, `slot-pill--joined-bottom`).
- **Grade nao trunca mais horarios do final da tarde.** `HORAS_GRADE`
  cobre 08:00-17:00 (10 linhas), permitindo blocos ate 18:00 (ex.:
  `Qui 16:00-18:00`).

## [0.4.0] - 2026-08-01

Grade do Semestre + regra "Roteiro exige Grade" + seed de dados.

### Added

- **Feature Grade do Semestre.**
  - Wizard em 2 passos: escolha do curso (Administracao ou Ciencia da
    Computacao) e selecao de disciplinas + horarios.
  - View `grade_list` lista as grades do aluno em cards com chips das
    disciplinas.
  - View `grade_detalhe` renderiza a grade semanal (grid hora x dia)
    com cores rotativas por disciplina + lista de turmas.
  - View `grade_excluir` com confirm-box e verificacao de posse.
  - Novas URLs: `grades/`, `grades/nova/`, `grades/<uuid>/`,
    `grades/<uuid>/excluir/`.
  - Item **Grade** no `NAV_ITEMS` (entre Inicio e Roteiro).
  - Card destacado no dashboard home ("Grade do Semestre").
- **Regra de negocio: Roteiro exige Grade.**
  - `RoteiroService.gerar_roteiro_padrao(*, aluno, grade)` agora exige
    `grade` e levanta `RoteiroSemGradeError` se `None`.
  - Slots do roteiro derivam das disciplinas da grade
    (`Estudar {codigo}`), distribuidos em blocos livres da semana.
  - Template `roteiro.html` cobre 3 estados: sem grade (CTA para criar),
    com grade sem roteiro (select + botao gerar), com roteiro (grid +
    acoes recriar/excluir).
- **Command `seed_dados`:** popula catalogo mockado idempotente
  (8 professores, 10 cargas horarias, 12 disciplinas ADM,
  13 disciplinas CC, incluindo pre-requisitos). Flag `--limpar` para
  reset completo. Respeita `--verbosity`.
- **Helper `app/cursos.py`:** agrupamento de disciplinas por prefixo
  do codigo (`ADM-*`, `CC-*`) sem criar novo model.
- **`DisciplinaService.listar_por_curso(codigo)`.**
- **`GradeService.criar_grade_do_aluno(*, aluno, periodo, selecoes)`**
  cria grade + turmas atomicamente (`@transaction.atomic`) e valida
  conflito de horario via `SimulacaoService.detectar_conflito_horario`,
  fazendo rollback se houver sobreposicao.
- **`GradeService.listar_do_aluno(aluno)`** — grades ordenadas por
  `-periodo`.
- **Excecao `RoteiroSemGradeError`** em `app/exceptions.py`.
- **16 novos testes** (86 no total):
  - `GradeUITests`: lista vazia, wizard passos 1 e 2, criacao com
    selecoes, conflito de horario, sem disciplinas, detalhe,
    isolamento entre alunos, exclusao POST, item no navbar.
  - `SeedDadosCommandTests`: cria catalogo + idempotencia.
  - `RoteiroServiceRegraDeGradeTests`: sem grade levanta erro, grade
    vazia salva slots vazios.
  - `RoteiroUITests` refatorado para cobrir os 3 estados.

### Changed

- View `roteiro_criar` valida existencia de grade e redireciona para
  `grade-list` com mensagem se o aluno ainda nao tem grade.
- `GradeService` ganhou dependencia injetavel `simulacao_service`
  (mantendo compat com testes que so passam `grade_repository`).
- Estilos de grade adicionados em `styles.css` (`.entity-list`,
  `.wizard-panel`, `.curso-choice`, `.discipline-picker`,
  `.confirm-box`, `.turma-list`) com breakpoints responsivos.

## [0.3.0] - 2026-07-01

Isolamento de CRUDs legados + unificação visual + regras de negócio,
novos models, UI conectada e ops.

### Added

- **Novos models e servicos:**
  - `Roteiro` (JSONField `slots`, OneToOne com `Aluno`) + service +
    repository + `RoteiroAdmin`.
  - `Notificacao` (tipos info/sucesso/aviso/erro, `lida`, `link_acao`)
    + service com helpers `info/sucesso/aviso/erro`.
  - `PreferenciaAcessibilidade` (tamanho_fonte, alto_contraste,
    reduzir_animacoes, sublinhar_links) auto-criado via signal
    `post_save`.
  - `PreferenciaConta` (idioma, tema) auto-criado via signal.
  - Migration `0003_roteiro_notificacao_preferencias`.
- **`DesempenhoService`** com `calcular_media_disciplina`,
  `calcular_cr_periodo` e `calcular_cra`.
- **Regras de simulacao:**
  - Validacao de pre-requisitos em
    `SimulacaoService.validar_prerequisitos`.
  - Deteccao de conflito de horario em
    `SimulacaoService.detectar_conflito_horario`.
  - Excecoes `PrerequisitoNaoAtendidoError`, `ConflitoDeHorarioError`.
- **Novas rotas de UI:** `roteiro-criar`, `roteiro-excluir`,
  `notificacoes-marcar-lida`, `notificacoes-marcar-todas`.
- **Preferencias aplicadas no layout:** `<html data-theme>` e
  `<body class="fonte-*">` via context processor + `base.html`.
- **Badge de notificacoes nao lidas** no nav global.
- **Ops:**
  - `python-decouple` para ler `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
    de env.
  - `.env.example` documentando as variaveis.
  - `STATIC_ROOT = BASE_DIR / "staticfiles"` + target
    `make collectstatic`.
  - Templates `404.html` e `500.html` estendendo `base.html`.
  - Licenca MIT.
- **Testes:** `test_desempenho.py` com media/CR/CRA + pre-req +
  conflito (14 testes); `test_web.py` expandido com WebAuthTests,
  RoteiroUITests, NotificacoesUITests, PreferenciaAcessibilidadeUITests,
  PreferenciaContaUITests, RotasLegadasTests (30 testes).
  **Total: 70 testes passando.**

### Changed

- **Unificacao visual completa (Alice + Daniel).** As 7 paginas
  standalone (roteiro, notificacoes, acessibilidade, config,
  dispositivos, duvidas, sobre) passaram a estender `app/base.html`
  com navbar unica, logo consistente e CSS unificado em `styles.css`.
  CSSs individuais em `app/static/app/*.css` (roteiro.css,
  notificacoes.css, acessibilidade.css, config.css, dispositivos.css,
  duvidas.css, sobre.css) mantidos apenas como referencia historica.
- **Home publica.** Removido `@login_required` de `views.home`. A raiz
  `/` responde 200 para visitantes (landing hero + features + CTA
  final) e mostra dashboard para autenticados.
- **Isolamento dos CRUDs legados.** Rotas de CRUD de Grade, Simulacao,
  Avaliacao, Disciplina, Professor e Perfil foram removidas de
  `urls.py`/`views.py` (recuperaveis via git history se necessarias
  no futuro).
- **`context_processors.gradesync_context`** reescrito para injetar
  `app_version`, `nav_items`, `active_nav`, `notificacoes_nao_lidas`,
  `prefs_acessibilidade` e `prefs_conta`.
- **Banco de dados:** substituido PostgreSQL por SQLite (arquivo
  `db.sqlite3` em dev, in-memory em testes).
- **Makefile** reescrito para rodar comandos locais sem Docker.
  Novos targets: `setup`, `run`, `lint`, `tests`, `coverage`,
  `collectstatic`. Removidos: `run-api`, `down-api`.
- **`requirements.txt`** simplificado (removido `psycopg[binary]`).
- **`settings.py`** simplificado (removidas variaveis `POSTGRES_*` e
  `DJANGO_*`).
- Version bump: `0.2.0` -> `0.3.0`.

### Fixed

- `views.duvidas` e `views.sobre` agora usam prefixo `app/` correto.
- Icone Font Awesome `faright-from-bracket` corrigido para
  `fa-right-from-bracket`.
- Sintaxe CSS invalida `background: color #2563eb;;` corrigida.
- Paginas privadas (`roteiro`, `notificacoes`, `acessibilidade`,
  `configuracoes`, `dispositivos`) receberam `@login_required`.
- `base.html` agora renderiza `nav_items` do context processor.
- `sobre.html` usa `{{ app_version }}` em vez de `1.0.0` hardcoded.

### Removed

- `docker-compose.yml`, `Dockerfile` e `.dockerignore`.
- Dependencia de Docker, Docker Compose e PostgreSQL.
- Arquivo orfao `app/static/app/cadastro.css`.

## [0.2.0] - 2026-05-06

### Added

- CRUDs de servico e repositorio para `Avaliacao`, `CargaHoraria`,
  `Disciplina`, `Professor` e `Turma`.
- Cobertura de testes para os novos CRUDs, regras de dominio de
  simulacao e desativacao de aluno.
- Campo `ativo` em `Aluno` para desativacao logica.
- Migration `app.0002_aluno_ativo_e_avaliacao_protect`.
- `Makefile` com atalhos para `lint`, `tests`, `coverage`, `run-api`,
  `down-api`.
- Dependencias `ruff` e `coverage`.

### Changed

- Reorganizacao para o padrao Django, removendo a antiga estrutura
  `domain/`.
- Separacao definitiva entre `models/`, `services/`, `repositories/`
  e `exceptions.py`.
- Regras de dominio de `Simulacao`: ao confirmar, a `Grade` e criada
  e o rascunho e removido.
- Regras de dominio de `Avaliacao`: nao existe mais rascunho;
  `professor` e `disciplina` sao obrigatorios.
- `Avaliacao.aluno` passou a usar `PROTECT` para preservar historico.
- Exclusao de `Aluno` substituida por desativacao logica.
- `AlunoRepository.list()` passou a listar apenas alunos ativos.
- Atualizacao de senha passou a usar `set_password()` corretamente.
- Operacoes criticas de `Aluno` e confirmacao de `Simulacao`
  protegidas por transacoes.
- Django Admin melhorado com `ModelAdmin`, filtros, busca e bloqueio
  de delete para `Aluno`, `Professor` e `Disciplina`.
- Suite de testes reorganizada em `app/tests/` (`test_models`,
  `test_services`, `test_flows`).

### Removed

- Estrutura legada `app/domain/`.
- Arquivo legado `app/tests.py`.
- Campo `avaliacao_completa` de `Avaliacao`.

### Security

- Desativacao do usuario Django vinculado ao aluno quando este e
  desativado.

## [0.1.0] - 2026-05-04

### Added

- Base inicial do projeto GradeSync com Django.
- Configuracao minima do projeto Django em `gradesync/`.
- Aplicacao `app` com `AppConfig`, `models`, `admin`, `tests` e
  migrations.
- Configuracao de PostgreSQL como banco principal via variaveis de
  ambiente.
- Configuracao de Docker e Docker Compose (`web` + `db`).
- Migration inicial `app.0001_initial`.
- Registro das entidades no Django Admin.
- Testes automatizados para validacoes essenciais.
- `readme.md` inicial com requisitos e comandos.

### Security

- Remocao do armazenamento direto de senha em `Aluno`.
- Uso do sistema de autenticacao do Django (senha com hash).
