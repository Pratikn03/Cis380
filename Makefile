.PHONY: help install test run streamlit train-all train-vision prod-check docker-build docker-up docker-up-prod docker-down

PY ?= python
PIP ?= $(PY) -m pip

help:
	@echo ""
	@echo "Sentifargo - Common Commands"
	@echo ""
	@echo "  make install        Install Python deps (requirements.txt)"
	@echo "  make test           Run pytest"
	@echo "  make run            Start FastAPI (uvicorn app.main:app --reload)"
	@echo "  make streamlit      Start Streamlit UI (app/streamlit_chatbot/app.py)"
	@echo "  make train-all      Train core models (scripts/train_all.py)"
	@echo "  make train-vision   Train vision stack (scripts/train_all_vision.py)"
	@echo "  make prod-check     Run production readiness checker"
	@echo "  make docker-build   Build Docker production image"
	@echo "  make docker-up      Docker Compose (dev) up --build"
	@echo "  make docker-up-prod Docker Compose (production profile) up -d"
	@echo "  make docker-down    Docker Compose down"
	@echo ""

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

streamlit:
	Sentifargo_BACKEND=$${Sentifargo_BACKEND:-http://localhost:8000} $(PY) -m streamlit run app/streamlit_chatbot/app.py

train-all:
	$(PY) scripts/train_all.py

train-vision:
	$(PY) scripts/train_all_vision.py

prod-check:
	$(PY) scripts/check_production.py

docker-build:
	docker build -f Dockerfile.production --target production -t Sentifargo:prod .

docker-up:
	docker compose up --build

docker-up-prod:
	docker compose -f docker-compose.production.yml --profile production up -d --build

docker-down:
	docker compose down
