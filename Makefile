.PHONY: dev test lint format build deploy

dev:
	docker compose up --build

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

build:
	docker build -t samfhir-api backend/

deploy: build
	docker tag samfhir-api us-docker.pkg.dev/samfhir-prod/samfhir-api/samfhir-api:latest
	docker push us-docker.pkg.dev/samfhir-prod/samfhir-api/samfhir-api:latest
	gcloud run deploy samfhir-api \
		--image us-docker.pkg.dev/samfhir-prod/samfhir-api/samfhir-api:latest \
		--region us-central1 \
		--platform managed
