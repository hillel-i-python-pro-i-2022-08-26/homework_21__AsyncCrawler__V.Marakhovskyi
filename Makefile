.PHONY: homework-i-run
# Run homework.
homework-i-run:
	@python manage.py runserver

.PHONY: homework-i-purge
# Delete all created artifacts, related with homework execution
homework-i-purge:
	@echo Goodbye

.PHONY: init-config
# Init config files
init-config:
	@cp docker-compose.override.dev.yml docker-compose.override.yml && \
		cp .env.dev .env

.PHONY: init-dev
# Init environment for development
init-dev:
	@pip install --upgrade pip && \
	pip install --requirement requirements.txt && \
	pre-commit install


.PHONY: pre-commit-run
# Run tools for files from commit.
pre-commit-run:
	@pre-commit run

.PHONY: pre-commit-run-all
# Run tools for all files.
pre-commit-run-all:
	@pre-commit run --all-files


.PHONY: d-homework-i-run
# Make all actions needed for run homework from zero.
d-homework-i-run:
	@make init-config && \
		make d-run

.PHONY: d-homework-i-purge
# Make all actions needed for purge homework related data.
d-homework-i-purge:
	@make d-purge

