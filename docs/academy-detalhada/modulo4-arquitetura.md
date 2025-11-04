# Módulo 4: Arquitetura da Aplicação

> **[← Voltar para Academia Mini PACS AI](../ACADEMY.md)**

**Duração estimada:** 2-3 horas
**Pré-requisitos:** Módulo 1 (PACS/DICOM), Módulo 2 (IA) e Módulo 3 (Explicabilidade)

---

## 4.1 Visão Geral do Sistema

### Diagrama de Arquitetura

```
┌──────────────────────────────────────────────────────────┐
│                     MINI PACS AI                         │
│                                                          │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐│
│  │            │      │            │      │            ││
│  │  ORTHANC   │ ───→ │ INFERENCE  │ ───→ │  JUPYTER   ││
│  │   (PACS)   │      │    API     │      │  NOTEBOOK  ││
│  │            │      │  (FastAPI) │      │            ││
│  └────────────┘      └────────────┘      └────────────┘│
│       ↓                    ↓                    ↓       │
│   Port 8042           Port 8000            Port 8888    │
│   REST API           /predict             Analysis      │
│   DICOM Storage      /generate_masks ⭐                  │
│                      /compare_preprocessing             │
└──────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

**Upload de DICOM:**
```
Médico/Técnico
    ↓ (upload via UI)
Orthanc REST API (/instances)
    ↓ (armazena)
SQLite + Filesystem
```

**Predição:**
```
Jupyter/Cliente
    ↓ (GET /instances/{id}/file)
Orthanc
    ↓ (retorna DICOM bytes)
Jupyter
    ↓ (POST /generate_masks)
Inference API
    ↓ (pré-processa)
DICOM → Tensor
    ↓ (executa)
TorchXRayVision Model
    ↓ (Grad-CAM)
Heatmaps + Máscaras
    ↓ (retorna JSON)
Jupyter
    ↓ (visualiza)
Matplotlib plots
```

### Containers Docker

**docker-compose.yml:**

```yaml
services:
  orthanc:
    image: orthancteam/orthanc:latest
    ports: ["8042:8042", "4242:4242"]
    volumes:
      - ./orthanc/data:/var/lib/orthanc/db
      - ./orthanc/orthanc.json:/etc/orthanc/orthanc.json:ro
    restart: unless-stopped

  inference-api:
    build: ./inference_api
    ports: ["8000:8000"]
    depends_on: [orthanc]
    restart: unless-stopped

  jupyter:
    build: ./jupyter
    ports: ["8888:8888"]
    volumes:
      - ./notebooks:/home/jovyan/work
    depends_on: [orthanc, inference-api]
```

**Rede:**
- Todos no mesmo network `default`
- Comunicação interna: `http://orthanc:8042`, `http://inference-api:8000`
- Acesso externo: `http://localhost:8042`, `http://localhost:8000`

## 4.2 Container Orthanc (PACS)

### Responsabilidades

1. ✅ Armazenar DICOMs enviados via upload
2. ✅ Indexar metadados em SQLite
3. ✅ Servir REST API para query/retrieve
4. ✅ Prover Web UI para visualização manual

### Estrutura de Dados

**SQLite (`orthanc/data/index`):**
```sql
-- Tabela: Resources
CREATE TABLE Resources (
    internalId INTEGER PRIMARY KEY,
    resourceType INTEGER,
    publicId TEXT UNIQUE,
    parentId INTEGER
);

-- Tipos:
-- 0 = Patient
-- 1 = Study
-- 2 = Series
-- 3 = Instance

-- Exemplo de query:
SELECT publicId FROM Resources
WHERE resourceType = 3;  -- Todas instâncias
```

**Filesystem (`orthanc/data/`):**
```
orthanc/data/
├── index           # SQLite database
└── [UUID]/         # Pastas por instância
    ├── [UUID]      # DICOM file
    └── [UUID].json # Metadata cache
```

### Endpoints Usados no Projeto

```bash
# Listar instâncias
GET /instances
→ ["abc-123", "def-456", ...]

# Metadados de uma instância
GET /instances/abc-123/tags
→ {"0010,0010": {"Value": "João Silva"}, ...}

# Download DICOM
GET /instances/abc-123/file
→ Binary DICOM file

# Preview PNG
GET /instances/abc-123/preview
→ PNG image

# Estatísticas do sistema
GET /statistics
→ {"TotalDiskSize": "1.2 GB", "CountInstances": 42, ...}
```

### Persistência

**Volume Docker:**
```yaml
volumes:
  - ./orthanc/data:/var/lib/orthanc/db
```

**O que é salvo:**
- ✅ DICOMs completos
- ✅ Índice SQLite
- ✅ Cache de metadados

**Backup:**
```bash
# Parar Orthanc
docker compose stop orthanc

# Copiar dados
tar -czf orthanc-backup-$(date +%Y%m%d).tar.gz orthanc/data/

# Reiniciar
docker compose start orthanc
```

## 4.3 API de Inferência (FastAPI)

### Estrutura de Código

```
inference_api/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py          # FastAPI app + endpoints
    ├── model.py         # Carregamento do modelo
    ├── preprocess.py    # DICOM → tensor
    ├── gradcam.py       # Grad-CAM + máscaras
    ├── nih_dataset.py   # (Opcional) Validação
    └── schemas.py       # Pydantic models
```

### Endpoints

**1. GET /health**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

**2. POST /predict**
```python
@app.post("/predict")
async def predict(dicom_file: UploadFile = File(...)):
    # 1. Ler DICOM
    dicom_bytes = await dicom_file.read()

    # 2. Pré-processar
    tensor, metadata = preprocess_dicom(dicom_bytes)

    # 3. Predição
    probabilities = model_predict(tensor)

    # 4. Retornar
    return {
        "probabilities": probabilities,
        "metadata": metadata
    }
```

**3. POST /generate_masks** ⭐ (Recomendado v1.3.0+)
```python
@app.post("/generate_masks")
async def generate_masks(
    dicom_file: UploadFile,
    top_n: int = 3,  # Padrão: 3 máscaras (mais focado)
    use_official_preprocessing: bool = True
):
    # 1-3. Igual /predict
    # 4. Gerar Grad-CAM para top N achados
    heatmaps = []
    for pathology, prob in top_predictions:
        heatmap = generate_gradcam(model, tensor, pathology_idx)
        mask = generate_binary_mask_from_heatmap(heatmap, threshold)
        heatmaps.append({
            "pathology": pathology,
            "probability": prob,
            "heatmap_base64": encode_heatmap_to_base64(heatmap),
            "mask_base64": encode_mask_to_base64(mask)
        })

    return {
        "probabilities": probabilities,
        "heatmaps": heatmaps,
        "metadata": metadata
    }
```

### Carregamento do Modelo

**app/model.py:**

```python
import torchxrayvision as xrv
import torch

# Singleton pattern (carrega apenas 1 vez)
_model = None

def get_model():
    global _model
    if _model is None:
        print("Carregando modelo TorchXRayVision...")
        _model = xrv.models.DenseNet(weights="densenet121-res224-all")
        _model.eval()
        print(f"Modelo carregado. Patologias: {_model.pathologies}")
    return _model

def model_predict(tensor: torch.Tensor) -> dict:
    model = get_model()
    with torch.no_grad():
        outputs = model(tensor)
    probs = torch.sigmoid(outputs).cpu().numpy()[0]
    return dict(zip(model.pathologies, probs.tolist()))
```

**Otimizações:**
- ✅ Modelo carregado apenas 1 vez (startup)
- ✅ `eval()` mode (dropout desativado)
- ✅ `torch.no_grad()` (sem gradientes, mais rápido)
- ✅ CPU por padrão (GPU opcional)

### Pré-Processamento

**app/preprocess.py:**

```python
def preprocess_dicom(dicom_bytes: bytes, use_official: bool = True):
    """
    DICOM → Tensor [1, 1, 224, 224]

    Etapas:
    1. Ler DICOM com pydicom
    2. Extrair pixel_array
    3. Normalizar (oficial TorchXRayVision ou custom)
    4. Redimensionar para 224x224
    5. Converter para tensor PyTorch
    """
    # 1. Ler DICOM
    dcm = pydicom.dcmread(BytesIO(dicom_bytes))

    # 2. Pixel array
    img = dcm.pixel_array.astype(np.float32)

    # 3. Normalizar
    if use_official:
        # Método oficial TorchXRayVision
        img = xrv.datasets.normalize(img, maxval=255, reshape=True)
    else:
        # Método alternativo (0-1, resize, normalização)
        img = img / img.max()
        img = transform.resize(img, (224, 224))
        img = (img - img.mean()) / (img.std() + 1e-8)
        img = img[None, ...]  # [1, H, W]

    # 4. Tensor
    tensor = torch.from_numpy(img).unsqueeze(0)  # [1, 1, H, W]

    # 5. Metadados
    metadata = extract_metadata(dcm)

    return tensor, metadata
```

**Por que 2 métodos?**
- **Oficial:** Recomendado (treinado assim)
- **Custom:** Comparação científica (análise no notebook)

## 4.4 Jupyter para Análise

### Por que container dedicado?

**Decisão de arquitetura:**
> "Container Jupyter separado garante isolamento, reprodutibilidade e facilita colaboração."

**Alternativas consideradas:**
1. ❌ Jupyter local (fora do Docker) - dependências conflitantes
2. ❌ Jupyter dentro do container da API - acoplamento, rebuild frequente
3. ✅ Container Jupyter dedicado - melhor opção

**Vantagens:**
- ✅ Ambiente isolado
- ✅ Notebooks versionados (Git)
- ✅ Fácil compartilhar (apenas `docker compose up`)
- ✅ Não precisa rebuild ao modificar notebooks

### Dockerfile

**jupyter/Dockerfile:**

```dockerfile
FROM jupyter/scipy-notebook:latest

# Instalar dependências adicionais
RUN pip install --no-cache-dir \
    requests \
    pydicom \
    Pillow

# Expor porta
EXPOSE 8888

# Comando padrão (já vem com jupyter/scipy-notebook)
CMD ["start-notebook.sh"]
```

### Volume Montado

```yaml
jupyter:
  volumes:
    - ./notebooks:/home/jovyan/work
```

**Vantagem:**
- Editar notebooks localmente (VS Code, Jupyter Desktop)
- Mudanças refletidas instantaneamente no container
- Sem necessidade de rebuild

### Notebook Unificado (v1.3.0+)

**orthanc_analysis.ipynb** (Análise Completa)
- **Seção 1**: Setup e configuração
- **Seção 2**: Pesquisa - Escolha do método oficial de pré-processamento ⭐
- **Seção 3**: Inferência básica (método oficial padrão)
- **Seção 4**: Máscaras de segmentação Grad-CAM

**Estrutura didática:**
- Fluxo completo: da pesquisa à produção
- Decisão técnica documentada (~11% diferença entre métodos)
- Uso do endpoint `/generate_masks` (recomendado)

## 4.5 Comunicação entre Serviços

### Rede Docker

**docker-compose.yml:**

```yaml
# Network padrão (implícito)
networks:
  default:
    driver: bridge
```

**DNS automático:**
- `http://orthanc:8042` → container Orthanc
- `http://inference-api:8000` → container API
- `http://jupyter:8888` → container Jupyter

### Fluxo de Requisição Completo

```
1. NOTEBOOK (Jupyter container)
   ↓ GET http://orthanc:8042/instances

2. ORTHANC (Orthanc container)
   ← ["abc-123", "def-456"]

3. NOTEBOOK
   ↓ GET http://orthanc:8042/instances/abc-123/file

4. ORTHANC
   ← binary DICOM file

5. NOTEBOOK
   ↓ POST http://inference-api:8000/generate_masks
      multipart/form-data: dicom_file=... top_n=3

6. INFERENCE API (inference-api container)
   ↓ preprocess_dicom()
   ↓ model_predict()
   ↓ generate_gradcam()
   ← JSON response

7. NOTEBOOK
   ↓ Decode base64 images
   ↓ plt.imshow(...)
   → Display to user
```

### Acesso Externo

**Host machine → Containers:**

```bash
# Acessar Orthanc UI
open http://localhost:8042

# Testar API
curl http://localhost:8000/health

# Jupyter
open http://localhost:8888
```

**Port mapping (docker-compose.yml):**
```yaml
orthanc:
  ports: ["8042:8042"]  # host:container

inference-api:
  ports: ["8000:8000"]

jupyter:
  ports: ["8888:8888"]
```

---

## Navegação

- **[← Módulo 3: Explicabilidade e Interpretabilidade](./modulo3-explicabilidade.md)**
- **[→ Módulo 5: Implementação Técnica](./modulo5-implementacao.md)**
- **[← Voltar para Academia](../ACADEMY.md)**

---

**Próximo passo:** Continue para o [Módulo 5](./modulo5-implementacao.md) para mergulhar nos detalhes técnicos da implementação.
