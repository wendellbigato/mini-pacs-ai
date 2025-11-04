# Módulo 5: Implementação Técnica

> **[← Voltar para Academia Mini PACS AI](../ACADEMY.md)**

**Duração estimada:** 3-4 horas
**Pré-requisitos:** Módulo 1-4 (Fundamentos, IA, Explicabilidade e Arquitetura)

---

## 5.1 Pré-Processamento DICOM

### Desafios

**DICOM ≠ Imagem comum:**
- Profundidade: 12-16 bits (não 8 bits)
- Range: 0-4095 (não 0-255)
- Orientação: variável (PA, AP, Lateral)
- Tamanho: variável (1500x1500, 2000x2500, etc.)
- Metadados: embedded no arquivo

### Pipeline

```
DICOM bytes
    ↓
pydicom.dcmread()
    ↓
pixel_array (numpy int16)
    ↓
Convert to float32
    ↓
Normalize (método escolhido)
    ↓
Resize to 224x224
    ↓
Reshape to [1, 1, 224, 224]
    ↓
torch.Tensor
```

### Método Oficial TorchXRayVision

```python
def preprocess_official(img: np.ndarray) -> np.ndarray:
    """
    Pré-processamento oficial TorchXRayVision.

    Referência:
    https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py#L743
    """
    # 1. Normalizar para [0, 255]
    img = img - img.min()
    img = img / img.max()
    img = img * 255.0

    # 2. Aplicar normalization do dataset
    img = xrv.datasets.normalize(img, maxval=255, reshape=True)
    # Internamente faz:
    #   img = img / 255  # [0, 1]
    #   img = (img - 0.5) / 0.5  # aproximadamente [-1, 1]
    #   + outros ajustes específicos

    # 3. Resize (feito internamente pelo modelo)
    # Input já vem em 224x224 após transforms

    return img
```

### Método Alternativo (Comparação)

```python
def preprocess_custom(img: np.ndarray) -> np.ndarray:
    """
    Método alternativo para comparação.
    """
    # 1. Normalizar para [0, 1]
    img = img.astype(np.float32)
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)

    # 2. Resize
    img = transform.resize(img, (224, 224), mode='constant')

    # 3. Z-score normalization
    mean = img.mean()
    std = img.std()
    img = (img - mean) / (std + 1e-8)

    # 4. Reshape
    img = img[None, ...]  # [1, H, W]

    return img
```

### Comparação Experimental

**Seção 2 do orthanc_analysis.ipynb:**

```python
# Testar ambos métodos no mesmo DICOM
response_current = requests.post(
    f"{API_URL}/predict",
    files={"dicom_file": dicom_bytes},
    params={"use_official_preprocessing": False}
)

response_official = requests.post(
    f"{API_URL}/predict",
    files={"dicom_file": dicom_bytes},
    params={"use_official_preprocessing": True}
)

# Comparar probabilidades
diff = abs(probs_current - probs_official)
if diff.mean() > 0.05:
    print("⚠️ Diferença significativa! Usar método oficial.")
else:
    print("✅ Ambos métodos similares.")
```

**Resultado típico:**
```
Mean difference: 0.113
Max difference: 0.161 (Enlarged Cardiomediastinum)
Std difference: 0.041

Decisão: Usar método oficial (diferença > 0.05)
```

## 5.2 Pipeline de Inferência

### Fluxo Completo

```python
async def predict_with_heatmap(
    dicom_file: UploadFile,
    top_n: int = 5,
    use_official_preprocessing: bool = True
):
    # 1. Ler arquivo
    dicom_bytes = await dicom_file.read()

    # 2. Pré-processar
    tensor, metadata = preprocess_dicom(
        dicom_bytes,
        use_official=use_official_preprocessing
    )
    # tensor.shape = [1, 1, 224, 224]

    # 3. Predição
    probabilities = model_predict(tensor)
    # {'Cardiomegaly': 0.78, 'Effusion': 0.65, ...}

    # 4. Top N achados
    sorted_probs = sorted(
        probabilities.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    # 5. Gerar Grad-CAM para cada achado
    model = get_model()
    heatmaps_data = []

    for pathology, prob in sorted_probs:
        # Índice da classe
        class_idx = model.pathologies.index(pathology)

        # Grad-CAM
        heatmap = generate_gradcam(model, tensor, class_idx)
        # heatmap.shape = (224, 224), valores [0, 1]

        # Threshold adaptativo
        if prob > 0.7:
            threshold = 0.6
        elif prob > 0.5:
            threshold = 0.5
        else:
            threshold = 0.4

        # Máscara binária
        mask = generate_binary_mask_from_heatmap(heatmap, threshold)

        # Encode to base64
        heatmap_b64 = encode_heatmap(heatmap)
        mask_b64 = encode_mask(mask)

        heatmaps_data.append({
            "pathology": pathology,
            "probability": float(prob),
            "heatmap_base64": heatmap_b64,
            "mask_base64": mask_b64
        })

    # 6. Retornar resposta
    return PredictionWithHeatmapResponse(
        probabilities=probabilities,
        heatmaps=heatmaps_data,
        metadata=metadata
    )
```

### Performance

**Tempo de execução típico (CPU):**

| Etapa | Tempo |
|-------|-------|
| Upload DICOM | 50-100 ms |
| Pré-processamento | 100-200 ms |
| Inferência (forward) | 300-500 ms |
| Grad-CAM (x5 achados) | 800-1200 ms |
| Encoding base64 | 100-200 ms |
| **TOTAL** | **~2-3 segundos** |

**Com GPU (CUDA):**
- Inferência: 50-100 ms
- Grad-CAM: 200-400 ms
- **TOTAL: ~0.5-1 segundo**

### Otimizações Aplicadas

**1. Singleton Model:**
```python
# Modelo carregado 1 vez no startup
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model
```

**2. No Gradient Computation:**
```python
with torch.no_grad():
    outputs = model(tensor)
# Economiza memória + 2x mais rápido
```

**3. Batch Size 1:**
```python
# Apenas 1 imagem por vez (suficiente para uso clínico)
tensor.shape = [1, 1, 224, 224]
```

**4. CPU vs GPU:**
```python
# Configurável via variável de ambiente
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
```

## 5.3 Geração de Heatmaps

### Código Completo

**inference_api/app/gradcam.py:**

```python
import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import base64

def generate_gradcam(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    target_class_idx: int,
    use_relu: bool = True
) -> np.ndarray:
    """
    Gera heatmap Grad-CAM.

    Referência:
    Selvaraju et al. (2017) https://arxiv.org/abs/1610.02391

    Args:
        model: modelo PyTorch (DenseNet121)
        input_tensor: [1, 1, 224, 224]
        target_class_idx: índice da classe alvo (0-17 para TorchXRayVision)
        use_relu: aplicar ReLU (True = foca apenas em contribuições positivas)

    Returns:
        heatmap: [224, 224] com valores [0, 1]
    """
    model.eval()

    # Registrar hooks
    features_blobs = []
    gradients_blobs = []

    def forward_hook(module, input, output):
        features_blobs.append(output.data.cpu().numpy())

    def backward_hook(module, grad_in, grad_out):
        gradients_blobs.append(grad_out[0].data.cpu().numpy())

    # Última camada convolucional (DenseNet: features[-1])
    target_layer = model.features[-1]

    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_backward_hook(backward_hook)

    # Forward pass
    output = model(input_tensor)

    # Backward pass
    model.zero_grad()
    one_hot = torch.zeros_like(output)
    one_hot[0, target_class_idx] = 1
    output.backward(gradient=one_hot, retain_graph=False)

    # Obter features e gradientes
    features = features_blobs[0][0]  # [C, H, W]
    gradients = gradients_blobs[0][0]  # [C, H, W]

    # Global Average Pooling dos gradientes
    weights = np.mean(gradients, axis=(1, 2))  # [C]

    # Weighted combination
    cam = np.zeros(features.shape[1:], dtype=np.float32)  # [H, W]
    for i, w in enumerate(weights):
        cam += w * features[i, :, :]

    # ReLU (apenas ativações positivas)
    if use_relu:
        cam = np.maximum(cam, 0)

    # Normalizar para [0, 1]
    if cam.max() > 0:
        cam = cam / cam.max()

    # Upsample para 224x224
    cam = cv2.resize(cam, (224, 224))

    # Remover hooks
    forward_handle.remove()
    backward_handle.remove()

    return cam


def generate_binary_mask_from_heatmap(
    heatmap: np.ndarray,
    threshold: float = 0.5,
    colormap: int = cv2.COLORMAP_HOT
) -> str:
    """
    Gera máscara binária colorida a partir de heatmap.

    Args:
        heatmap: [H, W] com valores [0, 1]
        threshold: limiar de binarização
        colormap: colormap OpenCV (COLORMAP_HOT, COLORMAP_JET, etc.)

    Returns:
        base64 string da imagem PNG
    """
    # Binarizar
    binary_mask = (heatmap > threshold).astype(np.uint8)

    # Aplicar colormap
    colored_mask = cv2.applyColorMap(
        np.uint8(255 * binary_mask),
        colormap
    )

    # BGR → RGB
    colored_mask = cv2.cvtColor(colored_mask, cv2.COLOR_BGR2RGB)

    # Converter para base64
    img = Image.fromarray(colored_mask)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"
```

### Escolhas de Implementação

**1. Por que última conv layer?**
- Melhor compromisso resolução vs semantics
- Layers iniciais: alta resolução, features genéricas (bordas)
- Layers finais: baixa resolução, features específicas (cardiomegalia)

**2. Por que ReLU?**
- Remove contribuições negativas (confundem visualização)
- Foca em regiões que **aumentam** a probabilidade da classe

**3. Por que Global Average Pooling?**
- Paper original usa GAP
- Mais robusto que apenas pegar valor máximo

**4. Colormap HOT:**
- Preto (frio) → vermelho (quente)
- Intuitivo para médicos
- Alternativas: JET (azul→vermelho), VIRIDIS

## 5.4 Validação Científica

### Métricas

**IoU (Intersection over Union):**

```
IoU = Área de Interseção / Área de União

      ┌─────────┐
      │ Pred    │
      │   ┌─────┼─────┐
      │   │ ∩   │     │ GT
      └───┼─────┘     │
          └───────────┘

IoU = |Pred ∩ GT| / |Pred ∪ GT|
```

**Código:**

```python
def calculate_iou(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    """
    Calcula IoU entre máscara predita e ground truth.

    Args:
        pred_mask: [H, W] binária {0, 1}
        gt_mask: [H, W] binária {0, 1}

    Returns:
        iou: float [0, 1]
    """
    intersection = np.logical_and(pred_mask, gt_mask).sum()
    union = np.logical_or(pred_mask, gt_mask).sum()

    if union == 0:
        return 0.0

    iou = intersection / union
    return float(iou)
```

**Interpretação:**

| IoU | Qualidade | Uso Clínico |
|-----|-----------|-------------|
| > 0.8 | Excelente | Confiável |
| 0.6-0.8 | Boa | Aceitável com supervisão |
| 0.4-0.6 | Razoável | Apenas triagem |
| < 0.4 | Pobre | Não usar |

**Resultados típicos (Grad-CAM vs Ground Truth):**
- Cardiomegaly: IoU ~0.72
- Effusion: IoU ~0.68
- Pneumothorax: IoU ~0.65
- **Média: IoU ~0.68** (razoável/boa)

### Dice Coefficient

**Alternativa ao IoU:**

```python
def calculate_dice(pred_mask, gt_mask):
    intersection = np.logical_and(pred_mask, gt_mask).sum()
    dice = 2 * intersection / (pred_mask.sum() + gt_mask.sum())
    return dice
```

**Relação com IoU:**
```
Dice = 2 * IoU / (1 + IoU)
```

### Validação no Projeto

**Endpoint:** `POST /validate_masks`

```python
@app.post("/validate_masks")
async def validate_masks(
    dicom_file: UploadFile,
    nih_sample_idx: int
):
    # 1. Gerar predição Grad-CAM
    result = await predict_with_heatmap(dicom_file, top_n=3)
    pred_masks = [decode_base64(hm['mask_base64']) for hm in result['heatmaps']]

    # 2. Obter ground truth do NIH dataset
    gt_sample = nih_dataset[nih_sample_idx]
    gt_mask = gt_sample['mask']

    # 3. Calcular IoU
    ious = []
    for pred_mask in pred_masks:
        iou = calculate_iou(pred_mask, gt_mask)
        ious.append(iou)

    # 4. Classificar qualidade
    quality = "excellent" if max(ious) > 0.8 else \
              "good" if max(ious) > 0.6 else \
              "fair" if max(ious) > 0.4 else \
              "poor"

    return {
        "ious": ious,
        "mean_iou": np.mean(ious),
        "quality": quality
    }
```

**Nota:** NIH Dataset **não é obrigatório** para uso normal (apenas validação científica).

---

## Navegação

- **[← Módulo 4: Arquitetura da Aplicação](./modulo4-arquitetura.md)**
- **[→ Módulo 6: Discovery e Insights de Desenvolvimento](./modulo6-discovery.md)**
- **[← Voltar para Academia](../ACADEMY.md)**

---

**Próximo passo:** Continue para o [Módulo 6](./modulo6-discovery.md) para conhecer os desafios e decisões tomadas durante o desenvolvimento.
