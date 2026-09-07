.PHONY: up build down logs shell migrate makemigrations superuser test

up:
	docker compose up

build:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f main-app

shell:
	docker compose exec main-app uv run python manage.py shell

migrate:
	docker compose exec main-app uv run python manage.py migrate

makemigrations:
	docker compose exec main-app uv run python manage.py makemigrations

superuser:
	docker compose exec main-app uv run python manage.py createsuperuser

test:
	docker compose exec main-app uv run python manage.py test