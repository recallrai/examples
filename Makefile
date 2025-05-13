.PHONY: build up down logs shell clean git_pull deploy restart refresh

all: deploy

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -af

git_pull:
	git pull origin main

deploy: down git_pull build up logs
	@echo "Deployment complete"

restart: down up logs
	@echo "Application reloaded"

refresh: down git_pull up logs
	@echo "Application reloaded"
