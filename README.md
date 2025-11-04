# Mini PACS AI

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0+

Sistema de inferência de achados radiológicos em imagens DICOM usando TorchXRayVision, integrado com PACS Orthanc.

---

## 📋 Visão Geral

Este projeto implementa um ambiente Docker com múltiplos serviços para simular um fluxo real de imagens médicas:

1. **PACS Orthanc**: Servidor DICOM para armazenamento e gerenciamento de exames
2. **API de Inferência**: API REST que recebe arquivos DICOM e retorna probabilidades de achados radiológicos usando modelo pré-treinado TorchXRayVision
3. **Jupyter Notebook**: Interface para integração automática entre Orthanc e API de inferência

### 🏗️ Arquitetura

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  Orthanc PACS   │─────▶│  Inference API   │◀─────│  Jupyter        │
│  (Port 8042)    │      │  (Port 8000)     │      │  Notebook       │
│                 │      │  TorchXRayVision │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                        │
         │                        │
    DICOM Files            Deep Learning Model
    (Persistent)           (CPU-based)
```

---

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)
- Python 3.11+ (para executar notebooks localmente)

### 1. Clonar o repositório

```bash
git clone <repository-url>
cd mini-pacs-ai
```

### 2. Subir os serviços

```bash
# Usando Makefile (recomendado)
make build  # Constrói as imagens
make up     # Sube os serviços em background

# Ou usando docker compose diretamente
docker compose build
docker compose up -d
```

### 3. Verificar status

```bash
make status  # Verifica status dos containers
make test    # Testa se os serviços estão respondendo
```

### 4. Acessar as interfaces

- **Orthanc Web UI**: http://localhost:8042
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Jupyter Notebook**: http://localhost:8888 (executar `make jupyter` para obter URL com token)

---

## 📚 Documentação Completa

### 🎓 **Aprenda do Básico ao Avançado**

**[📖 ACADEMY.md](./docs/ACADEMY.md)** - Trilha de aprendizado completa
- Módulo 1: Fundamentos PACS e DICOM
- Módulo 2: IA em Radiologia (TorchXRayVision, Deep Learning)
- Módulo 3: Explicabilidade (Grad-CAM, Máscaras)
- Módulo 4: Arquitetura da Aplicação
- Módulo 5: Implementação Técnica
- Módulo 6: Discovery e Insights de Desenvolvimento
- Módulo 7: Uso Clínico e Regulamentação (FDA/ANVISA)
- **1.200+ linhas** de conteúdo educacional

### 📖 **Navegação Rápida**

**[📖 DOCS_INDEX.md](./docs/DOCS_INDEX.md)** - Índice completo da documentação
- Navegação por persona (médico, desenvolvedor, pesquisador)
- Fluxos de leitura recomendados
- Estrutura de arquivos do projeto

### 🔧 **Guias Técnicos**

- **[API.md](./docs/API.md)** - Documentação completa dos endpoints
  - POST /predict (método oficial como padrão)
  - POST /generate_masks ⭐ (recomendado - máscaras Grad-CAM)
  - POST /predict_with_heatmap (legacy)
  - POST /compare_preprocessing (pesquisa científica)
  - GET /masks, POST /validate_masks (validação científica)
  - Exemplos Python, cURL, troubleshooting

- **[ORTHANC.md](./docs/ORTHANC.md)** - Configuração e uso do Orthanc
  - Arquitetura do PACS
  - REST API completa
  - Upload de DICOMs
  - Persistência e backup
  - Troubleshooting

- **[MODELO_IA.md](./docs/MODELO_IA.md)** - TorchXRayVision DenseNet121
  - Arquitetura do modelo
  - 18 achados detectados
  - Performance e métricas
  - Transfer Learning
  - Grad-CAM (explicabilidade)

- **[PREPROCESSAMENTO.md](./docs/PREPROCESSAMENTO.md)** - Pré-processamento DICOM
  - DICOM vs imagens comuns
  - Pesquisa: Método oficial vs anterior (~11% de diferença)
  - Decisão: Método oficial TorchXRayVision adotado como padrão
  - Discovery process
  - Recomendações técnicas

- **[TESTE_API.md](./docs/TESTE_API.md)** - Como testar a API
  - Métodos de teste (Swagger UI, cURL, Python)
  - Troubleshooting completo
  - Exemplos práticos

- **[GUIA_NOTEBOOK.md](./docs/GUIA_NOTEBOOK.md)** - Usando o notebook
  - orthanc_analysis.ipynb (análise completa - 4 seções)
  - Seção Pesquisa: escolha do método oficial
  - Visualização de máscaras Grad-CAM

- **[REBUILD_INSTRUCOES.md](./docs/REBUILD_INSTRUCOES.md)** - Quando fazer rebuild
  - Restart vs Rebuild
  - Quando e como rebuildar
  - Troubleshooting de build

### 🩺 **Uso Clínico**

**[CLINICAL_USAGE.md](./docs/CLINICAL_USAGE.md)** - Guia completo para médicos radiologistas
- Grad-CAM vs Ground Truth (qual usar?)
- Fluxo de trabalho recomendado
- Limitações clínicas (obrigatório ler!)
- Responsabilidades do médico
- Evidência científica
- Regulamentação FDA/ANVISA

**Resumo:**
- ✅ Grad-CAM: Para exames novos do PACS (produção)
- ❌ Ground Truth: Apenas para validação científica/pesquisa
- ⚠️ Sistema é auxílio diagnóstico, **NÃO substitui radiologista**

### 📝 **Histórico**

**[CHANGELOG.md](./CHANGELOG.md)** - Histórico de versões
- v1.3.0+: Método oficial padrão + Endpoint /generate_masks + Notebook unificado
- v1.3.0: Máscaras de segmentação Grad-CAM + Validação
- v1.2.0: Grad-CAM + Pré-processamento
- v1.0.1: Bug fixes
- v1.0.0: Versão inicial

---

## 🛠️ Comandos Make Disponíveis

```bash
make help           # Mostra todos os comandos disponíveis
make build          # Constrói as imagens Docker
make up             # Sube todos os serviços em background
make down           # Para e remove todos os containers
make restart        # Reinicia todos os serviços
make rebuild        # Rebuild completo da API (use após mudar código Python)
make logs           # Mostra logs de todos os serviços
make logs-orthanc   # Mostra logs apenas do Orthanc
make logs-api       # Mostra logs apenas da API
make logs-jupyter   # Mostra logs apenas do Jupyter
make status         # Mostra status dos containers
make test           # Testa se todos os serviços estão respondendo
make test-health    # Testa saúde da API e mostra labels do modelo
make jupyter        # Sobe Jupyter e exibe URL de acesso
make clean          # Remove containers, volumes e imagens
make shell-api      # Abre shell no container da API
make dev            # Sobe os serviços com logs visíveis
```

---

## 📁 Estrutura do Projeto

```
mini-pacs-ai/
├── README.md                        # Este arquivo
├── CHANGELOG.md                     # Histórico de mudanças
├── Makefile                         # Comandos para gerenciar o projeto
├── docker-compose.yml               # Orquestração dos serviços
│
├── docs/                            # 📚 Documentação completa
│   ├── DOCS_INDEX.md               # Índice de navegação
│   ├── ACADEMY.md                  # Trilha de aprendizado completa
│   ├── API.md                      # Documentação da API
│   ├── ORTHANC.md                  # Configuração Orthanc
│   ├── MODELO_IA.md                # TorchXRayVision
│   ├── PREPROCESSAMENTO.md         # Pré-processamento DICOM
│   ├── CLINICAL_USAGE.md           # Guia clínico para médicos
│   ├── TESTE_API.md                # Como testar
│   ├── GUIA_NOTEBOOK.md            # Usando notebooks
│   ├── REBUILD_INSTRUCOES.md       # Rebuild vs restart
│   ├── JUPYTER_IMPLEMENTADO.md     # Arquitetura Jupyter
│   └── plans/                      # Planos e TODOs
│
├── orthanc/
│   ├── orthanc.json                # Configuração do Orthanc
│   └── data/                       # Volume persistente (criado automaticamente)
│
├── inference_api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI + endpoints
│       ├── model.py                # TorchXRayVision
│       ├── preprocess.py           # Pré-processamento atual
│       ├── preprocess_official.py  # Pré-processamento oficial
│       ├── gradcam.py              # Grad-CAM + máscaras
│       ├── nih_dataset.py          # Validação (opcional)
│       └── schemas.py              # Pydantic models
│
├── notebooks/
│   ├── Dockerfile
│   ├── orthanc_analysis.ipynb      # Análise completa (4 seções)
│   └── requirements.txt
│
├── tests/                          # Scripts de teste
│   ├── README.md                   # Documentação de testes
│   ├── test_predict.py             # Teste /predict
│   ├── test_generate_masks.py      # Teste /generate_masks ⭐
│   └── test_compare_preprocessing.py # Teste comparação métodos
│
└── report/
    └── desafio_neuralmind.md       # Relatório técnico
```

---

## 🧠 Modelo TorchXRayVision

**Modelo:** DenseNet121 pré-treinado
**Dataset de treino:** NIH + CheXpert + MIMIC-CXR (224.316 imagens)
**Achados detectados:** 18 classes
**Performance:** AUC-ROC médio 0.84

**Achados:**
Atelectasis, Cardiomegaly, Consolidation, Edema, Pleural Effusion, Pneumonia, Pneumothorax, Enlarged Cardiomediastinum, Lung Lesion, Lung Opacity, Fracture, Support Devices, No Finding, Pleural Other, Infiltration, Nodule, Mass, Emphysema

**Ver documentação completa:** [docs/MODELO_IA.md](./docs/MODELO_IA.md)

---

## 📊 API Endpoints

### Principais

- **POST /predict** - Predição básica (método oficial padrão)
- **POST /generate_masks** ⭐ - Máscaras Grad-CAM (recomendado)
- **POST /predict_with_heatmap** - Predição + máscaras (legacy)
- **POST /compare_preprocessing** - Comparar métodos (pesquisa)
- **GET /health** - Status da API
- **GET /labels** - Lista de achados detectáveis

### Validação Científica (Opcional)

- **GET /masks** - Máscaras ground truth (NIH Dataset)
- **POST /validate_masks** - Validar Grad-CAM vs ground truth (IoU)

**Ver documentação completa:** [docs/API.md](./docs/API.md)

---

## 📊 Usando o Sistema

### 1. Upload de DICOMs no Orthanc

1. Acesse http://localhost:8042
2. Clique em "Upload"
3. Selecione arquivos DICOM
4. Dados persistem em `orthanc/data/`

**Dataset de teste**: https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

**Ver guia completo:** [docs/ORTHANC.md](./docs/ORTHANC.md)

### 2. Testar API

#### Via Swagger UI

http://localhost:8000/docs → POST /generate_masks → Try it out

#### Via Python

```python
import requests

# Endpoint recomendado (v1.3.0+)
url = "http://localhost:8000/generate_masks"
files = {"dicom_file": open("exam.dcm", "rb")}
params = {"top_n": 3}  # Número de máscaras
response = requests.post(url, files=files, params=params)
result = response.json()

print("Achados detectados:")
for achado, prob in result['probabilities'].items():
    if prob > 0.3:
        print(f"  {achado}: {prob:.2%}")
```

**Ver exemplos completos:** [docs/TESTE_API.md](./docs/TESTE_API.md)

### 3. Notebooks Jupyter

```bash
# Via Docker (recomendado)
make jupyter
# Acesse URL exibida: http://localhost:8888/...?token=...

# Abrir: orthanc_analysis.ipynb
# Executar: Cell → Run All
```

**Notebook unificado (v1.3.0+):**
- `orthanc_analysis.ipynb` - Análise completa (4 seções):
  - Seção 1: Setup e configuração
  - Seção 2: Pesquisa (escolha do método oficial) ⭐
  - Seção 3: Inferência com método oficial
  - Seção 4: Máscaras de segmentação Grad-CAM

**Ver guia completo:** [docs/GUIA_NOTEBOOK.md](./docs/GUIA_NOTEBOOK.md)

---

## 🩺 Uso Clínico

> ⚠️ **IMPORTANTE:** Sistema é auxílio diagnóstico, **NÃO substitui análise do radiologista**

### Fluxo Recomendado

```
1. Paciente faz raio-X
2. DICOM enviado ao Orthanc
3. Sistema gera máscaras Grad-CAM (2-3s)
4. Radiologista analisa:
   - Imagem original
   - Regiões de atenção (máscaras)
   - Probabilidades
5. Radiologista emite laudo final
```

### Grad-CAM vs Ground Truth

| Aspecto | Grad-CAM | Ground Truth |
|---------|----------|--------------|
| Funciona em exames novos? | ✅ Sim | ❌ Não (só dataset anotado) |
| Tempo | 2-3s | N/A (manual) |
| Uso clínico | ✅ Produção PACS | ❌ Apenas pesquisa |
| Precisão | ~70-80% vs ground truth | 100% (por definição) |

**Recomendação:** Use Grad-CAM para **todos os exames do PACS** (produção)

**Ground Truth:** Apenas para validação científica/pesquisa

**Ver guia completo:** [docs/CLINICAL_USAGE.md](./docs/CLINICAL_USAGE.md)

---

## 🐛 Troubleshooting

### Containers não sobem

```bash
make logs      # Ver logs
make rebuild   # Rebuildar tudo
```

### API retorna erro 500

```bash
make logs-api              # Ver logs da API
curl http://localhost:8000/health  # Verificar saúde
make rebuild               # Se modelo não carregou
```

### Mudei código Python, mas não funciona

```bash
make rebuild  # IMPORTANTE: Precisa rebuild, restart NÃO basta!
```

**Ver troubleshooting completo:**
- API: [docs/TESTE_API.md](./docs/TESTE_API.md)
- Orthanc: [docs/ORTHANC.md](./docs/ORTHANC.md)
- Rebuild: [docs/REBUILD_INSTRUCOES.md](./docs/REBUILD_INSTRUCOES.md)

---

## 📚 Referências

**Tecnologias:**
- **Orthanc**: https://www.orthanc-server.com/
- **TorchXRayVision**: https://github.com/mlmed/torchxrayvision
- **FastAPI**: https://fastapi.tiangolo.com/
- **Docker**: https://www.docker.com/
- **PyDICOM**: https://pydicom.github.io/

**Papers:**
- Grad-CAM: https://arxiv.org/abs/1610.02391
- CheXNet: https://arxiv.org/abs/1711.05225
- DenseNet: https://arxiv.org/abs/1608.06993

**Datasets:**
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- Desafio (DICOM teste): https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

---

## ⚠️ Avisos Importantes

1. **Segurança**: Autenticação desabilitada no Orthanc (apenas dev). **Habilitar em produção.**
2. **Performance**: Modelo roda em CPU. Para produção, configure GPU.
3. **Persistência**: Dados em `orthanc/data/`. Faça backup regularmente.
4. **Uso Clínico**: Sistema é **auxílio diagnóstico**. Decisão final sempre do médico.

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte de um desafio técnico.

---

## 👤 Autor

**Wendell Barreto**
📧 wendellbarreto@gmail.com

---

## 🎯 Próximos Passos

### Para começar:
1. **Leia:** [docs/ACADEMY.md](./docs/ACADEMY.md) - Aprenda do básico ao avançado
2. **Instale:** `make build && make up`
3. **Teste:** http://localhost:8000/docs
4. **Explore:** Notebooks Jupyter

### Para uso clínico:
1. **Leia:** [docs/CLINICAL_USAGE.md](./docs/CLINICAL_USAGE.md) - Guia obrigatório
2. **Teste:** Upload DICOM no Orthanc
3. **Visualize:** `orthanc_analysis.ipynb` Seção 4 (máscaras)
4. **Valide:** Análise com radiologista

### Para desenvolvimento:
1. **Entenda:** [docs/DOCS_INDEX.md](./docs/DOCS_INDEX.md) - Navegação completa
2. **API:** [docs/API.md](./docs/API.md) - Endpoints detalhados
3. **Modelo:** [docs/MODELO_IA.md](./docs/MODELO_IA.md) - TorchXRayVision
4. **Código:** `inference_api/app/` - Implementação

---

**Última atualização**: 2025-11-04
**Versão**: 1.3.0+
**Features**: Método oficial padrão + Endpoint /generate_masks + Notebook unificado + Documentação completa
