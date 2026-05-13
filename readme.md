# GradeSync

## Estrutura do projeto

O projeto possui duas areas principais:

- `app/`: onde fica o codigo da aplicacao e das regras de negocio.
- `gradesync/`: pacote de configuracao do Django.

A pasta `gradesync/` e a estrutura padrao criada pelo Django para guardar arquivos de configuracao do projeto, como:

- `settings.py`: configuracoes da aplicacao, banco, apps instalados e ambiente.
- `urls.py`: roteamento principal.
- `asgi.py` e `wsgi.py`: pontos de entrada para execucao da aplicacao.

Ou seja:

- o diretorio principal de desenvolvimento continua sendo `app/`;
- a pasta `gradesync/` continua importante porque ela configura e inicializa o projeto Django.

## Requisitos

Antes de subir a aplicacao, verifique se o sistema possui:

- Docker
- Docker Compose
- Python 3
- Git
- GNU Make

Para conferir rapidamente:

```powershell
docker --version
docker compose version
python --version
git --version
make --version
```

Se algum comando nao for reconhecido, instale ou ajuste o PATH da ferramenta antes de continuar.

> No Windows, se o `make` tiver sido instalado agora, talvez seja necessario fechar e abrir o terminal novamente para o PATH ser recarregado.

## Executando com Makefile

Na raiz do projeto, os atalhos principais sao:

```powershell
make run-api
make lint
make tests
make coverage
make down-api
```

Descricao dos comandos:

- `make run-api`: sobe os servicos com `docker compose up -d --build`.
- `make lint`: executa `ruff check .` dentro do container da aplicacao.
- `make tests`: executa `python manage.py test` dentro do container com SQLite para testes.
- `make coverage`: executa a suite de testes com `coverage` e gera o relatorio no terminal.
- `make down-api`: encerra os servicos com `docker compose down`.

Se preferir, os comandos Docker equivalentes continuam documentados abaixo.

## Subindo a aplicacao

Na raiz do projeto, execute:

```powershell
docker compose up -d --build
```

Esse comando cria e inicia:

- `db`: banco PostgreSQL
- `web`: aplicacao Django

Depois aplique as migrations:

```powershell
docker compose exec web python manage.py migrate
```

A aplicacao ficara disponivel em:

```text
http://localhost:8000
```

## Rodando verificacoes

Para verificar a configuracao do Django:

```powershell
docker compose exec web python manage.py check
```

Para conferir se as migrations estao sincronizadas com os models:

```powershell
docker compose exec web python manage.py makemigrations --check --dry-run
```

Para rodar os testes:

```powershell
docker compose exec web python manage.py test -v 2
```

Para rodar cobertura sem o Makefile:

```powershell
docker compose run --rm --no-deps -e GRADESYNC_SQLITE=True web sh -lc "coverage run --source=app,gradesync manage.py test && coverage report -m"
```

## Parando a aplicacao

Para parar os containers:

```powershell
docker compose down
```

Para parar e remover tambem o volume do PostgreSQL:

```powershell
docker compose down -v
```

Use `down -v` apenas quando quiser apagar os dados locais do banco.
