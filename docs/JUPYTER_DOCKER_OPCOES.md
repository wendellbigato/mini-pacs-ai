# 🐳 Jupyter no Docker - Comparação de Opções

**Cenário:** Rodar notebook sem instalar nada localmente, aproveitando infraestrutura Docker.

---

## 📊 Comparação Rápida

| Critério | Opção 1<br>Jupyter Dedicado | Opção 2<br>Jupyter na API | Opção 3<br>Imagem Oficial |
|----------|---------------------------|--------------------------|-------------------------|
| **Complexidade** | ⭐⭐⭐ Média | ⭐ Muito Baixa | ⭐⭐ Baixa |
| **Isolamento** | ✅ Excelente | ⚠️ Compartilha com API | ✅ Bom |
| **Tamanho** | ~500 MB | +50 MB na API | ~2 GB |
| **Build Time** | ~2 min | ~3 min | ~30 seg |
| **Manutenção** | Fácil | Simples | Muito Fácil |
| **Produção** | ✅ Sim | ❌ Não | ⚠️ Depende |
| **Recomendado** | ✅ **SIM** | Apenas teste | Se tempo curto |

---

## 🎯 OPÇÃO 1: Jupyter Dedicado (RECOMENDADO)

### ✅ Quando Usar
- Projeto profissional/demonstração
- Quer isolar serviços
- Vai commitar configuração Docker
- Precisa de reprodutibilidade

### 📁 Arquivos Criados
```
notebooks/
├── Dockerfile              ← Criado!
├── requirements.txt        ← Já existe
└── orthanc_analysis.ipynb  ← v1.3.0+ (unificado)
```

### 🚀 Como Usar

#### 1. Modificar docker-compose.yml
```bash
# Copie o conteúdo de docker-compose.opcao1.yml
# E cole no docker-compose.yml existente
# OU use:
mv docker-compose.yml docker-compose.yml.bak
mv docker-compose.opcao1.yml docker-compose.yml
```

#### 2. Modificar Notebook (Célula 2)
```python
# Trocar:
ORTHANC_URL = "http://localhost:8042"
INFERENCE_API_URL = "http://localhost:8000"

# Por:
ORTHANC_URL = "http://orthanc:8042"              # Nome do serviço
INFERENCE_API_URL = "http://inference-api:8000"  # Nome do serviço
```

#### 3. Subir Tudo
```bash
docker compose up -d

# Aguardar ~30 segundos (build primeira vez)
```

#### 4. Acessar Jupyter
```
http://localhost:8888
```

**SEM SENHA/TOKEN!** Acesso direto.

### 📝 Makefile Command (Opcional)
```makefile
jupyter: ## Sobe apenas Jupyter (requer outros serviços ativos)
	docker compose up -d jupyter
	@echo "Jupyter disponível em: http://localhost:8888"

jupyter-logs: ## Ver logs do Jupyter
	docker compose logs -f jupyter
```

---

## ⚡ OPÇÃO 2: Jupyter na API

### ✅ Quando Usar
- Teste rápido, ambiente temporário
- Não quer adicionar novo container
- Já tem API rodando

### ❌ Não Use Para
- Produção
- Demo profissional
- Commit no repositório

### 🚀 Como Usar

#### 1. Adicionar Jupyter ao requirements.txt da API
```bash
echo "jupyter==1.1.1" >> inference_api/requirements.txt
```

#### 2. Adicionar porta e volume no docker-compose.yml
```yaml
inference-api:
  ports:
    - "8000:8000"
    - "8888:8888"  # ← Adicionar
  volumes:
    - ./notebooks:/notebooks  # ← Adicionar
```

#### 3. Rebuild API
```bash
docker compose down
docker compose build inference-api
docker compose up -d
```

#### 4. Rodar Jupyter Manualmente
```bash
docker exec -it inference-api jupyter notebook \
  --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
  --notebook-dir=/notebooks \
  --NotebookApp.token='' --NotebookApp.password=''
```

#### 5. Acessar
```
http://localhost:8888
```

### 🔄 URLs no Notebook
```python
ORTHANC_URL = "http://orthanc:8042"              # Nome do serviço
INFERENCE_API_URL = "http://localhost:8000"      # Localhost (mesma rede)
```

---

## 🌐 OPÇÃO 3: Imagem Oficial Jupyter

### ✅ Quando Usar
- Quer começar AGORA (sem build)
- Não se importa com tamanho da imagem
- Quer JupyterLab moderno

### 🚀 Como Usar

#### 1. Usar docker-compose.opcao3.yml
```bash
mv docker-compose.yml docker-compose.yml.bak
mv docker-compose.opcao3.yml docker-compose.yml
```

#### 2. Subir Serviços
```bash
docker compose up -d

# Jupyter estará disponível em ~10 segundos
```

#### 3. Acessar
```
http://localhost:8888
```

#### 4. Navegar
```
work/ → orthanc_analysis.ipynb
```

### 🔄 URLs no Notebook
```python
ORTHANC_URL = "http://orthanc:8042"
INFERENCE_API_URL = "http://inference-api:8000"
```

### ⚠️ Observações
- Instala `pydicom` e `requests` a cada restart
- Para persistir: criar Dockerfile derivado da imagem oficial
- Diretório padrão: `/home/jovyan/work`

---

## 🎓 Diferença: localhost vs Nome do Serviço

### Dentro do Docker (Opção 1, 2, 3)
```python
# ✅ CORRETO - Usa nome do serviço
ORTHANC_URL = "http://orthanc:8042"
INFERENCE_API_URL = "http://inference-api:8000"

# ❌ ERRADO - Não funciona dentro do container
ORTHANC_URL = "http://localhost:8042"
```

**Por quê?**
- `localhost` dentro do container Jupyter = próprio container
- Orthanc e API estão em **outros** containers
- Docker resolve nomes de serviços via DNS interno

### Fora do Docker (Local)
```python
# ✅ CORRETO - Usa localhost
ORTHANC_URL = "http://localhost:8042"
INFERENCE_API_URL = "http://localhost:8000"

# ❌ ERRADO - Nome do serviço não existe fora do Docker
ORTHANC_URL = "http://orthanc:8042"
```

---

## 🔥 Teste Rápido de Cada Opção

### Opção 1
```bash
# 1. Já criou Dockerfile? ✅
# 2. Modificar docker-compose.yml
# 3. Modificar célula 2 do notebook
docker compose up -d
# → http://localhost:8888
```

### Opção 2
```bash
echo "jupyter==1.1.1" >> inference_api/requirements.txt
# Modificar docker-compose.yml (portas + volumes)
docker compose build inference-api && docker compose up -d
docker exec -it inference-api jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/notebooks --NotebookApp.token='' --NotebookApp.password=''
# → http://localhost:8888
```

### Opção 3
```bash
docker compose -f docker-compose.opcao3.yml up -d
# Aguardar 10s
# → http://localhost:8888 → work/
```

---

## 🏆 Recomendação Final

### Para ESTE projeto (mini-pacs-ai)
**OPÇÃO 1** - Jupyter Dedicado

**Razões:**
1. ✅ Projeto educacional/demonstração → precisa ser profissional
2. ✅ Vai commitar no GitHub → reprodutibilidade importante
3. ✅ Documentação já criada → Dockerfile pronto
4. ✅ Isolamento de serviços → boa prática DevOps
5. ✅ URLs internas consistentes → `http://serviço:porta`

### Se tiver pressa
**OPÇÃO 3** - Imagem Oficial (30 segundos para rodar)

---

## 📂 Arquivos de Suporte Criados

```
mini-pacs-ai/
├── notebooks/
│   ├── Dockerfile                      ← Opção 1
│   ├── orthanc_inference.docker.py     ← URLs internas
│   └── requirements.txt                ← Já existia
├── docker-compose.opcao1.yml           ← Opção 1 (completo)
├── docker-compose.opcao2.yml           ← Opção 2 (completo)
├── docker-compose.opcao3.yml           ← Opção 3 (completo)
└── JUPYTER_DOCKER_OPCOES.md            ← Este arquivo
```

---

## 🎬 Próximos Passos

**Escolha uma opção e me confirme!**

Depois posso:
1. ✅ Aplicar no docker-compose.yml principal
2. ✅ Atualizar Makefile com comandos Jupyter
3. ✅ Modificar notebook com URLs internas
4. ✅ Atualizar README.md e documentação
5. ✅ Testar end-to-end

**Qual opção você quer implementar? 1, 2 ou 3?**
