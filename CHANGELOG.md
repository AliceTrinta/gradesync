# Changelog

Todas as mudancas relevantes deste projeto sao documentadas neste arquivo.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e versionamento semantico ([SemVer](https://semver.org/lang/pt-BR/)).

## [Unreleased]

### Added — M10: Assistente por IA (Google Gemini)

- **`AIService`** (`app/services/ai_service.py`) — adapter sobre
  `google-generativeai` com duas operacoes publicas:
  `sugerir_roteiro()` (JSON estrito) e `responder_duvida()` (texto).
  Cliente Gemini injetavel via construtor (`client=...`) para os
  testes, sem tocar a rede. `SYSTEM_ROTEIRO` e `SYSTEM_DUVIDAS`
  como constantes de modulo.
- **Roteiro via IA** — `POST /roteiro/criar-ia/`, botao
  `✨ Sugerir com IA` no empty state do roteiro. O service calcula
  blocos livres subtraindo as cargas da grade, envia prompt com
  regras rigidas (`06:00-22:00`, blocos 1h/2h, max 3/dia e 12/semana,
  proporcional a carga_horaria) e valida cada slot devolvido antes
  de gravar. Slots invalidos sao descartados silenciosamente.
- **Chatbot real** — `POST /duvidas/perguntar/`. A tela `/duvidas/`
  faz `fetch()` AJAX com typing indicator (3 dots). O service injeta
  contexto (primeiro nome + estado de grade/roteiro/preferencias) e
  **nunca vaza PII** (matricula, email, username, senha).
- **Cache LocMem** — chave `ai:{prefixo}:{modelo}:{SHA-256(prompt)}`,
  TTL 1h para roteiro e 30min para duvidas. `use_cache=False`
  ignora leitura/gravacao.
- **Rate-limit no chatbot** — 10 perguntas/hora deslizante por
  sessao. Ao estourar, endpoint devolve HTTP 200 com
  `fonte: "fallback"` e nao consome cota.
- **Fallback do roteiro:** sem chave → `AIProviderError` imediato
  (botao nem aparece); IA falha → roteiro cai no gerador
  deterministico (`messages.warning`); IA responde com <
  `MIN_SLOTS_IA=4` slots validos → tambem cai no gerador.
  `prompt_usado` grava `"[IA] ..."` ou
  `"[fallback deterministico apos IA devolver N slots]"`.
- **Chatbot sem fallback local:** quando `ia_disponivel=False` ou a
  chamada ao Gemini falha, o front exibe uma mensagem curta
  explicando o estado (`MSG_OFFLINE` / `MSG_ERRO`) em vez de
  responder com conteudo pre-escrito.
- **Novas exceptions** em `app/exceptions.py`: `AIProviderError` (base),
  `AITimeoutError`, `AIQuotaExceededError`, `AIRespostaInvalidaError`.
  `_chamar_gemini` traduz `TimeoutError` e mensagens contendo
  `quota|rate|429|deadline|timeout` para as exceptions especificas.
- **Novas settings** (via `python-decouple`, defaults em
  `settings.py`): `AI_PROVIDER=gemini`, `AI_API_KEY=""`,
  `AI_MODEL=gemini-1.5-flash`, `AI_TIMEOUT_SECONDS=30`,
  `AI_MAX_TOKENS=1024`. Chave vazia desliga a IA.
- **Context processor** publica `ia_disponivel = bool(AI_API_KEY)`.
  Botoes/toggles dependentes de IA so aparecem quando `True`.
- **`python manage.py ai_ping`** — comando de sanidade que faz UMA
  chamada bypassando cache, mede latencia em ms e imprime preview.
  Exit 0 = OK, 1 = falha. Alias `make ai-ping`.
- **Dependencia** `google-generativeai>=0.7,<1.0` no
  `requirements.txt`.
- **52 novos testes** (baseline 157 → agora **209**, 3 opt-in de
  rede real via `@skipUnless(bool(os.getenv("AI_API_KEY")))`):
  27 unitarios do `AIService` (parse JSON, cache HIT/MISS, traducao
  de erros do SDK, prompts, PII), 8 do `RoteiroService.sugerir_via_ia`
  (fallback quando < 4 slots, filtragem por faixa e por conflito com
  grade), 5 da view `roteiro_criar_ia`, 7 da view `duvidas_perguntar`
  (rate-limit dispara na 11a pergunta), 3 de integracao real.

### Changed

- **`RoteiroService.CORES`** — `"amber"` (nao existia em
  `Roteiro.choices`) trocado por `"orange"`. Teste
  `test_editar_bloco_atualiza_slot_pelo_id_preservando_outros`
  atualizado.
- **`_preparar_bloco`** agora valida faixa horaria via
  `_garantir_dentro_da_faixa_permitida` quando chamado por
  `sugerir_roteiro_via_ia`, rejeitando blocos fora de 06:00-22:00
  mesmo que a IA nao respeite o system prompt.
- **`duvidas.html`** — form com `{% csrf_token %}` +
  `data-endpoint` + `data-ia-disponivel` (lidos via `form.dataset`,
  para nao misturar template tags dentro do JavaScript). O chat
  sempre delega ao endpoint quando `ia_disponivel=True`; se a IA
  estiver desligada mostra `MSG_OFFLINE`, se a rede falhar mostra
  `MSG_ERRO`. Sem fallback client-side com respostas pre-escritas.
- **`roteiro.html`** — botao `✨ Sugerir com IA` renderizado so se
  `ia_disponivel = True`. O form da IA usa `data-sync-from="grade_id"`
  para copiar o valor do `<select>` principal via handler generico no
  `extra_js`.
- **`styles.css`** — `.chat-bubble--loading` com 3 dots animados
  (`@keyframes chatBubbleLoadingBlink`), respeitando
  `body.reduzir-animacoes` e `prefers-reduced-motion: reduce`.
  Nova classe `.empty-panel-form--ia` para o form de sugestao IA.
- **Teste `test_csrf_token_removido_do_form` → `test_csrf_token_esta_no_form_para_endpoint_ajax`**
  com asserticao invertida (agora exige o token).

### Fixed

- **`SYSTEM_DUVIDAS` usava surrogate halves UTF-16** que quebravam
  `SHA-256(prompt.encode('utf-8'))` com
  `UnicodeEncodeError: surrogates not allowed`. Substituidos por
  code points UCS-4 (`\U0001F4C5`, `\U0001F4D6`, `\U0001F512`,
  `\U0001F511`, `\U0001F514`).


## [Baseline anterior]

### Added

- **Fluxo "Esqueceu a sua senha?"** completo usando as views prontas
  do `django.contrib.auth` com templates proprios do GradeSync:
  `PasswordResetView` (form) -> `PasswordResetDoneView` (aviso) ->
  e-mail com link -> `PasswordResetConfirmView` (nova senha) ->
  `PasswordResetCompleteView` (sucesso). As 4 rotas ficam no root
  urlconf (`gradesync/urls.py`) sem namespace porque a view interna
  do Django resolve `password_reset_confirm` via `reverse()` sem
  prefixo. Link "Esqueceu a sua senha?" adicionado em `login.html`.
- **`EMAIL_BACKEND` padrao = console** (`django.core.mail.backends
  .console.EmailBackend`) para que o link de recuperacao aparece no
  terminal do servidor em ambientes de desenvolvimento. Em producao,
  basta sobrescrever via variavel de ambiente `EMAIL_BACKEND` /
  `DEFAULT_FROM_EMAIL`.
- **Pagina de Privacidade** dedicada (`app:privacidade`) com secoes
  "O que guardamos", "O que fazemos com esses dados" e "Seus
  direitos". O item Privacidade em Configuracoes deixa de apontar
  para `/admin/` e passa a abrir a nova pagina.
- **Templates de recuperacao de senha** (`app/password_reset_*.html`)
  e template de e-mail (`app/password_reset_email.html` +
  `password_reset_subject.txt`) alinhados a identidade visual do
  restante do sistema (usa `app/base.html`).
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
- **46 novos testes** (+31 do editor de blocos, +15 dos fixes de UX):
  - Editor de blocos (31): helpers de modulo
    (`_normalizar_dia`, `_normalizar_hora`,
    `_intervalos_se_sobrepoem`); service com `RoteiroRepository` e
    `Turma` mockados (sucesso, dia invalido, titulo vazio, hora
    invertida, conflito com grade, bloco/roteiro inexistente);
    integracao HTTP nas 3 rotas do editor (sucesso, conflito,
    dados invalidos, exigencia de POST/login, render da UI).
  - `CadastroLabelsPtBrTests` (2): garante labels "Nome",
    "Sobrenome", "E-mail", "Usuario", "Matricula", "Senha",
    "Confirme a senha" no `<label>` e ausencia dos auto-gerados
    em ingles.
  - `SublinharLinksTests` (2): checa que a classe `sublinhar-links`
    aparece / desaparece do `<body>` conforme a preferencia.
  - `HtmlLangDinamicoTests` (2): `<html lang>` reflete o idioma
    escolhido em Configuracoes.
  - `PrivacidadeUITests` (3): rota exige login, renderiza conteudo
    esperado e o link de "Privacidade" em Configuracoes nao aponta
    mais para `/admin/`.
  - `EsqueceuSenhaTests` (5): link no login, form renderiza, POST
    valido dispara e-mail (via `mail.outbox`), paginas done e
    complete acessiveis.
  - `GradeFormEmptyStateTests` (1): curso sem disciplinas mostra
    painel explicativo + dica `seed_dados` e esconde o botao
    "Criar grade".
  - `DuvidasPageTests` (3): a pagina renderiza os chips de
    sugestao, o form aponta para o endpoint AJAX com
    `csrfmiddlewaretoken` presente, e a flag `data-ia-disponivel`
    e exposta para o JavaScript.
- **Total: 157 testes passando** (+50 sobre a baseline anterior de 107).

### Changed

- **Labels do formulario de cadastro/login em portugues.**
  `CadastroForm` e `LoginForm` (em `app/forms.py`) agora declaram
  `label=` explicito em cada campo ("Nome", "Sobrenome", "E-mail",
  "Usuario", "Matricula", "Senha", "Confirme a senha"). Antes o
  Django auto-gerava os labels a partir do nome do campo, ficando
  "First name", "Last name", "Password confirm" no HTML, com os
  placeholders em portugues, gerando incoerencia PT/EN na tela.
- **`<html lang>` reflete a preferencia de idioma do aluno.** Em
  `templates/app/base.html` a linha do html deixou de ser
  `<html lang="pt-br">` hardcoded e passou a usar
  `{{ prefs_conta.idioma|default:'pt-BR' }}`. Mudar o idioma em
  Configuracoes ja altera o atributo (util para leitores de tela).
  Traducao completa da UI ainda esta em desenvolvimento; texto
  explicativo adicionado ao item Idioma em `config.html`.
- **Body class ganha `sublinhar-links` quando a preferencia esta
  ativa.** Regras CSS correspondentes adicionadas em `styles.css` e
  `prefs.css` (`body.sublinhar-links a { text-decoration: underline;
  }`). Antes o toggle salvava no banco mas nao surtia efeito visual.
- **Empty state do wizard de grade.** Quando o curso escolhido nao
  tem disciplinas cadastradas, `grade_form.html` mostra um painel
  `.empty-panel` com icone, titulo, explicacao e dica para rodar
  `python manage.py seed_dados`, alem de esconder o botao "Criar
  grade" (que nao tinha o que submeter).
- **Item Privacidade em Configuracoes.** Antes o `<a>` apontava para
  `{% url 'admin:index' %}`, jogando o aluno no painel administrativo
  do Django. Agora aponta para `{% url 'app:privacidade' %}`.
- **Chatbot da Central de Ajuda reescrito.** As respostas locais
  em `duvidas.html` cobriam grade, roteiro, blocos, pre-requisitos,
  acessibilidade, privacidade, senha/esqueci, idioma, tema,
  notificacoes, dispositivos, sobre, excluir, conflito e admin,
  com acentos corretos, emoji discreto no comeco e bullets `•`.
  Referencias a `/admin/grades/` e ao antigo texto "CRUD web
  dedicado esta sendo trabalhado" foram substituidas pelas rotas
  web reais (`/grades/nova/`, `/roteiro/`, etc.). Saudacoes basicas
  passaram a receber resposta dedicada. Fallback tambem foi
  reescrito para apontar para a pagina Sobre em vez de `/admin/`.
  (No M10 essa camada local foi removida em favor de respostas
  geradas pela IA.)
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

- **Cadastro com labels em ingles.** Ver Changed acima (M1).
- **Preferencia "Sublinhar links" sem efeito.** Toggle salvava no
  banco mas nao aparecia no `<body>` nem tinha regra CSS
  correspondente (M6).
- **Idioma escolhido nao afetava a pagina.** Pelo menos o atributo
  `<html lang>` agora reflete a escolha (M7). Traducao completa
  da UI ainda depende de implementar i18n do Django (`.po`/`.mo`).
- **Item "Privacidade" abria o painel admin.** Rota dedicada
  criada (M8).
- **Ausencia de fluxo "Esqueceu a senha?".** Rotas + templates
  + `EMAIL_BACKEND` console configurados (M9).
- **Chatbot recomendava o painel admin.** A resposta para "grade"
  agora aponta ao wizard `/grades/nova/` (M4). Fallback tambem
  deixou de mencionar `/admin/`.
- **Chatbot ignorava perguntas curtas como cumprimento.** Frases
  como "oi", "ola", "bom dia" caiam no fallback generico; passaram
  a ganhar resposta dedicada nas versoes anteriores. (No M10 toda
  a logica de resposta migrou para a IA.)
- **`{% csrf_token %}` removido do form do chatbot.** O form
  tinha `onsubmit="return false;"` e nunca fazia POST, entao o
  token era ruido inutil.
- **Arquivo CSS orfao `app/static/app/duvidas.css` removido.**
  Nao era carregado por nenhum template e usava classes
  (`.topo`, `.robo`, `.caixaconteudo`, `.barrainput`) que nao
  existem no HTML atual — restos de uma versao anterior da
  pagina.
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
