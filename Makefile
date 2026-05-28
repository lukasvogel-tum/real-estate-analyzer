SHELL := cmd.exe
.SHELLFLAGS := /c

PYTHON := .venv\Scripts\python.exe
NPM := npm.cmd

# Start everything
.PHONY: run backend frontend

run:
	start "Backend" cmd /k "cd backend && ..\$(PYTHON) -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
	start "Frontend" cmd /k "cd frontend && $(NPM) run dev"

backend:
	cd backend && ..\$(PYTHON) -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && $(NPM) run dev

# Dependencies
.PHONY: install install-backend install-frontend

install: install-backend install-frontend

install-backend:
	$(PYTHON) -m pip install -r requirements.txt

install-frontend:
	cd frontend && $(NPM) install

# Neo4j (optional)
.PHONY: graph graph-stop

graph:
	docker compose up -d

graph-stop:
	docker compose down

# Quality checks
.PHONY: lint build check

lint:
	cd frontend && $(NPM) run lint

build:
	cd frontend && $(NPM) run build

check:
	$(PYTHON) -m compileall backend
	cd frontend && $(NPM) run lint
