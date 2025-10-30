.PHONY: help build up down restart logs logs-orthanc logs-api clean test-api status

# Variáveis
COMPOSE = docker compose
ORTHANC_URL = http://localhost:8042
API_URL = http://localhost:8000

help: ## Mostra esta mensagem de ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Constrói as imagens Docker
	$(COMPOSE) build

up: ## Sobe todos os serviços em background
	$(COMPOSE) up -d

down: ## Para e remove todos os containers
	$(COMPOSE) down

restart: down up ## Reinicia todos os serviços

logs: ## Mostra logs de todos os serviços
	$(COMPOSE) logs -f

logs-orthanc: ## Mostra logs do Orthanc
	$(COMPOSE) logs -f orthanc

logs-api: ## Mostra logs da API de inferência
	$(COMPOSE) logs -f inference-api

status: ## Mostra status dos containers
	$(COMPOSE) ps

clean: ## Remove containers, volumes e imagens
	$(COMPOSE) down -v --rmi all

test-api: ## Testa se a API está respondendo
	@echo "Testando API de inferência..."
	@curl -s $(API_URL)/docs > /dev/null && echo "✓ API está respondendo em $(API_URL)/docs" || echo "✗ API não está respondendo"

test-orthanc: ## Testa se o Orthanc está respondendo
	@echo "Testando Orthanc..."
	@curl -s $(ORTHANC_URL)/app/explorer.html > /dev/null && echo "✓ Orthanc está respondendo em $(ORTHANC_URL)" || echo "✗ Orthanc não está respondendo"

test: test-orthanc test-api ## Testa se todos os serviços estão respondendo

shell-api: ## Abre shell no container da API
	$(COMPOSE) exec inference-api /bin/bash

shell-orthanc: ## Abre shell no container do Orthanc
	$(COMPOSE) exec orthanc /bin/bash

dev: ## Sobe os serviços e mostra os logs
	$(COMPOSE) up
