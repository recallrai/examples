SERVICE_NAME = recallrai-demo-email-agent

.PHONY: all install enable start status logs stop disable clean deps start_dev_server deploy dev

# ----------Development commands----------
all: dev

deps:
	@echo "Installing dependencies ..."
	poetry install

start_dev_server:
	@echo "Starting development server ..."
	poetry run streamlit run main.py --server.port 8000

# format:
# 	@echo "Formatting code ..."
# 	poetry run black --line-length 100 --skip-string-normalization --skip-magic-trailing-comma --target-version py310 app

dev: deps start_dev_server

# ----------Production commands (Docker)----------
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec $(SERVICE_NAME) /bin/bash

clean:
	docker compose down -v
	docker system prune -af

pull:
	git pull origin main

deploy: down pull build up logs
	@echo "Deployment complete"

restart: down up logs
	@echo "Application reloaded"

refresh: down pull up logs
	@echo "Application reloaded"