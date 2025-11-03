# 🔄 Quando e Como Fazer Rebuild

## ⚠️ IMPORTANTE: Restart vs Rebuild

### `docker compose restart`
- ✅ **Usa:** Quando mudou apenas **configuração** (docker-compose.yml, orthanc.json)
- ❌ **NÃO usa:** Quando mudou **código Python** (.py)
- **Motivo:** Não recopia arquivos do código-fonte para o container

### `docker compose build`
- ✅ **Usa:** Quando mudou **código Python** (app/*.py, requirements.txt)
- ✅ **Usa:** Quando mudou **Dockerfile**
- **Motivo:** Reconstrói a imagem com os arquivos atualizados

---

## 📋 Quando Fazer Rebuild

### Sempre que modificar:
- ✅ `inference_api/app/main.py`
- ✅ `inference_api/app/model.py`
- ✅ `inference_api/app/preprocess.py`
- ✅ `inference_api/app/schemas.py`
- ✅ `inference_api/requirements.txt`
- ✅ `inference_api/Dockerfile`

### Quando apenas restart é suficiente:
- ✅ `docker-compose.yml` (variáveis de ambiente, portas)
- ✅ `orthanc/orthanc.json` (configuração do Orthanc)

---

## 🛠️ Comandos Corretos

### Rebuild Completo (Recomendado)
```bash
# 1. Para e remove containers
docker compose down

# 2. Reconstrói a imagem da API
docker compose build inference-api

# 3. Sobe os containers
docker compose up -d

# 4. Aguarda modelo carregar (~10 segundos)
sleep 10

# 5. Verifica saúde
curl http://localhost:8000/health
```

### Usando Makefile (Atalho)
```bash
make down
make build
make up
make test
```

---

## 🚨 Problemas Comuns

### "Mudei o código mas o erro continua"
**Causa:** Fez apenas `restart` em vez de `build`

**Solução:**
```bash
docker compose down
docker compose build inference-api
docker compose up -d
```

### "Build está muito lento"
**Causa:** Docker está refazendo toda a instalação de dependências

**Otimização:** As camadas do Dockerfile estão em cache. Se `requirements.txt` não mudou, apenas a camada `COPY app ./app` será reconstruída (~1 segundo).

### "Erro: address already in use"
**Causa:** Containers antigos ainda rodando

**Solução:**
```bash
# Força parada de todos os containers
docker compose down --remove-orphans

# Lista containers rodando
docker ps

# Se ainda houver, mata manualmente
docker stop $(docker ps -q)
```

---

## 📊 Verificação Pós-Rebuild

### Checklist:
```bash
# 1. Containers rodando?
docker compose ps

# 2. API saudável?
curl http://localhost:8000/health

# 3. Modelo carregado? (18 labels)
curl http://localhost:8000/labels | jq '.count'

# 4. Logs sem erro?
docker compose logs inference-api | tail -20
```

Todos devem retornar sucesso ✅

---

## 🎯 Workflow Recomendado

### Durante Desenvolvimento:
```bash
# Editar código Python
vim inference_api/app/main.py

# Rebuild rápido
docker compose build inference-api

# Restart apenas do serviço alterado
docker compose up -d inference-api

# Ver logs em tempo real
docker compose logs -f inference-api
```

### Para Produção:
```bash
# Rebuild completo sem cache
docker compose build --no-cache

# Sobe com restart automático
docker compose up -d --force-recreate
```

---

**Criado em:** 2025-11-02
**Contexto:** Correção de bugs 422 e 500 no endpoint /predict
