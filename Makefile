.PHONY: dev test lint format build deploy frontend-dev frontend-build frontend-lint frontend-test test-all lint-all

dev:
	docker compose up --build

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

build:
	docker build -t samfhir-api -f backend/Dockerfile .

deploy: build
	docker tag samfhir-api australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	docker push australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	gcloud run deploy samfhir-api \
		--image australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest \
		--region australia-southeast1 \
		--platform managed

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test

test-all: test frontend-test

lint-all: lint frontend-lint
