.PHONY: help install test run streamlit train-all train-vision prod-check docker-build docker-up docker-up-prod docker-down gateway-test gateway-run quality-fast quality-test quality-data quality-docs-fast quality-docs quality-all

ifneq ("$(wildcard .venv/bin/python)","")
PY ?= .venv/bin/python
else
PY ?= python3
endif
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
	@echo "  make rag-index      Build/rebuild DSA document index"
	@echo "  make rag-eval       Run DSA retrieval evaluation"
	@echo "  make rag-query      Query DSA index (QUERY=...)"
	@echo "  make prod-check     Run production readiness checker"
	@echo "  make docker-build   Build Docker production image"
	@echo "  make docker-up      Docker Compose (dev) up --build"
	@echo "  make docker-up-prod Docker Compose (production profile) up -d"
	@echo "  make docker-down    Docker Compose down"
	@echo "  make gateway-test   Run Kotlin gateway tests with Java 21"
	@echo "  make gateway-run    Run Kotlin GraphQL gateway (./gradlew bootRun)"
	@echo "  make quality-fast   Quick quality gates (lint + targeted tests)"
	@echo "  make quality-test   Full module test+coverage gates"
	@echo "  make quality-data   Data cleaning + validation gates"
	@echo "  make quality-docs-fast Docs schema and metadata checks"
	@echo "  make quality-docs   Full docs quality checks + lint + scorecard"
	@echo "  make quality-all    Run all quality gates"
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

rag-index:
	$(PY) -m src.cli rag index --rebuild

rag-eval:
	$(PY) scripts/rag/evaluate_dsa.py

rag-query:
	$(PY) -m src.cli rag query "$(QUERY)"

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

gateway-test:
	cd services/gateway-kotlin && \
	export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home && \
	export PATH="/opt/homebrew/opt/openjdk@21/bin:$$PATH" && \
	export GRADLE_USER_HOME=$$(pwd)/.gradle-user-home && \
	./gradlew clean test

gateway-run:
	cd services/gateway-kotlin && \
	export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home && \
	export PATH="/opt/homebrew/opt/openjdk@21/bin:$$PATH" && \
	export GRADLE_USER_HOME=$$(pwd)/.gradle-user-home && \
	./gradlew bootRun

quality-fast:
	$(PY) scripts/quality/quality_thresholds.py check --waivers quality/waivers.yml
	$(PY) -m ruff check app src scripts tests
	$(PY) -m pytest -q tests/test_data_quality_scripts.py tests/test_auth_password.py
	cd services/gateway-kotlin && \
	export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home && \
	export PATH="/opt/homebrew/opt/openjdk@21/bin:$$PATH" && \
	export GRADLE_USER_HOME=$$(pwd)/.gradle-user-home && \
	./gradlew test
	cd ui-web/next && npm run test:ci
	$(PY) scripts/quality/run_with_timeout.py --timeout 180 --name legacy-frontend-tests -- \
		bash -lc "cd ui-web/frontend && npm run test:ci:stable"

quality-test:
	$(PY) scripts/quality/quality_thresholds.py check --waivers quality/waivers.yml
	@PY_API_THRESHOLD=$$($(PY) scripts/quality/quality_thresholds.py threshold --module python_api --waivers quality/waivers.yml); \
	RAG_EMBED_BACKEND=hashing HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 $(PY) -m pytest -q tests --cov=app/api/v1 --cov-report=term-missing --cov-report=xml:reports/coverage_python_api.xml --cov-fail-under=$$PY_API_THRESHOLD
	@PY_SCRIPTS_THRESHOLD=$$($(PY) scripts/quality/quality_thresholds.py threshold --module python_quality_scripts --waivers quality/waivers.yml); \
	$(PY) -m pytest -q tests/test_data_quality_scripts.py --cov=scripts.data --cov=scripts.training_data_audit --cov-report=term-missing --cov-report=xml:reports/coverage_python_quality_scripts.xml --cov-fail-under=$$PY_SCRIPTS_THRESHOLD
	@GATEWAY_THRESHOLD=$$($(PY) scripts/quality/quality_thresholds.py threshold --module gateway_kotlin --waivers quality/waivers.yml); \
	cd services/gateway-kotlin && \
	export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home && \
	export PATH="/opt/homebrew/opt/openjdk@21/bin:$$PATH" && \
	export GRADLE_USER_HOME=$$(pwd)/.gradle-user-home && \
	./gradlew clean test jacocoTestReport jacocoTestCoverageVerification -PcoverageMinimum=$$GATEWAY_THRESHOLD
	@NEXT_THRESHOLD=$$($(PY) scripts/quality/quality_thresholds.py threshold --module next_frontend --waivers quality/waivers.yml); \
	cd ui-web/next && NEXT_THRESHOLD=$$NEXT_THRESHOLD npm run test:coverage
	@LEGACY_THRESHOLD=$$($(PY) scripts/quality/quality_thresholds.py threshold --module legacy_frontend --waivers quality/waivers.yml); \
	$(PY) scripts/quality/run_with_timeout.py --timeout 300 --name legacy-frontend-coverage -- \
		bash -lc "cd ui-web/frontend && LEGACY_THRESHOLD=$$LEGACY_THRESHOLD npm run test:coverage:stable"

quality-data:
	$(PY) scripts/data/run_quality_gates.py

quality-docs-fast:
	$(PY) scripts/quality/docs_quality_check.py --mode fast --threshold 85 --manifest docs/docs-manifest.yml

quality-docs:
	$(PY) scripts/quality/docs_quality_check.py --mode full --threshold 95 --manifest docs/docs-manifest.yml
	npx --yes markdownlint-cli@0.40.0 README.md docs/**/*.md ui-web/**/*.md services/**/*.md scripts/**/*.md data/**/*.md benchmarks/**/*.md infra/terraform/**/*.md --config .markdownlint.yml
	@if command -v vale >/dev/null 2>&1; then \
		vale README.md docs ui-web services scripts data benchmarks infra/terraform ; \
	elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		docker run --rm -v "$$(pwd):/work" -w /work jdkato/vale:latest --config=.vale.ini README.md docs ui-web services scripts data benchmarks infra/terraform ; \
	else \
		echo "Skipping Vale: no local vale binary and Docker daemon unavailable."; \
	fi

quality-all:
	$(MAKE) quality-fast
	$(MAKE) quality-data
	$(MAKE) quality-test
	$(MAKE) quality-docs
