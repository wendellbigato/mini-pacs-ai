# Módulo 3: Explicabilidade e Interpretabilidade

> **[← Voltar para Academia Mini PACS AI](../ACADEMY.md)**

**Duração estimada:** 2-3 horas
**Pré-requisitos:** Módulo 1 (PACS/DICOM) e Módulo 2 (Deep Learning)

---

## 3.1 O Problema da Caixa Preta

### Por que explicabilidade importa?

**Cenário:**
```
IA: "Probabilidade de pneumonia: 87%"
Médico: "Onde você viu pneumonia?"
IA: "..."
```

**Problemas:**
- ❌ Médico não pode validar o raciocínio
- ❌ Impossível ensinar residentes
- ❌ Difícil detectar erros do modelo
- ❌ Não aprovado por reguladores (FDA/ANVISA)

### Regulamentação

**FDA (USA) - Class II Medical Device:**
- Requer explicação das predições
- "Substantial equivalence" com dispositivos aprovados
- Post-market surveillance

**ANVISA (Brasil):**
- RDC 44/2023 - Dispositivos médicos com software
- Exige rastreabilidade das decisões
- Documentação de validação clínica

**GDPR (Europa):**
- "Right to explanation"
- Decisões automatizadas devem ser explicáveis

### Tipos de Explicabilidade

**1. Global:**
- Como o modelo funciona em geral?
- Quais features são mais importantes?

**2. Local:**
- Por que esta predição específica?
- O que influenciou este caso?

**3. Visual:**
- Mostrar regiões de atenção
- Heatmaps, saliency maps

## 3.2 Grad-CAM: Class Activation Maps

### O que é Grad-CAM?

**Grad-CAM** (Gradient-weighted Class Activation Mapping):
- Técnica de visualização para CNNs
- Mostra **onde** o modelo "olhou" para fazer predição
- Usa gradientes da última camada convolucional

**Paper original:**
> Selvaraju et al. (2017) "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization"
> https://arxiv.org/abs/1610.02391

### Como funciona?

**Algoritmo:**

```
1. Forward pass: imagem → modelo → predição

2. Backward pass: gradiente da classe c em relação à última conv layer
   ∂y^c / ∂A^k  (gradiente da classe c em relação ao feature map k)

3. Global Average Pooling dos gradientes:
   α_k^c = (1/Z) Σ Σ (∂y^c / ∂A_{ij}^k)
   (importância do feature map k para classe c)

4. Combinação linear dos feature maps:
   L^c_Grad-CAM = ReLU( Σ α_k^c · A^k )

5. Upsample para resolução original
   Heatmap = resize(L^c_Grad-CAM, (H, W))

6. Normalizar para [0, 1]
```

**Visualmente:**

```
INPUT IMAGE          CONV LAYERS             GRADIENTS
┌─────────┐         ┌───────────┐           ┌─────────┐
│         │         │FeatureMap │ ∂y^c/∂A  │Weights  │
│ 224x224 │  ────→  │  14x14    │  ─────→  │ α_1...αn│
│         │         │  512 maps │           └─────────┘
└─────────┘         └───────────┘                ↓
                                          WEIGHTED SUM
                                                ↓
                                          ┌─────────┐
                                          │Heatmap  │
                                          │ 14x14   │
                                          └─────────┘
                                                ↓
                                             UPSAMPLE
                                                ↓
                                          ┌─────────┐
                                          │Heatmap  │
                                          │ 224x224 │
                                          └─────────┘
```

### Implementação

**inference_api/app/gradcam.py:**

```python
def generate_gradcam(model, input_tensor, target_class_idx):
    """
    Gera heatmap Grad-CAM.

    Args:
        model: modelo PyTorch
        input_tensor: [1, 1, H, W]
        target_class_idx: índice da classe alvo

    Returns:
        heatmap: [H, W] com valores [0, 1]
    """
    model.eval()

    # 1. Registrar hook na última conv layer
    features = []
    gradients = []

    def forward_hook(module, input, output):
        features.append(output)

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    target_layer = model.features[-1]  # última conv
    fh = target_layer.register_forward_hook(forward_hook)
    bh = target_layer.register_backward_hook(backward_hook)

    # 2. Forward pass
    output = model(input_tensor)

    # 3. Backward pass
    model.zero_grad()
    target = output[0, target_class_idx]
    target.backward()

    # 4. Calcular pesos α_k
    gradient = gradients[0].cpu().data.numpy()[0]  # [C, H, W]
    feature = features[0].cpu().data.numpy()[0]    # [C, H, W]

    weights = np.mean(gradient, axis=(1, 2))  # [C] - GAP

    # 5. Weighted sum
    cam = np.zeros(feature.shape[1:], dtype=np.float32)  # [H, W]
    for i, w in enumerate(weights):
        cam += w * feature[i, :, :]

    # 6. ReLU
    cam = np.maximum(cam, 0)

    # 7. Normalizar
    cam = cam / np.max(cam)

    # 8. Upsample
    cam = cv2.resize(cam, (224, 224))

    # Remover hooks
    fh.remove()
    bh.remove()

    return cam
```

### Vantagens do Grad-CAM

**✅ Vantagens:**
- Funciona com qualquer CNN (não precisa retreinar)
- Resolução razoável (tamanho da última conv layer)
- Genérico (qualquer classe)
- Implementação simples

**❌ Limitações:**
- Resolução limitada pela conv layer (14x14 → 224x224)
- Pode misturar múltiplos objetos
- Não é perfeito (podem haver falsos positivos)

### Alternativas

| Método | Resolução | Velocidade | Precisão |
|--------|-----------|------------|----------|
| CAM | Baixa | Rápida | Boa |
| Grad-CAM | Média | Rápida | Boa |
| Grad-CAM++ | Média | Média | Melhor |
| Attention Maps | Alta | Lenta | Melhor |
| Saliency Maps | Alta | Lenta | Variável |

## 3.3 Máscaras de Segmentação

### Grad-CAM → Máscara Binária

**Pipeline:**

```
Heatmap Grad-CAM [0, 1]
        ↓
  Thresholding
        ↓
Máscara Binária {0, 1}
        ↓
  Colormap (hot)
        ↓
Visualização RGB
```

**Código:**

```python
def generate_binary_mask_from_heatmap(
    heatmap: np.ndarray,
    threshold: float = 0.5
) -> np.ndarray:
    """
    Converte heatmap em máscara binária.

    Args:
        heatmap: [H, W] valores [0, 1]
        threshold: limiar de binarização

    Returns:
        mask: [H, W] valores {0, 1}
    """
    binary_mask = (heatmap > threshold).astype(np.uint8)
    return binary_mask
```

### Threshold Adaptativo

**Problema:**
- Threshold fixo (ex: 0.5) nem sempre é ideal
- Alta probabilidade → área mais focada (threshold alto)
- Baixa probabilidade → área mais ampla (threshold baixo)

**Solução implementada:**

```python
if probability > 0.7:
    threshold = 0.6  # Mais restritivo
elif probability > 0.5:
    threshold = 0.5  # Médio
else:
    threshold = 0.4  # Mais permissivo
```

**Exemplo:**
```
Cardiomegaly: 0.85 → threshold 0.6 → área pequena e focada
Pneumonia: 0.48    → threshold 0.4 → área maior, menos certa
```

### Visualização Estilo TorchXRayVision

**Referência:**
https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb

**Layout:**
```
┌─────────┬─────────┬─────────┬─────────┐
│         │Máscara 1│Máscara 2│Máscara 3│
│Original │ (alpha) │ (alpha) │ (alpha) │
│         │Cardio   │Effusion │ Pneumo  │
└─────────┴─────────┴─────────┴─────────┘
```

**Código (notebook PARTE 4):**

```python
# Estilo TorchXRayVision
fig, axs = plt.subplots(1, 1+len(masks), figsize=(3+3*len(masks), 3))

# Imagem original
axs[0].imshow(original_img, cmap="gray")
axs[0].set_title("Original")

# Máscaras sobrepostas (alpha=0.5)
for i, (mask, pathology, prob) in enumerate(zip(masks, pathologies, probs)):
    axs[i+1].imshow(original_img, cmap="gray")
    axs[i+1].imshow(mask, alpha=0.5, cmap='hot')
    axs[i+1].set_title(f"{pathology}\n{prob:.0%}")
```

**Alpha blending:**
- alpha=0.5 → 50% imagem original, 50% máscara
- Permite ver anatomia E região de atenção simultaneamente

## 3.4 Ground Truth vs Predição

### Diferença Fundamental

| Aspecto | Ground Truth | Grad-CAM |
|---------|--------------|----------|
| **Origem** | Anotação manual (radiologista) | Gerado automaticamente (IA) |
| **Precisão** | Alta (~95%) | Média (~70-80%) |
| **Tempo** | Horas/dias | 2-3 segundos |
| **Custo** | Alto ($$$) | Zero |
| **Escalabilidade** | Baixa | Infinita |
| **Exames novos?** | ❌ Não | ✅ Sim |

### Ground Truth (Anotação Manual)

**Processo:**
```
1. Radiologista especialista
2. Desenha contorno manual (bounding box ou segmentação)
3. Revisão por segundo radiologista
4. Consenso ou terceiro revisor
5. Armazenado em dataset (ex: NIH, RSNA)
```

**Exemplos de datasets com ground truth:**
- **RSNA Pneumonia Detection Challenge** - bounding boxes
- **SIIM-ACR Pneumothorax** - máscaras de segmentação
- **NIH Dataset** - algumas imagens têm bounding boxes

**Uso:**
- Treino de modelos de segmentação (U-Net, Mask R-CNN)
- Validação científica (calcular IoU, Dice)
- Benchmark de modelos

### Grad-CAM (Gerado Automaticamente)

**Processo:**
```
1. Modelo de classificação faz predição
2. Grad-CAM calcula regiões de atenção
3. Threshold gera máscara binária
4. Pronto! (2-3 segundos)
```

**Uso:**
- Explicação de predições (interpretabilidade)
- Auxílio diagnóstico PACS (tempo real)
- Segunda opinião para médico
- Triagem automática

### Por que usamos Grad-CAM neste projeto?

**Contexto clínico:**
- ✅ PACS recebe exames novos diariamente
- ✅ Impossível ter ground truth para cada exame
- ✅ Médico precisa de auxílio IMEDIATO (não dá para esperar anotação)
- ✅ Grad-CAM é "good enough" para mostrar onde o modelo "olhou"

**Decisão de design:**
> "Para uso clínico em PACS, Grad-CAM é a **única abordagem viável** porque funciona em exames novos sem anotação manual prévia."

**Validação:**
- Em pesquisa: comparamos Grad-CAM com ground truth (IoU ~70%)
- Em produção: usamos Grad-CAM para todos os exames

### Comparação Visual

**Ground Truth (xray_masks.ipynb):**
```python
# Notebook oficial TorchXRayVision
# Mostra MÁSCARAS MANUAIS do NIH dataset

mask_gt = nih_dataset[0]['mask']  # Anotação humana
plt.imshow(mask_gt)
```

**Grad-CAM (nosso sistema):**
```python
# Mini PACS AI
# Gera MÁSCARAS AUTOMÁTICAS via Grad-CAM

mask_gradcam = generate_binary_mask_from_heatmap(heatmap)
plt.imshow(mask_gradcam)
```

**Diferença importante:**
- `xray_masks.ipynb` → ensino/validação (dataset estático)
- `orthanc_analysis.ipynb Seção 4` → produção clínica (exames novos)

---

## Navegação

- **[← Módulo 2: Inteligência Artificial em Radiologia](../ACADEMY.md#módulo-2-inteligência-artificial-em-radiologia)**
- **[→ Módulo 4: Arquitetura da Aplicação](./modulo4-arquitetura.md)**
- **[← Voltar para Academia](../ACADEMY.md)**

---

**Próximo passo:** Continue para o [Módulo 4](./modulo4-arquitetura.md) para entender a arquitetura completa do sistema.
