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
	docker tag samfhir-api australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	docker push australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	gcloud run deploy samfhir-api \
		--image australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest \
		--region australia-southeast1 \
		--platform managed
