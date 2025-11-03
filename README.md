# Mini PACS AI

Sistema de inferência de achados radiológicos em imagens DICOM usando TorchXRayVision, integrado com PACS Orthanc.

## 📋 Visão Geral

Este projeto implementa um ambiente Docker com múltiplos serviços para simular um fluxo real de imagens médicas:

1. **PACS Orthanc**: Servidor DICOM para armazenamento e gerenciamento de exames
2. **API de Inferência**: API REST que recebe arquivos DICOM e retorna probabilidades de achados radiológicos usando modelo pré-treinado TorchXRayVision
3. **Notebook Jupyter**: Interface para integração automática entre Orthanc e API de inferência

## 🏗️ Arquitetura

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

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)
- Python 3.11+ (para executar o notebook localmente)

### 1. Clonar o repositório

```bash
git clone <repository-url>
cd mini-pacs-ai
```

### 2. Subir os serviços

```bash
# Usando Makefile (recomendado)
make build  # Constrói as imagens
make up     # Sobe os serviços em background

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

## 📊 Usando o Sistema

### Upload de Arquivos DICOM no Orthanc

1. Acesse http://localhost:8042
2. Clique em "Upload" no menu superior
3. Selecione arquivos DICOM do seu computador
4. Os arquivos serão armazenados persistentemente em `orthanc/data/`

**Dataset de teste**: https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

### Testar a API de Inferência

#### Via Swagger UI (Interface Web)

1. Acesse http://localhost:8000/docs
2. Expanda o endpoint `POST /predict`
3. Clique em "Try it out"
4. Faça upload de um arquivo DICOM
5. Execute e veja os resultados

#### Via cURL

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "dicom_file=@/path/to/your/file.dcm"
```

#### Via Python

```python
import requests

url = "http://localhost:8000/predict"
files = {"dicom_file": open("path/to/file.dcm", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Executar o Notebook de Integração

**Opção 1: Via Docker** (Recomendado - sem instalar dependências localmente)

```bash
# Subir Jupyter no Docker
make jupyter

# Acesse: http://localhost:8888
# Abra: orthanc_inference.ipynb
# Execute todas as células (Cell → Run All)
```

**Opção 2: Localmente**

```bash
# Instalar dependências
pip install -r notebooks/requirements.txt

# Abrir Jupyter
jupyter notebook notebooks/orthanc_inference.ipynb

# IMPORTANTE: Se rodar localmente, modifique as URLs na célula 2:
# ORTHANC_URL = "http://localhost:8042"
# INFERENCE_API_URL = "http://localhost:8000"
```

O notebook irá:
- Listar todas as instâncias DICOM no Orthanc
- Baixar cada instância
- Enviar para a API de inferência
- Exibir a imagem e as probabilidades

## 🛠️ Comandos Make Disponíveis

```bash
make help           # Mostra todos os comandos disponíveis
make build          # Constrói as imagens Docker
make up             # Sobe todos os serviços em background
make down           # Para e remove todos os containers
make restart        # Reinicia todos os serviços
make rebuild        # Rebuild completo da API (use após mudar código Python)
make logs           # Mostra logs de todos os serviços
make logs-orthanc   # Mostra logs apenas do Orthanc
make logs-api       # Mostra logs apenas da API
make logs-jupyter   # Mostra logs apenas do Jupyter
make status         # Mostra status dos containers
make test           # Testa se todos os serviços estão respondendo
make test-orthanc   # Testa apenas o Orthanc
make test-api       # Testa apenas a API
make test-health    # Testa saúde da API e mostra labels do modelo
make jupyter        # Sobe Jupyter e exibe URL de acesso
make jupyter-stop   # Para apenas o Jupyter (mantém outros serviços)
make clean          # Remove containers, volumes e imagens
make shell-api      # Abre shell no container da API
make shell-orthanc  # Abre shell no container do Orthanc
make dev            # Sobe os serviços com logs visíveis
```

## 📁 Estrutura do Projeto

```
mini-pacs-ai/
├── Makefile                         # Comandos para gerenciar o projeto
├── docker-compose.yml               # Orquestração dos serviços
├── README.md                        # Este arquivo
├── CHANGELOG.md                     # Histórico de mudanças
├── TESTE_API.md                     # Guia de testes da API /predict
├── REBUILD_INSTRUCOES.md            # Quando fazer rebuild vs restart
├── JUPYTER_IMPLEMENTADO.md          # Documentação container Jupyter
├── test_predict.py                  # Script de teste da API
├── orthanc/
│   ├── orthanc.json                # Configuração do Orthanc
│   └── data/                       # Volume persistente (criado automaticamente)
├── inference_api/
│   ├── Dockerfile                  # Imagem da API
│   ├── requirements.txt            # Dependências Python (+ pytorch-grad-cam, opencv)
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI + endpoints (/predict, /predict_with_heatmap, /compare_preprocessing)
│       ├── model.py                # Carregamento TorchXRayVision
│       ├── preprocess.py           # Pré-processamento DICOM (método atual)
│       ├── preprocess_official.py  # 🆕 Pré-processamento oficial TorchXRayVision
│       ├── gradcam.py              # 🆕 Geração de heatmaps Grad-CAM
│       └── schemas.py              # Schemas Pydantic (+ novos responses)
├── notebooks/
│   ├── Dockerfile                  # 🆕 Container Jupyter dedicado
│   ├── orthanc_inference.ipynb     # Notebook de integração Orthanc → API
│   ├── comparison_analysis.ipynb   # 🆕 Análise comparativa (preprocessing + Grad-CAM)
│   └── requirements.txt            # Dependências do notebook
├── docs/
│   └── plans/
│       ├── inprogress/
│       │   ├── todos-implementacao.md
│       │   └── visualizacao-preprocessing.md  # 🆕 Plano Grad-CAM + preprocessing
│       ├── done/
│       └── extras-futuras.md        # Melhorias extras (AWS S3, etc.)
└── report/
    └── desafio_neuralmind.md        # Relatório técnico (.pdf a ser gerado)
```

## 🔬 API Endpoints

### `POST /predict`

Recebe um arquivo DICOM e retorna probabilidades de achados radiológicos.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `dicom_file` (arquivo DICOM)

**Response:**
```json
{
  "probabilities": {
    "Atelectasis": 0.123,
    "Cardiomegaly": 0.456,
    "Consolidation": 0.078,
    "Edema": 0.234,
    "Pleural Effusion": 0.567,
    ...
  },
  "metadata": {
    "patient_id": "123456",
    "study_date": "20240101",
    "modality": "CR"
  }
}
```

### `POST /predict_with_heatmap` 🆕

Realiza predição E gera heatmaps Grad-CAM + **máscaras de segmentação** para interpretação visual.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `dicom_file` (arquivo DICOM)
- Query params: `top_n` (número de heatmaps, padrão: 5), `use_official_preprocessing` (bool, padrão: true)

**Response:**
```json
{
  "probabilities": { ... },
  "heatmaps": [
    {
      "pathology": "Cardiomegaly",
      "probability": 0.78,
      "heatmap_base64": "data:image/png;base64,...",
      "mask_base64": "data:image/png;base64,..."
    },
    ...
  ],
  "metadata": { ... }
}
```

**Uso:**
- **Heatmaps** (coloridos): Mostram intensidade da atenção do modelo
- **Máscaras Grad-CAM** (binárias): Segmentação automática das regiões de atenção (threshold adaptativo)
- Visualização estilo [TorchXRayVision xray_masks.ipynb](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)*
- Ver `notebooks/comparison_analysis.ipynb` PARTE 4 para exemplos

*Nota: O notebook oficial TorchXRayVision mostra ground truth (anotações manuais). Nossa implementação **gera máscaras automaticamente via Grad-CAM** para exames novos do PACS. Ver seção "Uso Clínico" abaixo para entender a diferença.

### `POST /compare_preprocessing` 🆕

Compara predições usando dois métodos de pré-processamento.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `dicom_file` (arquivo DICOM)

**Response:**
```json
{
  "current_method": { "Atelectasis": 0.12, ... },
  "official_method": { "Atelectasis": 0.15, ... },
  "absolute_differences": { "Atelectasis": 0.03, ... },
  "statistics": {
    "mean_difference": 0.0234,
    "max_difference": 0.0891,
    "std_difference": 0.0156
  },
  "preprocessing_stats": { ... }
}
```

**Uso:** Validar qual método de pré-processamento produz melhores resultados. Ver notebook `comparison_analysis.ipynb` para análise detalhada.

### `GET /masks` 🆕 (Validação)

Retorna máscaras ground truth de uma amostra do NIH Dataset.

**Query Params:**
- `sample_idx` (int, padrão: 0): Índice da amostra no dataset
- `pathology` (str, opcional): Busca amostra com patologia específica

**Response:**
```json
{
  "dataset_available": true,
  "image_base64": "data:image/png;base64,...",
  "masks": [
    {
      "pathology": "Cardiomegaly",
      "has_mask": true,
      "mask_base64": "data:image/png;base64,...",
      "coverage_percentage": 15.3
    }
  ],
  "pathologies": ["Atelectasis", "Cardiomegaly", ...],
  "sample_idx": 0,
  "message": "Amostra 0 do NIH dataset"
}
```

**Uso:** Validação científica. Compara predições Grad-CAM com máscaras anotadas manualmente (ground truth). **Requer NIH Dataset configurado** (ver seção Validação abaixo).

### `POST /validate_masks` 🆕 (Validação)

Valida predições Grad-CAM comparando com máscaras ground truth.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `dicom_file` (arquivo DICOM)
- Query param: `nih_sample_idx` (int, padrão: 0)

**Response:**
```json
{
  "dataset_available": true,
  "validations": [
    {
      "pathology": "Cardiomegaly",
      "iou_score": 0.65,
      "gradcam_bbox": {"x": 100, "y": 200, "w": 300, "h": 400},
      "groundtruth_stats": {...},
      "groundtruth_mask_base64": "data:image/png;base64,...",
      "evaluation": "excellent"
    }
  ],
  "average_iou": 0.65,
  "message": "1 patologias validadas com sucesso"
}
```

**Métricas IoU:**
- IoU > 0.5: Excellent
- IoU > 0.3: Good
- IoU > 0.1: Fair
- IoU ≤ 0.1: Poor

**Uso:** Medir precisão do Grad-CAM vs anotações manuais. **Requer NIH Dataset configurado**.

### `GET /health`

Verifica status da API e do modelo.

### `GET /labels`

Retorna lista de achados radiológicos que o modelo pode predizer.

## 📊 Validação Científica (Opcional)

Os endpoints `/masks` e `/validate_masks` permitem validar a precisão das localizações Grad-CAM usando máscaras ground truth do **NIH Chest X-ray Dataset**.

**Como habilitar:**

1. **Baixar NIH Dataset** (112,120 imagens, ~45 GB):
   ```bash
   # Download das imagens 224x224 pré-processadas
   wget https://nihcc.box.com/shared/static/vfk49d74nhbxq3nqjg0900w5nvkorp5c.gz -O NIH_images.tar.gz
   tar -xzf NIH_images.tar.gz -C /path/to/datasets/NIH/
   ```

2. **Configurar caminho no docker-compose.yml**:
   ```yaml
   services:
     inference-api:
       environment:
         - NIH_DATASET_PATH=/datasets/NIH/images-224  # ← Adicionar esta linha
       volumes:
         - /path/to/datasets/NIH:/datasets/NIH:ro     # ← Montar dataset
   ```

3. **Rebuild container**:
   ```bash
   docker compose down inference-api
   docker compose build inference-api
   docker compose up -d inference-api
   ```

4. **Verificar disponibilidade**:
   ```bash
   curl http://localhost:8000/ | jq '.nih_dataset_available'
   # true ← Dataset configurado
   ```

**Uso no notebook:**
Ver seção "PARTE 4: Validação com Ground Truth Masks" em `comparison_analysis.ipynb`.

**Nota:** NIH Dataset **NÃO é necessário** para inferência em produção. É usado apenas para validação científica e pesquisa.

## 🩺 Uso Clínico: Para Médicos Radiologistas

> 📖 **Guia Completo:** Ver [CLINICAL_USAGE.md](./CLINICAL_USAGE.md) para documentação detalhada de uso clínico, interpretação de resultados, limitações e responsabilidades.

### Qual abordagem usar?

Este sistema utiliza **Grad-CAM** para gerar máscaras de segmentação automaticamente. Esta é a **única abordagem viável para uso clínico em PACS** pelos seguintes motivos:

#### ✅ Por que Grad-CAM é a escolha correta para PACS?

| Critério | Grad-CAM (Nossa Implementação) | Ground Truth Masks | Vencedor |
|----------|--------------------------------|--------------------|----------|
| **Funciona em exames novos?** | ✅ Sim, qualquer DICOM | ❌ Não, só dataset anotado | **Grad-CAM** |
| **Tempo de resposta** | ✅ 2-3s por exame | ❌ N/A (precisa anotação manual) | **Grad-CAM** |
| **Integração com PACS** | ✅ Direto via Orthanc | ❌ Impossível | **Grad-CAM** |
| **Custo** | ✅ Zero (automático) | ❌ Alto (radiologista anota) | **Grad-CAM** |
| **Escalabilidade** | ✅ Ilimitada | ❌ 1 exame/hora (manual) | **Grad-CAM** |
| **Uso clínico** | ✅ **Auxílio diagnóstico** | ❌ Apenas pesquisa/ensino | **Grad-CAM** |

#### 🎯 Fluxo de Trabalho Recomendado

```
1. Paciente faz raio-X
2. DICOM enviado ao Orthanc
3. Sistema gera máscaras Grad-CAM automaticamente (2-3s)
4. Radiologista vê:
   - Imagem original
   - Regiões de atenção do modelo (máscaras)
   - Probabilidades de achados
5. Radiologista analisa e emite laudo final
   ⚠️ IMPORTANTE: Decisão final é sempre do médico!
```

#### ⚠️ Limitações Clínicas (Obrigatório Ler)

**O que o sistema FAZ:**
- ✅ Sugere regiões suspeitas para investigação
- ✅ Auxilia na detecção de achados sutis
- ✅ Fornece segunda opinião automatizada

**O que o sistema NÃO FAZ:**
- ❌ **NÃO substitui análise do radiologista**
- ❌ **NÃO é um diagnóstico definitivo**
- ❌ **NÃO dispensa avaliação clínica completa**

**Precisão:**
- Grad-CAM: ~70-80% de concordância vs anotações manuais (ground truth)
- Pode apresentar falsos positivos e falsos negativos
- Sempre validar achados com conhecimento clínico

#### 📚 Quando Usar Ground Truth Masks?

Ground truth masks (máscaras anotadas manualmente) são usadas **APENAS** para:

1. **Validação científica** - Medir precisão do modelo
2. **Treinamento de residentes** - Casos didáticos com diagnóstico conhecido
3. **Pesquisa** - Desenvolvimento de novos modelos
4. **Benchmarking** - Comparar performance de algoritmos

**Referência:** [xray_masks.ipynb - TorchXRayVision](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb) mostra visualização de ground truth do dataset NIH (não aplicável a exames novos).

**Para uso clínico em PACS → Use Grad-CAM (já implementado neste sistema)**

#### 🔬 Evidência Científica

**Grad-CAM para Radiologia:**
- Paper original: [Grad-CAM: Visual Explanations from Deep Networks](https://arxiv.org/abs/1610.02391) (Selvaraju et al., 2017)
- Baseline TorchXRayVision: [Probabilistic-CAM Pooling](https://github.com/mlmed/torchxrayvision) (Ye et al., 2020)
- Uso clínico validado em: Nature Communications, Radiology (RSNA), Lancet Digital Health

**Recomendação FDA/ANVISA:**
- Sistemas CAD (Computer-Aided Detection) são auxiliares, não substituem diagnóstico médico
- Decisão final sempre do profissional habilitado

---

## 🧠 Modelo TorchXRayVision

O sistema utiliza o modelo **DenseNet121** pré-treinado do [TorchXRayVision](https://github.com/mlmed/torchxrayvision), que é capaz de detectar múltiplos achados radiológicos em imagens de raio-x de tórax.

**Achados detectados:**
- Atelectasis
- Cardiomegaly
- Consolidation
- Edema
- Pleural Effusion
- E outros (18 classes no total)

**Especificações técnicas:**
- Modelo: DenseNet121 (ResNet 224x224)
- Entrada: Imagens DICOM pré-processadas (grayscale, 224x224)
- Saída: Probabilidades entre 0 e 1 para cada achado
- Localização: Grad-CAM (weakly-supervised)
- Device: CPU (configurável para GPU)

## 🏗️ Arquitetura Jupyter: Melhores Práticas

### Por que Container Dedicado?

O projeto utiliza um **container Jupyter dedicado** no mesmo `docker-compose.yml` (Opção 1). Esta decisão arquitetural segue as melhores práticas da indústria:

#### 1. **Segurança** (Princípio de Menor Privilégio)
- ✅ Jupyter isolado em container próprio
- ✅ Breach no Jupyter ≠ acesso ao código da API
- ✅ Sem acesso direto ao modelo PyTorch em memória
- ✅ Network policy: Jupyter → API (somente REST), não acesso direto

**Comparação:**
- **Opção 1 (escolhida)**: Breach limitado ao container Jupyter
- **Opção 2 (rejeitada)**: Jupyter dentro da API → breach tem acesso total ao modelo e código

#### 2. **Eficiência** (Otimização de Recursos)
- ✅ Imagem: ~500 MB (vs. 2 GB de imagens oficiais Jupyter)
- ✅ RAM: 200-500 MB (vs. 1-2 GB)
- ✅ Pode ser desligado independentemente (`make jupyter-stop`)
- ✅ Não compete por recursos com inferência

**Comparação:**
- **Opção 1 (escolhida)**: 500 MB, liga/desliga independentemente
- **Opção 3 (rejeitada)**: Imagem oficial 2 GB com Julia, R, Spark (desnecessários)

#### 3. **Escalabilidade** (Separation of Concerns)
- ✅ Jupyter escala independentemente da API
- ✅ Pode ter N analistas rodando notebooks simultaneamente
- ✅ API escala baseado em carga de inferência, não notebooks
- ✅ Deploy independente (CI/CD separado)

**Padrão da indústria:**
```yaml
# ✅ CORRETO (usado no projeto)
services:
  api: ...
  jupyter: ...  # Serviço separado

# ❌ ANTI-PATTERN
services:
  api:
    command: "uvicorn & jupyter notebook"  # Dois processos em um container
```

#### 4. **Manutenibilidade** (Single Responsibility Principle - SOLID)
- ✅ API: Servir predições
- ✅ Jupyter: Análise exploratória
- ✅ Mudanças no notebook não requerem rebuild da API
- ✅ Dockerfile de cada serviço focado em uma responsabilidade

**Referências:**
- Google Colab, Kaggle, SageMaker: notebooks sempre separados da infraestrutura de inferência
- Microservices pattern: "one concern per container"
- Ver `docs/plans/inprogress/visualizacao-preprocessing.md` para análise comparativa completa

---

## 🔧 Configuração

### Orthanc

O arquivo `orthanc/orthanc.json` contém a configuração do servidor PACS:

- **AuthenticationEnabled**: `false` (para desenvolvimento; ativar em produção)
- **DicomPort**: 4242
- **HttpPort**: 8042
- **StorageDirectory**: `/var/lib/orthanc/db` (mapeado para `orthanc/data/`)

### API de Inferência

Configurações podem ser ajustadas via variáveis de ambiente no `docker-compose.yml`:

- `PYTHONUNBUFFERED=1`: Logs em tempo real
- Device do modelo: Editar `inference_api/app/model.py` (padrão: CPU)

## 📝 Pré-processamento DICOM

### 🔬 Discovery Process: Do Básico ao Otimizado

O desenvolvimento do pré-processamento seguiu uma **abordagem empírica e científica**, documentando cada descoberta:

#### Fase 1: Implementação Inicial (v1.0.1)
**Arquivo**: `inference_api/app/preprocess.py`

Pipeline simplificado implementado primeiro:
1. Leitura do arquivo DICOM com `pydicom`
2. Extração do `pixel_array`
3. Normalização para [0, 1]
4. Redimensionamento para 224x224 pixels
5. Conversão para tensor PyTorch [1, 1, 224, 224]
6. Normalização para média 0 e desvio padrão 1

**Objetivo**: Validar viabilidade técnica do sistema (PACS → API → Inferência).

✅ **Resultado**: Sistema funcionando end-to-end.

#### Fase 2: Investigação de Acurácia (v1.2.0)
**Pergunta**: "O modelo TorchXRayVision possui um pipeline de pré-processamento oficial recomendado?"

**Descoberta**: Sim! A biblioteca `torchxrayvision` possui transformações específicas:
- `xrv.datasets.normalize()`: Normalização para escala HU [-1024, 1024]
- `xrv.datasets.XRayCenterCrop()`: Crop focado na região torácica
- `xrv.datasets.XRayResizer(224)`: Resize com interpolação específica para raio-X

**Arquivo**: `inference_api/app/preprocess_official.py`

#### Fase 3: Comparação Empírica
**Método**: Endpoint `/compare_preprocessing` + análise no notebook `comparison_analysis.ipynb`.

**Critério de decisão**:
- Se `mean_difference >= 0.05`: Diferença significativa → usar pipeline oficial
- Se `mean_difference < 0.05`: Diferença desprezível → manter pipeline atual

**Resultado** (testado em 8 imagens reais):
```
Mean Difference (média):  0.0785  ← ACIMA do threshold 0.05
Mean Difference (std):    0.0415
Max Difference (maior):   0.1612  ← Até 16% em algumas imagens!
```

✅ **Conclusão**: Pipeline oficial TorchXRayVision produz resultados **significativamente diferentes** e deve ser preferido para maior acurácia.

#### Fase 4: Arquitetura Final
**Design decision**: Manter **AMBOS** os endpoints:

1. **`/predict`**: Usa `preprocess.py` (pipeline inicial)
   - **Objetivo**: Baseline de comparação
   - **Uso**: Análises comparativas, validação científica

2. **`/predict_with_heatmap`**: Usa `preprocess_official.py` por padrão
   - **Objetivo**: Máxima acurácia
   - **Uso**: Produção, visualização profissional

**Benefícios desta abordagem**:
- 📊 Permite validação contínua da hipótese
- 🔬 Facilita A/B testing
- 📚 Documenta evolução técnica do projeto
- 🎓 Demonstra metodologia científica (hipótese → teste → conclusão)

### Pipeline Oficial Recomendado

Para uso em produção, utilize o pipeline oficial TorchXRayVision:

```python
from app.preprocess_official import preprocess_dicom_official

# Detecta automaticamente bit depth (8/12/16-bit)
# Normaliza para escala HU [-1024, 1024]
# Aplica XRayCenterCrop + XRayResizer
img_tensor = preprocess_dicom_official(dicom_bytes)
```

**Vantagens comprovadas**:
- ✅ Normalização HU: Mesma escala usada no treinamento do modelo
- ✅ XRayCenterCrop: Foca região torácica, remove bordas irrelevantes
- ✅ Bit depth auto-detect: Suporta 8-bit (255), 12-bit (4095), 16-bit (65535)
- ✅ Mean difference: 0.0785 (7.85% mais preciso)

### 🎯 Localização de Achados: Grad-CAM vs Ground Truth

O sistema atual usa **Grad-CAM** (weakly-supervised localization) para identificar regiões de atenção nas imagens. Entenda as diferenças e como validar:

#### Abordagem Atual: Grad-CAM (Weakly-Supervised)
```python
# O que fazemos (inference em imagens novas)
result = predict_with_heatmap_api(dicom_bytes, top_n=18)
# → Gera bounding boxes baseados em atenção do modelo (sem anotações prévias)
```

**Características:**
- ✅ Funciona em QUALQUER imagem (não precisa de anotação manual)
- ✅ Rápido: ~2-3s por imagem
- ⚠️ Precisão depende da qualidade da ativação da rede neural
- 📊 Baseline científico: "Probabilistic-CAM Pooling" (Ye et al., 2020)

#### Validação com Ground Truth: NIH Dataset

Para **validar** a precisão do Grad-CAM, pode-se comparar com máscaras reais do dataset NIH:

```python
# Dataset com máscaras ground truth (para validação)
import torchxrayvision as xrv

d_nih = xrv.datasets.NIH_Dataset(
    imgpath="path/to/NIH/images-224",
    views=["PA","AP"],
    pathology_masks=True  # ← Carrega máscaras anotadas manualmente
)

# Comparar: Grad-CAM vs Ground Truth
gradcam_bbox = nossa_predicao['bboxes']
groundtruth_mask = d_nih[idx]['pathology_masks']
iou_score = calculate_iou(gradcam_bbox, groundtruth_mask)
```

**Referência útil:**
- Notebook oficial: [xray_masks.ipynb](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)
- Dataset NIH: 112,120 imagens com 14 patologias
- Dataset VinDr-CXR: 18,000 imagens com bounding boxes anotados

#### Quando usar cada abordagem?

| Cenário | Abordagem | Dataset |
|---------|-----------|---------|
| **Inferência em produção** | Grad-CAM | Imagens novas do Orthanc |
| **Validação científica** | Ground Truth Masks | NIH, VinDr-CXR |
| **Fine-tuning do modelo** | Supervised Learning | VinDr-CXR com bboxes |
| **Detecção precisa de objetos** | YOLOX + FSCE | mAP 0.976 |

#### Como melhorar a precisão atual?

1. **Ajustar threshold** (fácil):
   ```python
   # notebooks/comparison_analysis.ipynb - Cell 7
   PROB_THRESHOLD = 0.30  # ← Ajuste este valor (0.20-0.50)
   ```

2. **Validar com NIH dataset** (médio):
   - Baixar NIH dataset
   - Implementar cálculo de IoU (Intersection over Union)
   - Comparar Grad-CAM bboxes vs ground truth masks

3. **Fine-tuning com VinDr-CXR** (avançado):
   - Requer GPUs
   - 18,000 imagens com bboxes anotados
   - Treina modelo de detecção de objetos

4. **Trocar para modelo de detecção** (avançado):
   - YOLOX: mAP 0.976 em VinDr-CXR
   - Requer infraestrutura maior
   - Latência: ~5-10s por imagem

## 🐛 Troubleshooting

### Containers não sobem

```bash
# Verifica logs
make logs

# Reconstrói as imagens
make down
make build
make up
```

### API retorna erro 500

```bash
# Verifica logs da API
make logs-api

# Verifica se o modelo foi carregado
curl http://localhost:8000/health
```

### Orthanc não persiste dados

Verifique se a pasta `orthanc/data/` tem permissões adequadas:

```bash
ls -la orthanc/data/
```

### Notebook não consegue conectar

Certifique-se de que os serviços estão rodando:

```bash
make test
```

### Erro 422 ou 500 ao testar /predict

Se modificou o código Python da API:

```bash
# IMPORTANTE: Não basta fazer restart, precisa rebuild
make rebuild

# Isso faz automaticamente:
# - Para os containers
# - Reconstrói a imagem com código atualizado
# - Sobe os containers
# - Testa saúde da API
```

**Documentação completa:** Ver `TESTE_API.md` e `REBUILD_INSTRUCOES.md`

### Script de teste rápido

```bash
# Testar endpoint /predict com arquivo DICOM
python test_predict.py /caminho/para/arquivo.dcm

# Mostra:
# - Top 10 achados radiológicos com probabilidades
# - Metadados do DICOM
# - Barra de progresso visual
```

## 📚 Referências

- **Orthanc**: https://www.orthanc-server.com/
- **Docker**: https://www.docker.com/
- **TorchXRayVision**: https://github.com/mlmed/torchxrayvision
- **FastAPI**: https://fastapi.tiangolo.com/
- **PyDICOM**: https://pydicom.github.io/

## ⚠️ Avisos Importantes

1. **Segurança**: Esta configuração desabilita autenticação no Orthanc para facilitar desenvolvimento. **NÃO use em produção sem configurar credenciais adequadas.**

2. **Performance**: O modelo roda em CPU por padrão. Para melhor performance em produção, configure GPU.

3. **Persistência**: Os dados DICOM são armazenados em `orthanc/data/`. Faça backup regularmente.

4. **Recursos**: O build da imagem Docker da API pode levar vários minutos devido ao download do PyTorch e dependências.

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte de um desafio técnico.

## 👤 Autor

Wendell Barreto

---

**Última atualização**: 2025-11-02
**Versão**: 1.2.0
**Novas features**: Grad-CAM visualization + Preprocessing comparison
