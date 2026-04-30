.PHONY: help install test run dev dev-down api web scrub streamlit train-all train-vision train-fraud train-cyber train-behavior train-recommender train-brand train-video-temporal train-voice train-voice-ssl eval promote model-quality-gate prod-check docker-build docker-up docker-up-prod docker-down gateway-test gateway-run quality-fast quality-test quality-data quality-docs-fast quality-docs quality-all

ifneq ("$(wildcard .venv/bin/python)","")
PY ?= .venv/bin/python
else
PY ?= python3
endif
PIP ?= $(PY) -m pip
VOICE_EPOCHS ?= 50
VOICE_BATCH ?= 64
VOICE_RF_ESTIMATORS ?= 600
VOICE_RF_MAX_DEPTH ?= 32
VOICE_SSL_MODEL ?= microsoft/wavlm-base-plus
VOICE_SSL_OUTPUT ?= models/voice_emotion_ssl_6class
VOICE_SSL_EPOCHS ?= 50
VOICE_SSL_BATCH ?= 16
VOICE_SSL_DEVICE ?= auto
VOICE_SSL_MAX_STEPS ?= 0
VOICE_SSL_NUM_WORKERS ?= 2

help:
	@echo ""
	@echo "Sentifargo - Common Commands"
	@echo ""
	@echo "  make dev            Boot full local stack: postgres+redis (docker), API (:8000), web (:5173)"
	@echo "  make dev-down       Stop the local postgres+redis containers"
	@echo "  make api            Start only the FastAPI backend (APP_ENV=development)"
	@echo "  make web            Start only the Vite frontend"
	@echo "  make scrub          Remove macOS AppleDouble (._*) ghost files"
	@echo "  make install        Install Python deps (requirements.txt)"
	@echo "  make test           Run pytest"
	@echo "  make run            Start FastAPI (uvicorn app.main:app --reload)"
	@echo "  make streamlit      Start legacy Streamlit UI (app/streamlit_chatbot/app.py)"
	@echo "  make train-fraud    Train fraud model (DVC stage)"
	@echo "  make train-cyber    Train cyber model (DVC stage, full data)"
	@echo "  make train-behavior Train behavior model (DVC stage, full data)"
	@echo "  make train-recommender  Train recommender model (DVC stage)"
	@echo "  make train-brand    Train brand/logo detector (DVC stage, full data)"
	@echo "  make train-video-temporal Train video temporal model (full data)"
	@echo "  make train-voice    Prepare, train, and evaluate fast API-backed MFCC voice baseline"
	@echo "  make train-voice-ssl Prepare, fine-tune, and evaluate production SSL voice model"
	@echo "  make train-all      Train core models (scripts/train_all.py)"
	@echo "  make train-vision   Train vision stack (scripts/train_all_vision.py)"
	@echo "  make eval           Evaluate all trained models (DVC evaluate_all)"
	@echo "  make promote        Promote passing artifacts into artifacts/release"
	@echo "  make model-quality-gate Validate release manifest and promotion gates"
	@echo "  make rag-index      Build/rebuild DSA document index"
	@echo "  make rag-eval       Run DSA retrieval evaluation"
	@echo "  make rag-query      Query DSA index (QUERY=...)"
	@echo "  make prod-check     Run production readiness checker"
	@echo "  make docker-build   Build Docker production image"
	@echo "  make docker-up      Docker Compose (dev) up --build"
	@echo "  make docker-up-prod Docker Compose production stack up -d"
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

dev:
	bash scripts/dev.sh

dev-down:
	docker compose -f docker-compose.dev.yml down

api:
	APP_ENV=development $(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd ui-web/frontend && npm run dev

scrub:
	bash scripts/scrub_appledouble.sh

contract:
	APP_ENV=development AUTH_BYPASS=true $(PY) -m pytest -q tests/contract

e2e:
	APP_ENV=development AUTH_BYPASS=true $(PY) -m pytest -q -m e2e tests/e2e

load:
	@command -v k6 >/dev/null 2>&1 || { echo "k6 not installed — brew install k6 or see https://k6.io" >&2; exit 1; }
	BASE_URL=$${BASE_URL:-http://localhost:8000} k6 run tests/load/agent_run.js

agent-eval:
	APP_ENV=development PYTHONPATH=. $(PY) scripts/run_agent_eval.py --threshold 0.7

streamlit:
	Sentifargo_BACKEND=$${Sentifargo_BACKEND:-http://localhost:8000} $(PY) -m streamlit run app/streamlit_chatbot/app.py

train-fraud:
	PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro --single-item train_fraud_model

train-cyber:
	PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro --single-item train_cyber_model

train-behavior:
	PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro --single-item train_behavior_model

train-recommender:
	PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro --single-item train_recommender

train-brand:
	BRAND_SINGLE_CLASS=true $(PY) scripts/prepare_brand_data.py --single-class
	BRAND_EPOCHS=50 BRAND_BATCH=16 BRAND_FRACTION=1.0 BRAND_TRAIN_MAX_IMAGES=0 BRAND_VAL_MAX_IMAGES=0 BRAND_VAL=true BRAND_SINGLE_CLS=false COPYFILE_DISABLE=1 PATH="$(CURDIR)/.venv/bin:$$PATH" $(PY) -m dvc repro --single-item train_brand_model

train-video-temporal:
	PYTHONPATH=src $(PY) src/train/train_video_temporal.py --max-per-class 0 --max-frames 0

train-voice:
	$(PY) scripts/prepare_voice_from_audiowav.py --mode link
	$(PY) scripts/voice/build_emotion_manifest.py --data-root data/raw/voice --out data/raw/voice/manifest.csv
	$(PY) scripts/voice/split_manifest.py --manifest data/raw/voice/manifest.csv --out-dir data/raw/voice --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
	$(PY) scripts/voice/train_emotion_mfcc.py --train-manifest data/raw/voice/manifest.train.csv --val-manifest data/raw/voice/manifest.val.csv --output-model models/voice_emotion.pkl --epochs $(VOICE_EPOCHS) --batch-size $(VOICE_BATCH) --rf-estimators $(VOICE_RF_ESTIMATORS) --rf-max-depth $(VOICE_RF_MAX_DEPTH)
	$(PY) scripts/voice/eval_emotion_mfcc.py --model models/voice_emotion.pkl --test-manifest data/raw/voice/manifest.test.csv

train-voice-ssl:
	$(PY) scripts/prepare_voice_from_audiowav.py --mode link
	$(PY) scripts/voice/build_emotion_manifest.py --data-root data/raw/voice --out data/raw/voice/manifest.csv
	$(PY) scripts/voice/split_manifest.py --manifest data/raw/voice/manifest.csv --out-dir data/raw/voice --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
	$(PY) scripts/voice/train_emotion_ssl.py --train-manifest data/raw/voice/manifest.train.csv --val-manifest data/raw/voice/manifest.val.csv --model $(VOICE_SSL_MODEL) --output-dir $(VOICE_SSL_OUTPUT) --epochs $(VOICE_SSL_EPOCHS) --batch-size $(VOICE_SSL_BATCH) --device $(VOICE_SSL_DEVICE) --num-workers $(VOICE_SSL_NUM_WORKERS) --max-steps $(VOICE_SSL_MAX_STEPS)
	$(PY) scripts/voice/eval_emotion_ssl.py --model-dir $(VOICE_SSL_OUTPUT) --test-manifest data/raw/voice/manifest.test.csv --batch-size $(VOICE_SSL_BATCH) --num-workers $(VOICE_SSL_NUM_WORKERS)

eval:
	PYTHONPATH=src $(PY) -m uais.evaluation.evaluate_all

promote:
	$(PY) scripts/promote_model.py --all --promote-passing

model-quality-gate:
	PYTHONPATH=. $(PY) scripts/model_quality_gate.py

train-all:
	$(PY) scripts/train_all.py

train-vision:
	$(PY) scripts/train_all_vision.py

rag-index:
	$(PY) -m src.cli rag index --rebuild

rag-eval:
	PYTHONPATH=. $(PY) scripts/rag/evaluate_dsa.py

rag-query:
	$(PY) -m src.cli rag query "$(QUERY)"

prod-check:
	$(PY) scripts/check_production.py

docker-build:
	docker build -f Dockerfile.production --target production -t Sentifargo:prod .

docker-up:
	docker compose up --build

docker-up-prod:
	docker compose -f docker-compose.production.yml up -d --build

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
