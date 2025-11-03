# 🧠 Modelo de IA - TorchXRayVision

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0
> **Modelo:** DenseNet121

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [TorchXRayVision](#torchxrayvision)
- [Arquitetura DenseNet121](#arquitetura-densenet121)
- [Achados Detectados](#achados-detectados)
- [Performance](#performance)
- [Transfer Learning](#transfer-learning)
- [Uso no Projeto](#uso-no-projeto)
- [Explicabilidade (Grad-CAM)](#explicabilidade-grad-cam)

---

## Visão Geral

O **Mini PACS AI** utiliza o modelo **DenseNet121** pré-treinado da biblioteca [TorchXRayVision](https://github.com/mlmed/torchxrayvision) para detecção de achados radiológicos em imagens de raio-X de tórax.

**Características:**
- ✅ **Modelo pré-treinado** - Não requer treino adicional
- ✅ **Multi-label** - Detecta múltiplos achados simultaneamente
- ✅ **18 classes** - Ampla cobertura de patologias
- ✅ **Explicável** - Grad-CAM para interpretação visual
- ✅ **CPU-friendly** - Roda em CPU (GPU opcional)

---

## TorchXRayVision

### O que é?

TorchXRayVision é uma biblioteca PyTorch especializada em análise de raio-X de tórax:

**GitHub:** https://github.com/mlmed/torchxrayvision

**Recursos:**
- Modelos pré-treinados (DenseNet, ResNet)
- Datasets padronizados (NIH, CheXpert, MIMIC-CXR)
- Pré-processamento específico para raio-X
- Utilitários para Grad-CAM e visualização

### Instalação

```bash
pip install torchxrayvision
```

### Modelos Disponíveis

| Modelo | Arquitetura | Datasets | Resolução | Achados |
|--------|-------------|----------|-----------|---------|
| densenet121-res224-all | DenseNet121 | NIH + CheXpert + MIMIC | 224x224 | 18 |
| densenet121-res224-nih | DenseNet121 | NIH | 224x224 | 14 |
| densenet121-res224-chex | DenseNet121 | CheXpert | 224x224 | 14 |
| densenet121-res224-mimic | DenseNet121 | MIMIC-CXR | 224x224 | 14 |
| resnet50-res512-all | ResNet50 | NIH + CheXpert | 512x512 | 18 |

**Modelo usado neste projeto:** `densenet121-res224-all`

**Por quê?**
- ✅ Treinado em 224.316 imagens (3 datasets combinados)
- ✅ 18 achados (maior cobertura)
- ✅ Resolução 224x224 (mais rápido que 512x512)
- ✅ Performance comprovada (AUC-ROC médio: 0.84)

---

## Arquitetura DenseNet121

### Conceito: Dense Blocks

```
Input (224x224x1)
      ↓
  Conv2D (7x7)
      ↓
  MaxPool (3x3)
      ↓
┌──────────────┐
│ Dense Block 1│ ─┐
└──────────────┘  │
      ↓           │ Skip Connection
  Transition      │ (concatenation)
      ↓           │
┌──────────────┐  │
│ Dense Block 2│ ─┤
└──────────────┘  │
      ↓           │
  Transition      │
      ↓           │
┌──────────────┐  │
│ Dense Block 3│ ─┤
└──────────────┘  │
      ↓           │
  Transition      │
      ↓           │
┌──────────────┐  │
│ Dense Block 4│ ─┘
└──────────────┘
      ↓
  Global AvgPool
      ↓
  FC (18 outputs)
```

### Características

**Dense Blocks:**
- Cada camada recebe features de **TODAS** as camadas anteriores
- Reduce vanishing gradient problem
- Reutiliza features (eficiente em parâmetros)

**Transições:**
- Batch Normalization
- 1x1 Convolution (reduz canais)
- Average Pooling 2x2

**Parâmetros:**
- Total: ~8 milhões de parâmetros
- Camadas: 121 layers
- Input: 224x224 (grayscale)
- Output: 18 probabilidades [0, 1]

### Por que DenseNet vs ResNet?

| Aspecto | DenseNet121 | ResNet50 |
|---------|-------------|----------|
| Parâmetros | 8M | 25M |
| Memória | Menor | Maior |
| Gradiente | Melhor propagação | Boa propagação |
| Reuso de features | ✅ Máximo | Moderado |
| Performance | Similar | Similar |
| Velocidade CPU | ✅ Mais rápido | Mais lento |

**Escolha:** DenseNet121 por ser mais leve e igualmente preciso.

---

## Achados Detectados

### Lista Completa (18 classes)

| # | Achado | Nome em Português | Prevalência (NIH) |
|---|--------|-------------------|-------------------|
| 1 | Atelectasis | Atelectasia | 11.5% |
| 2 | Cardiomegaly | Cardiomegalia | 2.5% |
| 3 | Consolidation | Consolidação | 4.4% |
| 4 | Edema | Edema pulmonar | 2.0% |
| 5 | Pleural Effusion | Derrame pleural | 13.3% |
| 6 | Pneumonia | Pneumonia | 1.3% |
| 7 | Pneumothorax | Pneumotórax | 5.0% |
| 8 | Enlarged Cardiomediastinum | Mediastino alargado | - |
| 9 | Lung Lesion | Lesão pulmonar | - |
| 10 | Lung Opacity | Opacidade pulmonar | 17.5% |
| 11 | Fracture | Fratura | - |
| 12 | Support Devices | Dispositivos de suporte | - |
| 13 | No Finding | Sem achados | - |
| 14 | Pleural Other | Outras alterações pleurais | 3.0% |
| 15 | Infiltration | Infiltrado | 17.5% |
| 16 | Nodule | Nódulo | 5.6% |
| 17 | Mass | Massa | 5.1% |
| 18 | Emphysema | Enfisema | 2.2% |

### Glossário Clínico

**Atelectasis (Atelectasia):**
- Colapso parcial ou total do pulmão
- Redução de volume pulmonar
- Causas: obstrução, compressão, cicatrização

**Cardiomegaly (Cardiomegalia):**
- Aumento do tamanho do coração
- Razão cardiotorácica > 0.5
- Indica insuficiência cardíaca, hipertensão

**Pleural Effusion (Derrame pleural):**
- Acúmulo de líquido na cavidade pleural
- Opacifica ângulo costofrênico
- Causas: infecção, insuficiência cardíaca, câncer

**Pneumonia:**
- Infecção dos alvéolos pulmonares
- Consolidação do parênquima
- Opacidades localizadas ou difusas

**Pneumothorax (Pneumotórax):**
- Presença de ar na cavidade pleural
- Colapso parcial ou total do pulmão
- Emergência médica se tensional

**Lung Opacity (Opacidade pulmonar):**
- Área de aumento de densidade
- Pode indicar infiltrado, consolidação, massa
- Requer correlação clínica

**Support Devices (Dispositivos de suporte):**
- Tubo endotraqueal, sonda nasogástrica
- Cateter venoso central, marcapasso
- Dreno torácico

---

## Performance

### Métricas (NIH ChestX-ray14 Dataset)

| Achado | AUC-ROC | Sensibilidade | Especificidade |
|--------|---------|---------------|----------------|
| Cardiomegaly | 0.90 | 0.82 | 0.85 |
| Pleural Effusion | 0.88 | 0.79 | 0.83 |
| Pneumothorax | 0.88 | 0.81 | 0.84 |
| Consolidation | 0.82 | 0.74 | 0.79 |
| Edema | 0.89 | 0.80 | 0.84 |
| Pneumonia | 0.76 | 0.68 | 0.72 |
| Atelectasis | 0.81 | 0.73 | 0.77 |
| **Média** | **0.84** | **0.77** | **0.81** |

**Interpretação:**
- AUC-ROC 0.84 = **bom desempenho**
- Comparável a radiologista generalista
- Inferior a radiologista especialista (AUC ~0.90-0.95)

### Comparação com Radiologistas

**Estudo CheXNet (Stanford, 2017):**
- Modelo DenseNet121 vs 4 radiologistas
- Dataset: ChestX-ray14 (112.120 imagens)
- Resultado: **Modelo = Performance humana** (14 patologias)

**Limitações:**
- Melhor em achados comuns (Effusion, Cardiomegaly)
- Pior em achados raros (Pneumonia, Hernia)
- Sensível à qualidade da imagem
- Não considera contexto clínico

---

## Transfer Learning

### Conceito

```
ImageNet (1.4M imagens gerais)
         ↓ Pre-training
   DenseNet121 weights
         ↓ Transfer Learning
   Fine-tune em ChestX-ray
         ↓
   Modelo especializado
```

### Vantagens

| Aspecto | Transfer Learning | From Scratch |
|---------|-------------------|--------------|
| Dados necessários | 10.000 - 100.000 | 1.000.000+ |
| Tempo de treino | Horas (GPU) | Dias/Semanas |
| Compute | 1 GPU | Múltiplas GPUs |
| Performance | Boa | Melhor (se dados suficientes) |
| Custo | Baixo | Alto |

### Neste Projeto

**Escolha:** Usar modelo **já treinado** (sem fine-tuning adicional)

**Por quê?**
- ✅ TorchXRayVision já treinado em 224.316 raio-X
- ✅ Performance excelente (AUC 0.84)
- ✅ Pronto para uso (inference apenas)
- ✅ Foco na aplicação clínica, não em pesquisa de ML

**Alternativa (se fosse treinar):**
```python
# Fine-tuning (exemplo)
import torchxrayvision as xrv

# Carregar modelo pré-treinado
model = xrv.models.DenseNet(weights="densenet121-res224-all")

# Congelar features iniciais
for param in model.features.parameters():
    param.requires_grad = False

# Treinar apenas classificador
optimizer = torch.optim.Adam(model.classifier.parameters(), lr=0.001)

for epoch in range(10):
    for batch in dataloader:
        loss = criterion(model(batch.images), batch.labels)
        loss.backward()
        optimizer.step()
```

---

## Uso no Projeto

### Carregamento do Modelo

**Arquivo:** `inference_api/app/model.py`

```python
import torchxrayvision as xrv
import torch

# Singleton pattern (carrega apenas 1 vez)
_model = None

def get_model():
    """
    Carrega modelo TorchXRayVision (DenseNet121).

    Returns:
        model: TorchXRayVision model
    """
    global _model
    if _model is None:
        print("Carregando modelo TorchXRayVision...")
        _model = xrv.models.DenseNet(weights="densenet121-res224-all")
        _model.eval()  # Modo inferência (sem dropout)
        print(f"Modelo carregado. Patologias: {_model.pathologies}")
    return _model
```

**Otimizações:**
- ✅ Carregado apenas 1 vez (singleton)
- ✅ `eval()` mode (dropout desativado)
- ✅ CPU por padrão (GPU opcional)

### Inferência

**Arquivo:** `inference_api/app/model.py`

```python
def model_predict(tensor: torch.Tensor) -> dict:
    """
    Executa predição no tensor DICOM pré-processado.

    Args:
        tensor: [1, 1, 224, 224] tensor normalizado

    Returns:
        dict: {pathology: probability}
    """
    model = get_model()

    with torch.no_grad():  # Sem gradientes (mais rápido)
        outputs = model(tensor)  # [1, 18] logits

    # Sigmoid (multi-label classification)
    probs = torch.sigmoid(outputs).cpu().numpy()[0]

    # Mapear para dict
    return dict(zip(model.pathologies, probs.tolist()))
```

**Pipeline completo:**
```
DICOM bytes
    ↓ (preprocess.py)
Tensor [1, 1, 224, 224]
    ↓ (model.py)
DenseNet121 forward pass
    ↓
Logits [1, 18]
    ↓ (sigmoid)
Probabilidades [0, 1]
    ↓
{"Cardiomegaly": 0.78, ...}
```

### Performance

**Tempo de inferência (CPU):**
- Forward pass: 300-500 ms
- Grad-CAM (x5): 800-1200 ms
- **Total:** ~2-3 segundos por exame

**Com GPU (CUDA):**
- Forward pass: 50-100 ms
- Grad-CAM (x5): 200-400 ms
- **Total:** ~0.5-1 segundo

---

## Explicabilidade (Grad-CAM)

### O que é Grad-CAM?

**Grad-CAM** (Gradient-weighted Class Activation Mapping):
- Técnica de visualização para CNNs
- Mostra **onde** o modelo "olhou" para fazer predição
- Usa gradientes da última camada convolucional

**Paper:** [Selvaraju et al., 2017](https://arxiv.org/abs/1610.02391)

### Como funciona?

```
1. Forward pass: imagem → modelo → predição
2. Backward pass: ∂y^c / ∂A^k (gradiente da classe c)
3. Global Average Pooling dos gradientes: α_k^c
4. Weighted combination: L^c = ReLU(Σ α_k^c · A^k)
5. Upsample para 224x224
6. Normalizar para [0, 1]
```

### Implementação

**Arquivo:** `inference_api/app/gradcam.py`

```python
def generate_gradcam(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    target_class_idx: int
) -> np.ndarray:
    """
    Gera heatmap Grad-CAM.

    Args:
        model: DenseNet121
        input_tensor: [1, 1, 224, 224]
        target_class_idx: índice da classe (0-17)

    Returns:
        heatmap: [224, 224] com valores [0, 1]
    """
    model.eval()

    # Registrar hooks na última conv layer
    target_layer = model.features[-1]
    # ... (ver código completo em gradcam.py)

    # Forward + Backward
    output = model(input_tensor)
    output[0, target_class_idx].backward()

    # Calcular CAM
    gradients = ...  # Gradientes capturados
    features = ...   # Features capturadas
    weights = gradients.mean(axis=(1, 2))  # GAP
    cam = np.sum(weights * features, axis=0)  # Weighted sum
    cam = np.maximum(cam, 0)  # ReLU
    cam = cam / cam.max()  # Normalize

    # Upsample
    cam = cv2.resize(cam, (224, 224))

    return cam
```

### Máscaras de Segmentação

**Threshold adaptativo:**
```python
if probability > 0.7:
    threshold = 0.6  # Mais restritivo
elif probability > 0.5:
    threshold = 0.5  # Médio
else:
    threshold = 0.4  # Mais permissivo

mask = (heatmap > threshold).astype(np.uint8)
```

**Visualização:**
- Ver `notebooks/comparison_analysis.ipynb` PARTE 4
- Estilo [TorchXRayVision xray_masks.ipynb](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)
- Alpha blending: 50% imagem + 50% máscara

---

## Documentação Complementar

**TorchXRayVision:**
- GitHub: https://github.com/mlmed/torchxrayvision
- Paper: https://arxiv.org/abs/2003.11968
- Notebooks: https://github.com/mlmed/torchxrayvision/tree/main/scripts

**Grad-CAM:**
- Paper original: https://arxiv.org/abs/1610.02391
- Implementação: `inference_api/app/gradcam.py`
- Análise: `notebooks/comparison_analysis.ipynb` PARTE 2

**Datasets:**
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- CheXpert: https://stanfordmlgroup.github.io/competitions/chexpert/
- MIMIC-CXR: https://physionet.org/content/mimic-cxr/2.0.0/

**Papers:**
- CheXNet (Stanford, 2017): https://arxiv.org/abs/1711.05225
- DenseNet (Huang et al., 2017): https://arxiv.org/abs/1608.06993

**Arquivos do projeto:**
- Modelo: `inference_api/app/model.py`
- Grad-CAM: `inference_api/app/gradcam.py`
- API: `inference_api/app/main.py`
- Academy: `docs/ACADEMY.md` (Módulo 2 e 3)

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Autor:** Wendell Barreto (wendellbarreto@gmail.com)
