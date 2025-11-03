# 🔬 Documentação da API de Inferência

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0
> **Base URL:** http://localhost:8000

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Endpoints](#endpoints)
  - [POST /predict](#post-predict)
  - [POST /predict_with_heatmap](#post-predict_with_heatmap)
  - [POST /compare_preprocessing](#post-compare_preprocessing)
  - [GET /masks](#get-masks)
  - [POST /validate_masks](#post-validate_masks)
  - [GET /health](#get-health)
  - [GET /labels](#get-labels)
- [Exemplos de Uso](#exemplos-de-uso)
- [Códigos de Resposta](#códigos-de-resposta)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

A API de Inferência é uma REST API construída com FastAPI que:
- Recebe arquivos DICOM
- Executa inferência usando TorchXRayVision
- Retorna probabilidades de 18 achados radiológicos
- Gera visualizações Grad-CAM com máscaras de segmentação

**Tecnologias:**
- FastAPI 0.104+
- PyTorch
- TorchXRayVision
- PyDICOM
- OpenCV (para Grad-CAM)

**Documentação Interativa:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Endpoints

### POST /predict

Recebe um arquivo DICOM e retorna probabilidades de achados radiológicos.

**URL:** `/predict`

**Método:** `POST`

**Content-Type:** `multipart/form-data`

**Parâmetros:**

| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| `dicom_file` | File | ✅ Sim | Arquivo DICOM (.dcm) |

**Exemplo de Request (cURL):**

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "dicom_file=@/path/to/exam.dcm"
```

**Exemplo de Request (Python):**

```python
import requests

url = "http://localhost:8000/predict"
files = {"dicom_file": open("exam.dcm", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Response (200 OK):**

```json
{
  "probabilities": {
    "Atelectasis": 0.123,
    "Cardiomegaly": 0.456,
    "Consolidation": 0.078,
    "Edema": 0.234,
    "Pleural Effusion": 0.567,
    "Pneumonia": 0.089,
    "Pneumothorax": 0.045,
    "Enlarged Cardiomediastinum": 0.389,
    "Lung Lesion": 0.012,
    "Lung Opacity": 0.678,
    "Fracture": 0.001,
    "Support Devices": 0.890,
    "No Finding": 0.123,
    "Pleural Other": 0.045,
    "Infiltration": 0.234,
    "Nodule": 0.089,
    "Mass": 0.034,
    "Emphysema": 0.012
  },
  "metadata": {
    "patient_id": "123456",
    "study_date": "20240101",
    "modality": "CR",
    "image_shape": "(2619, 2000)"
  }
}
```

**Achados Detectados:**
- Total: 18 classes
- Saída: Probabilidade [0, 1] para cada achado
- Modelo: DenseNet121 (TorchXRayVision)

---

### POST /predict_with_heatmap

Realiza predição E gera heatmaps Grad-CAM + máscaras de segmentação para interpretação visual.

**URL:** `/predict_with_heatmap`

**Método:** `POST`

**Content-Type:** `multipart/form-data`

**Parâmetros:**

| Nome | Tipo | Obrigatório | Descrição | Padrão |
|------|------|-------------|-----------|--------|
| `dicom_file` | File | ✅ Sim | Arquivo DICOM (.dcm) | - |
| `top_n` | int | ❌ Não | Número de heatmaps a gerar | 5 |
| `use_official_preprocessing` | bool | ❌ Não | Usar pipeline oficial TorchXRayVision | true |

**Exemplo de Request (cURL):**

```bash
curl -X POST "http://localhost:8000/predict_with_heatmap?top_n=3&use_official_preprocessing=true" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "dicom_file=@exam.dcm"
```

**Exemplo de Request (Python):**

```python
import requests

url = "http://localhost:8000/predict_with_heatmap"
params = {
    "top_n": 3,
    "use_official_preprocessing": True
}
files = {"dicom_file": open("exam.dcm", "rb")}
response = requests.post(url, params=params, files=files)
result = response.json()

# Decodificar imagens base64
import base64
from io import BytesIO
from PIL import Image

for heatmap_data in result['heatmaps']:
    # Heatmap
    heatmap_b64 = heatmap_data['heatmap_base64'].split(',')[1]
    heatmap_img = Image.open(BytesIO(base64.b64decode(heatmap_b64)))

    # Máscara
    mask_b64 = heatmap_data['mask_base64'].split(',')[1]
    mask_img = Image.open(BytesIO(base64.b64decode(mask_b64)))

    print(f"{heatmap_data['pathology']}: {heatmap_data['probability']:.2%}")
```

**Response (200 OK):**

```json
{
  "probabilities": {
    "Atelectasis": 0.123,
    "Cardiomegaly": 0.780,
    "Consolidation": 0.078,
    ...
  },
  "heatmaps": [
    {
      "pathology": "Cardiomegaly",
      "probability": 0.780,
      "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
      "mask_base64": "data:image/png;base64,iVBORw0KGgo..."
    },
    {
      "pathology": "Lung Opacity",
      "probability": 0.678,
      "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
      "mask_base64": "data:image/png;base64,iVBORw0KGgo..."
    },
    {
      "pathology": "Pleural Effusion",
      "probability": 0.567,
      "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
      "mask_base64": "data:image/png;base64,iVBORw0KGgo..."
    }
  ],
  "metadata": {
    "patient_id": "123456",
    "study_date": "20240101",
    "modality": "CR",
    "image_shape": "(2619, 2000)"
  }
}
```

**Componentes da Resposta:**

**1. Heatmaps (coloridos):**
- Formato: PNG em base64
- Dimensão: 224x224 pixels
- Colormap: HOT (preto → vermelho → amarelo)
- Mostra intensidade da atenção do modelo

**2. Máscaras (binárias):**
- Formato: PNG em base64
- Dimensão: 224x224 pixels
- Threshold adaptativo:
  - Prob > 0.7 → threshold 0.6 (mais restritivo)
  - Prob > 0.5 → threshold 0.5 (médio)
  - Prob ≤ 0.5 → threshold 0.4 (mais permissivo)
- Segmentação automática das regiões de atenção

**Uso Clínico:**
- Ver `CLINICAL_USAGE.md` para interpretação adequada
- Ver `notebooks/comparison_analysis.ipynb` PARTE 4 para visualização
- Referência: [TorchXRayVision xray_masks.ipynb](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)*

*Nota: O notebook oficial mostra ground truth (anotações manuais). Nossa implementação gera máscaras automaticamente via Grad-CAM.

---

### POST /compare_preprocessing

Compara predições usando dois métodos de pré-processamento (atual vs oficial TorchXRayVision).

**URL:** `/compare_preprocessing`

**Método:** `POST`

**Content-Type:** `multipart/form-data`

**Parâmetros:**

| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| `dicom_file` | File | ✅ Sim | Arquivo DICOM (.dcm) |

**Exemplo de Request:**

```bash
curl -X POST "http://localhost:8000/compare_preprocessing" \
  -F "dicom_file=@exam.dcm"
```

**Response (200 OK):**

```json
{
  "current_method": {
    "Atelectasis": 0.120,
    "Cardiomegaly": 0.450,
    ...
  },
  "official_method": {
    "Atelectasis": 0.150,
    "Cardiomegaly": 0.480,
    ...
  },
  "absolute_differences": {
    "Atelectasis": 0.030,
    "Cardiomegaly": 0.030,
    ...
  },
  "statistics": {
    "mean_difference": 0.0785,
    "max_difference": 0.1612,
    "max_difference_pathology": "Enlarged Cardiomediastinum",
    "std_difference": 0.0415
  },
  "preprocessing_stats": {
    "current": {
      "min": 0.0,
      "max": 1.0,
      "mean": 0.5,
      "std": 0.29
    },
    "official": {
      "min": -1024.0,
      "max": 1024.0,
      "mean": 0.0,
      "std": 512.0
    }
  }
}
```

**Interpretação:**

- **mean_difference < 0.05:** Métodos similares
- **mean_difference ≥ 0.05:** Diferença significativa → preferir método oficial
- **max_difference:** Maior discordância entre métodos
- **preprocessing_stats:** Estatísticas das imagens pré-processadas

**Uso:**
- Validar qual método usar
- Análise detalhada em `notebooks/comparison_analysis.ipynb` PARTE 1
- Documentação em `docs/PREPROCESSAMENTO.md`

---

### GET /masks

Retorna máscaras ground truth de uma amostra do NIH Dataset (validação científica).

**URL:** `/masks`

**Método:** `GET`

**Parâmetros:**

| Nome | Tipo | Obrigatório | Descrição | Padrão |
|------|------|-------------|-----------|--------|
| `sample_idx` | int | ❌ Não | Índice da amostra no dataset | 0 |
| `pathology` | str | ❌ Não | Buscar amostra com patologia específica | - |

**Exemplo de Request:**

```bash
# Amostra por índice
curl "http://localhost:8000/masks?sample_idx=42"

# Buscar por patologia
curl "http://localhost:8000/masks?pathology=Cardiomegaly"
```

**Response (200 OK - Dataset disponível):**

```json
{
  "dataset_available": true,
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "masks": [
    {
      "pathology": "Cardiomegaly",
      "has_mask": true,
      "mask_base64": "data:image/png;base64,iVBORw0KGgo...",
      "coverage_percentage": 15.3
    },
    {
      "pathology": "Atelectasis",
      "has_mask": false,
      "mask_base64": null,
      "coverage_percentage": 0.0
    }
  ],
  "pathologies": ["Atelectasis", "Cardiomegaly", "Effusion", ...],
  "sample_idx": 42,
  "message": "Amostra 42 do NIH dataset carregada com sucesso"
}
```

**Response (200 OK - Dataset não disponível):**

```json
{
  "dataset_available": false,
  "message": "NIH Dataset não configurado. Configure NIH_DATASET_PATH no docker-compose.yml para habilitar validação científica."
}
```

**Requisitos:**
- NIH Dataset configurado (ver seção "Validação Científica")
- Variável `NIH_DATASET_PATH` no docker-compose.yml
- Dataset: ~45 GB, 112.120 imagens

**Uso:**
- Validação científica
- Comparação Grad-CAM vs Ground Truth
- Pesquisa e benchmarking

---

### POST /validate_masks

Valida predições Grad-CAM comparando com máscaras ground truth do NIH Dataset.

**URL:** `/validate_masks`

**Método:** `POST`

**Content-Type:** `multipart/form-data`

**Parâmetros:**

| Nome | Tipo | Obrigatório | Descrição | Padrão |
|------|------|-------------|-----------|--------|
| `dicom_file` | File | ✅ Sim | Arquivo DICOM (.dcm) | - |
| `nih_sample_idx` | int | ❌ Não | Índice da amostra NIH para comparar | 0 |

**Exemplo de Request:**

```bash
curl -X POST "http://localhost:8000/validate_masks?nih_sample_idx=42" \
  -F "dicom_file=@exam.dcm"
```

**Response (200 OK - Dataset disponível):**

```json
{
  "dataset_available": true,
  "validations": [
    {
      "pathology": "Cardiomegaly",
      "iou_score": 0.68,
      "gradcam_coverage": 18.5,
      "groundtruth_coverage": 15.3,
      "gradcam_mask_base64": "data:image/png;base64,...",
      "groundtruth_mask_base64": "data:image/png;base64,...",
      "evaluation": "good"
    },
    {
      "pathology": "Effusion",
      "iou_score": 0.52,
      "gradcam_coverage": 12.3,
      "groundtruth_coverage": 10.8,
      "gradcam_mask_base64": "data:image/png;base64,...",
      "groundtruth_mask_base64": "data:image/png;base64,...",
      "evaluation": "excellent"
    }
  ],
  "average_iou": 0.60,
  "message": "2 patologias validadas com sucesso"
}
```

**Métricas de Avaliação (IoU - Intersection over Union):**

| IoU Score | Avaliação | Interpretação |
|-----------|-----------|---------------|
| > 0.5 | Excellent | Localização muito precisa |
| 0.3 - 0.5 | Good | Localização boa, aceitável |
| 0.1 - 0.3 | Fair | Localização razoável |
| ≤ 0.1 | Poor | Localização imprecisa |

**Campos da Resposta:**

- `iou_score`: Intersection over Union (0-1)
- `gradcam_coverage`: % da imagem coberta pela máscara Grad-CAM
- `groundtruth_coverage`: % da imagem coberta pela ground truth
- `evaluation`: Classificação qualitativa (excellent/good/fair/poor)

**Uso:**
- Medir precisão do Grad-CAM
- Pesquisa científica
- Validação de melhorias no modelo

---

### GET /health

Verifica status da API e do modelo.

**URL:** `/health`

**Método:** `GET`

**Exemplo de Request:**

```bash
curl http://localhost:8000/health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "DenseNet121",
  "num_pathologies": 18
}
```

**Campos:**
- `status`: "healthy" ou "unhealthy"
- `model_loaded`: Se modelo TorchXRayVision está carregado
- `model_name`: Nome do modelo (DenseNet121)
- `num_pathologies`: Número de achados detectáveis

---

### GET /labels

Retorna lista de achados radiológicos que o modelo pode predizer.

**URL:** `/labels`

**Método:** `GET`

**Exemplo de Request:**

```bash
curl http://localhost:8000/labels
```

**Response (200 OK):**

```json
{
  "labels": [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion",
    "Pneumonia",
    "Pneumothorax",
    "Enlarged Cardiomediastinum",
    "Lung Lesion",
    "Lung Opacity",
    "Fracture",
    "Support Devices",
    "No Finding",
    "Pleural Other",
    "Infiltration",
    "Nodule",
    "Mass",
    "Emphysema"
  ],
  "count": 18
}
```

---

## Exemplos de Uso

### Via Swagger UI (Interface Web)

1. Acesse http://localhost:8000/docs
2. Expanda o endpoint desejado (ex: `POST /predict_with_heatmap`)
3. Clique em "Try it out"
4. Configure parâmetros (top_n, use_official_preprocessing)
5. Faça upload de um arquivo DICOM
6. Clique em "Execute"
7. Veja o resultado JSON na resposta

### Script Python Completo

```python
import requests
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# 1. Predição com heatmaps
url = "http://localhost:8000/predict_with_heatmap"
params = {"top_n": 3, "use_official_preprocessing": True}
files = {"dicom_file": open("exam.dcm", "rb")}

response = requests.post(url, params=params, files=files)
result = response.json()

# 2. Exibir probabilidades
print("Probabilidades:")
for pathology, prob in result['probabilities'].items():
    if prob > 0.3:
        print(f"  {pathology}: {prob:.2%}")

# 3. Visualizar heatmaps
fig, axes = plt.subplots(1, len(result['heatmaps']), figsize=(15, 5))

for i, heatmap_data in enumerate(result['heatmaps']):
    # Decodificar heatmap
    heatmap_b64 = heatmap_data['heatmap_base64'].split(',')[1]
    heatmap_img = Image.open(BytesIO(base64.b64decode(heatmap_b64)))

    # Plotar
    axes[i].imshow(heatmap_img)
    axes[i].set_title(f"{heatmap_data['pathology']}\n{heatmap_data['probability']:.0%}")
    axes[i].axis('off')

plt.tight_layout()
plt.show()
```

### Script de Teste (test_predict.py)

```bash
# Usar script fornecido no repositório
python test_predict.py /path/to/exam.dcm

# Saída:
# ✅ Predição realizada com sucesso!
#
# Top 10 Achados Radiológicos:
# Lung Opacity                 0.678 ████████████████████████████████
# Cardiomegaly                 0.456 ███████████████████████
# Pleural Effusion             0.567 ████████████████████████████
# ...
```

---

## Códigos de Resposta

| Código | Status | Descrição |
|--------|--------|-----------|
| 200 | OK | Requisição bem-sucedida |
| 400 | Bad Request | Parâmetros inválidos |
| 422 | Unprocessable Entity | Arquivo não é DICOM válido ou campo ausente |
| 500 | Internal Server Error | Erro no servidor (verificar logs) |

**Tratamento de Erros:**

```python
try:
    response = requests.post(url, files=files)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        print("Erro: Arquivo DICOM inválido")
    elif e.response.status_code == 500:
        print("Erro no servidor. Verifique os logs:")
        print("docker compose logs inference-api")
    else:
        print(f"Erro HTTP: {e}")
except Exception as e:
    print(f"Erro: {e}")
```

---

## Troubleshooting

### Erro 422: Unprocessable Entity

**Causa:** Arquivo não é DICOM válido ou campo `dicom_file` ausente.

**Solução:**
```bash
# Verificar se arquivo é DICOM válido
python -c "import pydicom; pydicom.dcmread('exam.dcm')"

# Verificar nome do campo no request
curl -F "dicom_file=@exam.dcm" ...  # ✅ Correto
curl -F "file=@exam.dcm" ...         # ❌ Errado
```

### Erro 500: Internal Server Error

**Causa:** Erro no processamento (modelo não carregado, DICOM corrompido, etc.)

**Solução:**
```bash
# 1. Verificar logs
docker compose logs inference-api

# 2. Verificar saúde da API
curl http://localhost:8000/health

# 3. Se modelo não carregado, rebuild
docker compose down
docker compose build inference-api
docker compose up -d

# 4. Aguardar carregamento do modelo (~10s)
sleep 10
curl http://localhost:8000/health
```

### API não responde

**Causa:** Container parado ou não iniciado.

**Solução:**
```bash
# Verificar status
docker compose ps

# Se parado, subir
docker compose up -d inference-api

# Testar conectividade
curl http://localhost:8000/health
```

### Predições inconsistentes

**Causa:** Pré-processamento inadequado.

**Solução:**
```bash
# 1. Comparar métodos de pré-processamento
curl -X POST "http://localhost:8000/compare_preprocessing" \
  -F "dicom_file=@exam.dcm" | jq '.statistics'

# 2. Se mean_difference > 0.05, usar método oficial
curl -X POST "http://localhost:8000/predict_with_heatmap?use_official_preprocessing=true" \
  -F "dicom_file=@exam.dcm"
```

### NIH Dataset não disponível

**Causa:** Variável `NIH_DATASET_PATH` não configurada.

**Solução:** Ver seção "Validação Científica" no README.md principal ou documentação completa em `TESTE_API.md`.

---

## Documentação Complementar

- **Guia de Testes Completo:** [TESTE_API.md](../TESTE_API.md)
- **Uso Clínico:** [CLINICAL_USAGE.md](../CLINICAL_USAGE.md)
- **Pré-processamento:** [docs/PREPROCESSAMENTO.md](./PREPROCESSAMENTO.md)
- **Modelo IA:** [docs/MODELO_IA.md](./MODELO_IA.md)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Endpoints disponíveis:** 7
**Autor:** Wendell Barreto (wendellbarreto@gmail.com)
