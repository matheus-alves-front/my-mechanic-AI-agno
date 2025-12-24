.PHONY: help venv install install-dev run-api dev-api run-os dev-os dev-all stop docker-up docker-down ingest lint

# =========================
# Config
# =========================
VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
UVICORN ?= $(VENV)/bin/uvicorn

HOST ?= 0.0.0.0
API_PORT ?= 8080
AGENTOS_PORT ?= 7777

# Uvicorn app para sua API (FastAPI)
API_APP ?= app.main:app

# Módulo ASGI que o AgentOS vai tentar importar (agent_os.serve(app="my_os:app", ...))
AGENTOS_APP ?= my_os:app

# =========================
# UX
# =========================
help:
	@echo ""
	@echo "Targets:"
	@echo "  make venv         - cria o venv em .venv"
	@echo "  make install      - instala requirements.txt"
	@echo "  make dev-api      - sobe API (8080) com reload"
	@echo "  make run-api      - sobe API (8080) sem reload"
	@echo "  make dev-os       - sobe AgentOS (7777) com reload (Control Plane/Agent UI)"
	@echo "  make run-os       - sobe AgentOS (7777) sem reload"
	@echo "  make dev-all      - sobe API (8080) + AgentOS (7777) juntos"
	@echo "  make stop         - mata processos que estejam usando 8080/7777"
	@echo "  make docker-up    - sobe compose"
	@echo "  make docker-down  - derruba compose"
	@echo "  make ingest       - roda ingest no container (compose exec api)"
	@echo ""

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -U ruff

# =========================
# Run API (8080)
# =========================
run-api:
	HOST=$(HOST) PORT=$(API_PORT) $(PYTHON) -m app.main

dev-api:
	$(UVICORN) $(API_APP) --host $(HOST) --port $(API_PORT) --reload

# =========================
# Run AgentOS (7777)
# =========================
# Recomendado: use agent_os.serve(...) (porta 7777 é o padrão esperado por UI/Control Plane)
# A implementação do serve fica no seu código; este target apenas inicia o processo.
run-os:
	AGENTOS_PORT=$(AGENTOS_PORT) $(PYTHON) -m my_os

dev-os:
	AGENTOS_PORT=$(AGENTOS_PORT) $(PYTHON) -m my_os --reload

# =========================
# Run both (8080 + 7777)
# =========================
dev-all:
	@set -e; \
	echo "Starting API on :$(API_PORT) and AgentOS on :$(AGENTOS_PORT)"; \
	$(UVICORN) $(API_APP) --host $(HOST) --port $(API_PORT) --reload & \
	API_PID=$$!; \
	AGENTOS_PORT=$(AGENTOS_PORT) $(PYTHON) -m my_os --reload & \
	OS_PID=$$!; \
	trap "echo 'Stopping...'; kill $$API_PID $$OS_PID 2>/dev/null || true" INT TERM; \
	wait $$API_PID $$OS_PID

# =========================
# Kill ports (useful when Address already in use)
# =========================
stop:
	@echo "Killing processes on ports $(API_PORT) and $(AGENTOS_PORT) (if any)..."
	@fuser -k $(API_PORT)/tcp 2>/dev/null || true
	@fuser -k $(AGENTOS_PORT)/tcp 2>/dev/null || true
	@pkill -f "uvicorn $(API_APP)" 2>/dev/null || true
	@pkill -f "python -m my_os" 2>/dev/null || true
	@echo "Done."

# =========================
# Docker
# =========================
docker-up:
	sudo docker compose up -d --build

docker-down:
	sudo docker compose down -v

ingest:
	sudo docker compose exec api python /app/scripts/ingest_jsonl.py

lint:
	ruff check .
