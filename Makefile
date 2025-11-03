.PHONY: help build up down restart rebuild logs logs-orthanc logs-api logs-jupyter clean test-api test-health status jupyter jupyter-stop

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

rebuild: ## Rebuild completo da API (use após mudar código Python)
	@echo "🔄 Parando containers..."
	$(COMPOSE) down
	@echo "🔨 Reconstruindo imagem da API..."
	$(COMPOSE) build inference-api
	@echo "🚀 Subindo containers..."
	$(COMPOSE) up -d
	@echo "⏳ Aguardando modelo carregar (10s)..."
	@sleep 10
	@echo "✅ Testando saúde da API..."
	@curl -s $(API_URL)/health | grep -q "healthy" && echo "✓ API está saudável!" || echo "✗ API com problemas"

logs: ## Mostra logs de todos os serviços
	$(COMPOSE) logs -f

logs-orthanc: ## Mostra logs do Orthanc
	$(COMPOSE) logs -f orthanc

logs-api: ## Mostra logs da API de inferência
	$(COMPOSE) logs -f inference-api

logs-jupyter: ## Mostra logs do Jupyter
	$(COMPOSE) logs -f jupyter

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

test-health: ## Testa saúde da API e mostra labels do modelo
	@echo "🏥 Verificando saúde da API..."
	@curl -s $(API_URL)/health | jq
	@echo "\n📊 Labels detectáveis pelo modelo:"
	@curl -s $(API_URL)/labels | jq '.count'

shell-api: ## Abre shell no container da API
	$(COMPOSE) exec inference-api /bin/bash

shell-orthanc: ## Abre shell no container do Orthanc
	$(COMPOSE) exec orthanc /bin/bash

jupyter: ## Sobe Jupyter e exibe URL de acesso
	@echo "🚀 Subindo Jupyter Notebook..."
	$(COMPOSE) up -d jupyter
	@echo "⏳ Aguardando Jupyter iniciar..."
	@sleep 5
	@echo ""
	@echo "✅ Jupyter está rodando!"
	@echo "📓 Acesse: http://localhost:8888"
	@echo "📁 Notebooks em: /workspace"
	@echo ""
	@echo "Para ver logs: make logs-jupyter"

jupyter-stop: ## Para apenas o Jupyter (mantém outros serviços)
	$(COMPOSE) stop jupyter
	@echo "🛑 Jupyter parado (outros serviços continuam rodando)"

dev: ## Sobe os serviços e mostra os logs
	$(COMPOSE) up
