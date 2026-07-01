# GradeSync

Sistema academico para montar a **grade do semestre** e gerar um **roteiro
de estudos semanal** a partir dela, com notificacoes, preferencias de
acessibilidade e tema. Desenvolvido em Django + SQLite.

---

## Requisitos

| Ferramenta | Versao minima | Obrigatorio |
|-----------|---------------|-------------|
| Python | 3.12+ | Sim |
| Git | qualquer | Sim |
| GNU Make | qualquer | Nao (facilita os comandos) |

```powershell
python --version
git --version
make --version
```

> **Windows:** se `make` nao for reconhecido, instale com
> `winget install GnuWin32.Make` e reinicie o terminal.

---

## Setup inicial (primeira vez)

### Com Make (recomendado)

```powershell
make setup
.venv\Scripts\activate
```

O `make setup` cria o `.venv`, atualiza o pip, instala as dependencias e
aplica todas as migrations (cria o `db.sqlite3`).

### Sem Make (manual)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
```

> **Linux/macOS:** substitua `.venv\Scripts\activate` por
> `source .venv/bin/activate`.

### Popular o catalogo mockado

```powershell
python manage.py seed_dados
```

Cria 8 professores, 10 blocos de carga horaria e 25 disciplinas (12 ADM +
13 CC) com pre-requisitos. O comando e **idempotente** — rodar de novo
nao duplica. Use `--limpar` para resetar antes de popular.

---

## Executando a aplicacao

```powershell
make run
```

Ou diretamente:

```powershell
python manage.py runserver
```

A aplicacao ficara disponivel em **http://localhost:8000**.

### Endpoints

**Publicas (sem login):**

| URL | Descricao |
|-----|-----------|
| `/` | Landing (visitante) ou dashboard (autenticado) |
| `/login/` | Tela de login |
| `/cadastro/` | Cadastro de aluno |
| `/sobre/` | Pagina institucional |
| `/duvidas/` | Central de duvidas (mock) |
| `/api/status/` | JSON com status da aplicacao |

**Autenticadas (`@login_required`):**

| URL | Descricao |
|-----|-----------|
| `/grades/` | Lista das grades do aluno |
| `/grades/nova/` | Wizard de criacao (2 passos: curso + disciplinas) |
| `/grades/<uuid>/` | Detalhe da grade (schedule semanal) |
| `/grades/<uuid>/excluir/` | Confirmacao + exclusao |
| `/roteiro/` | Roteiro de estudo semanal |
| `POST /roteiro/criar/` | Gera o roteiro a partir da grade selecionada |
| `POST /roteiro/excluir/` | Remove o roteiro |
| `POST /roteiro/blocos/adicionar/` | Adiciona um bloco livre ao roteiro |
| `POST /roteiro/blocos/<id>/editar/` | Edita um bloco existente |
| `POST /roteiro/blocos/<id>/remover/` | Remove um bloco do roteiro |
| `/notificacoes/` | Lista de notificacoes |
| `POST /notificacoes/<id>/marcar-lida/` | Marca uma como lida |
| `POST /notificacoes/marcar-todas/` | Marca todas como lidas |
| `/configuracoes/` | Idioma + tema |
| `/acessibilidade/` | Tamanho de fonte + contraste + animacoes |
| `/dispositivos/` | Sessoes ativas (mock) |
| `/admin/` | Painel administrativo Django (superuser) |
| `/logout/` | Encerra sessao |

> **Nota:** as rotas de CRUD web para Simulacao, Avaliacao, Disciplina,
> Professor e Perfil foram removidas — use o
> **Django Admin (`/admin/`)** para gerenciar essas entidades.

---

## Fluxo principal (aluno)

1. Faca login (ou cadastro).
2. Acesse **Grade** no menu e clique em **Criar minha primeira grade**.
3. **Passo 1:** escolha o curso (Administracao ou Ciencia da Computacao).
4. **Passo 2:** o periodo do semestre e detectado automaticamente
   (badge readonly). Marque as disciplinas — os horarios so aparecem
   depois de marcar cada uma. Selecione ao menos um horario por
   disciplina. Se dois horarios se sobreporem, a criacao e revertida
   com mensagem de conflito. Duplicata no mesmo periodo tambem e
   bloqueada.
5. Va em **Roteiro** e clique em **Criar roteiro** — ele e gerado a
   partir das disciplinas da grade selecionada.
6. No editor abaixo do grid, **adicione**, **edite** ou **remova**
   blocos livremente. Qualquer bloco que conflite com a grade
   é bloqueado com mensagem clara.

---

## Variaveis de ambiente

Copie `.env.example` para `.env` e ajuste. Em dev, os defaults funcionam
sem `.env`.

| Variavel | Default | Descricao |
|----------|---------|-----------|
| `SECRET_KEY` | `dev-only-secret-key` | Chave secreta do Django |
| `DEBUG` | `True` | Modo debug (use `False` em producao) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos (CSV) |

---

## Comandos do Makefile

| Comando | O que faz |
|---------|-----------|
| `make setup` | Cria venv, instala deps e aplica migrations |
| `make run` | Inicia o servidor de desenvolvimento |
| `make migrate` | Aplica migrations pendentes |
| `make lint` | Executa `ruff check .` |
| `make tests` | Executa a suite de testes |
| `make coverage` | Executa testes com cobertura e gera relatorio |
| `make collectstatic` | Coleta arquivos estaticos em `staticfiles/` |

---

## Rodando testes

```powershell
python manage.py test
```

Ou:

```powershell
make tests
```

Para detalhe:

```powershell
python manage.py test -v 2
```

Para cobertura:

```powershell
make coverage
```

**138 testes** cobrindo models, services, flows e web.

---

## Banco de dados

O projeto usa **SQLite**:

| Ambiente | Configuracao |
|----------|--------------|
| Desenvolvimento | Arquivo `db.sqlite3` na raiz |
| Testes | Banco in-memory (automatico) |

- `db.sqlite3` esta no `.gitignore` e nao e versionado.
- Para resetar: apague o arquivo, rode `make migrate` e depois
  `python manage.py seed_dados` para repopular o catalogo.

---

## Criando um superusuario

```powershell
python manage.py createsuperuser
```

---

## Estrutura do projeto

```
gradesync/                       ← Raiz
├── app/                         ← Codigo da aplicacao
│   ├── models/                  ← 12 entidades de dominio
│   ├── repositories/            ← Acesso a dados (12 repositories)
│   ├── services/                ← Regras de negocio (13 services)
│   ├── templates/app/           ← Templates HTML
│   ├── static/app/              ← styles.css unificado
│   ├── tests/                   ← Testes (138 testes)
│   ├── management/commands/     ← seed_dados
│   ├── admin.py                 ← Django Admin
│   ├── views.py                 ← Views (web + API)
│   ├── urls.py                  ← Rotas da app
│   ├── forms.py                 ← Forms (login, cadastro)
│   ├── signals.py               ← Auto-cria prefs default
│   ├── context_processors.py    ← Injeta app_version, nav_items, prefs
│   ├── cursos.py                ← Cursos disponiveis (ADM, CC)
│   └── exceptions.py            ← Excecoes de dominio
├── gradesync/                   ← Configuracao Django
│   ├── settings.py              ← Le .env via python-decouple
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── .env.example                 ← Template de env vars
├── LICENSE                      ← MIT
├── manage.py
├── Makefile
├── requirements.txt
├── CHANGELOG.md
├── claude.md                    ← Documentacao tecnica detalhada
└── readme.md
```

### Camadas da arquitetura

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| Models | `app/models/` | Entidades, validacoes, constraints |
| Repositories | `app/repositories/` | Queries, persistencia, `full_clean` antes de `save` |
| Services | `app/services/` | Regras de negocio, transacoes atomicas |
| Views | `app/views.py` | Interface HTTP |

---

## Dependencias

| Pacote | Versao | Uso |
|--------|--------|-----|
| Django | >=5.0, <6.0 | Framework web |
| python-decouple | >=3.8, <4.0 | Leitura de variaveis de ambiente |
| coverage | >=7.6, <8.0 | Cobertura de testes |
| ruff | >=0.11, <0.12 | Linter Python |

Todas sao instaladas automaticamente pelo `make setup`.
