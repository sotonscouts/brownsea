.PHONY: all clean fix hooks lint type test test-cov e2e e2e-report

CMD:=uv run
PYMODULE:=brownsea
MANAGEPY:=$(CMD) ./manage.py
SETTINGS_MODULE:=brownsea.core.settings.dev

all: format lint
fix: lint-fix format

lint:
	$(CMD) ruff check $(PYMODULE)

lint-fix:
	$(CMD) ruff check --fix $(PYMODULE)

check:
	$(MANAGEPY) check

dev:
	$(MANAGEPY) runserver

format:
	find $(PYMODULE) -name "*.html" | xargs $(CMD) djhtml
	$(CMD) ruff format $(PYMODULE)

format-check:
	find $(PYMODULE) -name "*.html" | xargs $(CMD) djhtml --check
	$(CMD) ruff format --check $(PYMODULE)

type:
	$(CMD) mypy $(PYMODULE)

test: | $(PYMODULE)
	DJANGO_SETTINGS_MODULE=$(SETTINGS_MODULE) $(CMD) pytest -vv --cov=$(PYMODULE) $(PYMODULE)

test-cov:
	DJANGO_SETTINGS_MODULE=$(SETTINGS_MODULE) $(CMD) pytest -vv --cov=$(PYMODULE) $(PYMODULE) --cov-report html

e2e: | $(PYMODULE)
	npm run build
	$(CMD) playwright install chromium
	mkdir -p reports/e2e
	$(CMD) pytest -vv e2e --cucumberjson=reports/e2e/cucumber.json; status=$$?; npm run e2e:report; exit $$status

e2e-report:
	npm run e2e:report

clean:
	git clean -Xdf # Delete all files in .gitignore

hooks:
	$(CMD) prek install -f
