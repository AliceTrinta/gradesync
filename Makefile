.PHONY: lint tests coverage run-api down-api

COMPOSE = docker compose
WEB_RUN = $(COMPOSE) run --rm --no-deps -e GRADESYNC_SQLITE=True web

lint:
	$(WEB_RUN) sh -lc "ruff check ."

tests:
	$(WEB_RUN) sh -lc "python manage.py test"

coverage:
	$(WEB_RUN) sh -lc "coverage run --source=app,gradesync manage.py test && coverage report -m"

run-api:
	$(COMPOSE) up -d --build

down-api:
	$(COMPOSE) down
