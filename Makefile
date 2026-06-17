.PHONY: setup migrate run lint tests coverage

PYTHON = python

setup:
	$(PYTHON) -m venv .venv
	.venv\Scripts\pip install --upgrade pip
	.venv\Scripts\pip install -r requirements.txt
	.venv\Scripts\python manage.py migrate --noinput
	@echo.
	@echo Ambiente pronto. Ative com: .venv\Scripts\activate

migrate:
	$(PYTHON) manage.py migrate

run:
	$(PYTHON) manage.py runserver

lint:
	$(PYTHON) -m ruff check .

tests:
	$(PYTHON) manage.py test

coverage:
	$(PYTHON) -m coverage run --source=app,gradesync manage.py test
	$(PYTHON) -m coverage report -m
