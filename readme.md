# GradeSync

Sistema academico de gerenciamento de grades curriculares, simulacoes de matricula e avaliacoes, desenvolvido com Django.

---

## Requisitos

| Ferramenta | Versao minima | Obrigatorio |
|-----------|---------------|-------------|
| Python | 3.12+ | Sim |
| Git | qualquer | Sim |
| GNU Make | qualquer | Nao (facilita os comandos) |

Para conferir rapidamente:

```powershell
python --version
git --version
make --version
```

> **Windows:** se `make` nao for reconhecido, instale com `winget install GnuWin32.Make` e reinicie o terminal.

---

## Setup inicial (primeira vez)

### Com Make (recomendado)

```powershell
make setup
.venv\Scripts\activate
```

O comando `make setup` faz tudo automaticamente:
1. Cria o ambiente virtual `.venv`
2. Atualiza o pip
3. Instala as dependencias do `requirements.txt`
4. Aplica todas as migrations (cria o banco SQLite)

### Sem Make (manual)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
```

> **Linux/macOS:** substitua `.venv\Scripts\activate` por `source .venv/bin/activate`.

---

## Executando a aplicacao

Com o ambiente virtual ativado:

```powershell
python manage.py runserver
```

Ou:

```powershell
make run
```

A aplicacao ficara disponivel em **http://localhost:8000**.

### Endpoints disponiveis

| URL | Descricao |
|-----|-----------|
| `/` | Pagina base (interface web) |
| `/admin/` | Painel administrativo Django |
| `/api/status/` | JSON com status da aplicacao |
| `/cadastro/` | Tela de cadastro |
| `/configuracoes/` | Tela de configuracoes |
| `/roteiro/` | Tela de roteiro |

---

## Comandos do Makefile

| Comando | O que faz |
|---------|-----------|
| `make setup` | Cria venv, instala deps e aplica migrations |
| `make run` | Inicia o servidor de desenvolvimento |
| `make migrate` | Aplica migrations pendentes |
| `make lint` | Executa o linter `ruff check .` |
| `make tests` | Executa a suite de testes |
| `make coverage` | Executa testes com cobertura e gera relatorio |

---

## Rodando testes

```powershell
python manage.py test
```

Ou:

```powershell
make tests
```

Para mais detalhe:

```powershell
python manage.py test -v 2
```

Para gerar relatorio de cobertura:

```powershell
make coverage
```

---

## Verificacoes uteis

```powershell
# Verificar configuracao geral do Django
python manage.py check

# Conferir se ha migrations pendentes nao geradas
python manage.py makemigrations --check --dry-run

# Lint (requer ruff instalado na venv)
make lint
```

---

## Banco de dados

O projeto utiliza **SQLite**:

| Ambiente | Configuracao |
|----------|--------------|
| Desenvolvimento | Arquivo `db.sqlite3` na raiz do projeto |
| Testes | Banco in-memory (automatico, sem configuracao) |

- O arquivo `db.sqlite3` esta no `.gitignore` e nao e versionado.
- Para resetar o banco local, basta apagar o arquivo e rodar `make migrate` novamente.

---

## Criando um superusuario (admin)

Para acessar `/admin/`:

```powershell
python manage.py createsuperuser
```

Siga as instrucoes no terminal (username, email, senha).

---

## Estrutura do projeto

```
gradesync/                  ← Raiz
├── app/                    ← Codigo da aplicacao
│   ├── models/             ← Entidades de dominio
│   ├── repositories/       ← Acesso a dados
│   ├── services/           ← Logica de negocio
│   ├── templates/app/      ← Templates HTML
│   ├── static/app/         ← CSS
│   ├── tests/              ← Testes automatizados
│   ├── admin.py            ← Configuracao do Django Admin
│   ├── views.py            ← Views (web + API)
│   ├── urls.py             ← Rotas da app
│   └── exceptions.py       ← Excecoes de dominio
├── gradesync/              ← Configuracao Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── Makefile
├── requirements.txt
└── readme.md
```

### Camadas da arquitetura

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| Models | `app/models/` | Entidades, validacao, constraints |
| Repositories | `app/repositories/` | Queries, persistencia, full_clean antes de save |
| Services | `app/services/` | Regras de negocio, transacoes atomicas |
| Views | `app/views.py` | Interface HTTP |

---

## Dependencias

| Pacote | Versao | Uso |
|--------|--------|-----|
| Django | >=5.0, <6.0 | Framework web |
| coverage | >=7.6, <8.0 | Relatorio de cobertura de testes |
| ruff | >=0.11, <0.12 | Linter Python |

Todas sao instaladas automaticamente pelo `make setup` ou `pip install -r requirements.txt`.
