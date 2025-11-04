# Módulo 2: Inteligência Artificial em Radiologia

> **Parte da:** [Academia Mini PACS AI](../ACADEMY.md)
> **Duração estimada:** 60-75 minutos
> **Pré-requisitos:** [Módulo 1](./modulo1-fundamentos-pacs-dicom.md)

---

## 2.1 Deep Learning para Raio-X

### Por que Deep Learning?

**Problema clássico:**
- Radiologista humano: 10-20 anos de treinamento
- Identifica padrões visuais sutis
- Memória de milhares de casos

**IA pode:**
- Treinar em milhões de casos
- Detectar padrões invisíveis ao olho humano
- Ser consistente (não fica cansado)
- Dar segunda opinião

### CNN (Convolutional Neural Networks)

**Arquitetura básica:**

```
INPUT                    CONVOLUTION               POOLING
┌─────────┐             ┌───────────┐             ┌─────┐
│         │   Filters   │           │   MaxPool   │     │
│ 224x224 │ ────────→  │  112x112  │ ────────→  │56x56│
│         │   3x3, 64   │  64 maps  │    2x2      │ 64  │
└─────────┘             └───────────┘             └─────┘
                                                      ↓
                                                  FC LAYERS
                                                  ┌─────┐
                                                  │ 14  │ Outputs
                                                  └─────┘
```

**O que acontece em cada camada:**

1. **Convolução** - detecta features (bordas, texturas)
2. **ReLU** - não-linearidade
3. **Pooling** - reduz dimensão, mantém features importantes
4. **Flatten** - transforma em vetor
5. **Dense** - classificação final

### Dataset: NIH ChestX-ray14

**Origem:**
- National Institutes of Health (USA)
- 112.120 imagens de raio-X frontal
- 30.805 pacientes únicos
- Anotado por NLP (Natural Language Processing) dos laudos

**14 Achados radiológicos:**

| Achado | Prevalência | Tradução |
|--------|-------------|----------|
| Atelectasis | 11.5% | Atelectasia (colapso pulmonar parcial) |
| Cardiomegaly | 2.5% | Cardiomegalia (coração aumentado) |
| Effusion | 13.3% | Derrame pleural |
| Infiltration | 17.5% | Infiltrado |
| Mass | 5.1% | Massa |
| Nodule | 5.6% | Nódulo |
| Pneumonia | 1.3% | Pneumonia |
| Pneumothorax | 5.0% | Pneumotórax (ar na pleura) |
| Consolidation | 4.4% | Consolidação |
| Edema | 2.0% | Edema pulmonar |
| Emphysema | 2.2% | Enfisema |
| Fibrosis | 1.5% | Fibrose |
| Pleural_Thickening | 3.0% | Espessamento pleural |
| Hernia | 0.2% | Hérnia |

**Limitações do dataset:**
- Labels gerados por NLP (não anotação manual)
- Possíveis erros/ruídos
- Múltiplos achados por imagem (multi-label)

### Transfer Learning

**Conceito:**
```
ImageNet (1.4M imagens gerais)
         ↓
   Pre-trained weights
         ↓
   Fine-tune em ChestX-ray
         ↓
   Modelo especializado
```

**Vantagens:**
- Menos dados necessários
- Treino mais rápido
- Features genéricas (bordas, texturas) já aprendidas
- Foco em features específicas de raio-X

**Exemplo:**
```python
import torchvision.models as models

# Modelo pré-treinado no ImageNet
model = models.densenet121(pretrained=True)

# Modificar última camada para 14 achados
model.classifier = nn.Linear(1024, 14)

# Fine-tune apenas últimas camadas
for param in model.features.parameters():
    param.requires_grad = False
```

## 2.2 TorchXRayVision

### O que é?

**TorchXRayVision** é uma biblioteca PyTorch especializada em raio-X:
- Modelos pré-treinados (DenseNet, ResNet)
- Datasets padronizados (NIH, CheXpert, MIMIC-CXR)
- Pré-processamento automático
- Utilitários para Grad-CAM

**GitHub:** https://github.com/mlmed/torchxrayvision

### Instalação

```bash
pip install torchxrayvision
```

### Modelos Disponíveis

```python
import torchxrayvision as xrv

# Ver modelos disponíveis
xrv.models.get_model_names()
# ['densenet121-res224-all',
#  'densenet121-res224-rsna',
#  'densenet121-res224-nih',
#  'resnet50-res512-all', ...]
```

**Principais modelos:**

| Nome | Arquitetura | Datasets | Resolução | Achados |
|------|-------------|----------|-----------|---------|
| densenet121-res224-all | DenseNet121 | NIH + CheXpert + MIMIC | 224x224 | 18 |
| densenet121-res224-nih | DenseNet121 | NIH | 224x224 | 14 |
| resnet50-res512-all | ResNet50 | NIH + CheXpert | 512x512 | 18 |

### Uso Básico

```python
import torchxrayvision as xrv
import torch

# Carregar modelo
model = xrv.models.DenseNet(weights="densenet121-res224-all")
model.eval()

# Preparar imagem (normalização específica de raio-X)
img = xrv.datasets.normalize(img, maxval=255, reshape=True)
img = torch.from_numpy(img).unsqueeze(0)

# Predição
with torch.no_grad():
    outputs = model(img)

# Probabilidades (sigmoid para multi-label)
probs = torch.sigmoid(outputs).cpu().numpy()[0]

# Mapear para achados
predictions = dict(zip(model.pathologies, probs))
```

### Normalização Especial

TorchXRayVision usa normalização **específica para raio-X**:

```python
def normalize(img, maxval, reshape=False):
    """
    Normaliza imagem de raio-X.

    1. Escala para [0, maxval]
    2. Normaliza com mean/std de múltiplos datasets
    3. Garante formato [1, H, W]
    """
    # Implementação interna
    img = img / maxval  # [0, 1]
    img = (img - 0.5) / 0.5  # [-1, 1] aproximadamente

    if reshape:
        img = img[None, ...]  # [1, H, W]

    return img
```

**Por que não usar ImageNet normalization?**
- ImageNet: fotos coloridas RGB
- Raio-X: grayscale, física diferente (atenuação de raios-X)
- Range de intensidades diferente

## 2.3 Modelos Pré-Treinados

### DenseNet121

**Arquitetura:**

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
  FC (14 outputs)
```

**Dense Blocks:**
- Cada camada recebe features de TODAS as camadas anteriores
- Reduce vanishing gradient
- Reutiliza features (eficiente)

**Parâmetros:**
- ~8 milhões de parâmetros
- 121 camadas
- Input: 224x224 (raio-X)

### Performance

**Métricas típicas (NIH ChestX-ray14):**

| Achado | AUC-ROC | Sensibilidade | Especificidade |
|--------|---------|---------------|----------------|
| Cardiomegaly | 0.90 | 0.82 | 0.85 |
| Effusion | 0.88 | 0.79 | 0.83 |
| Pneumonia | 0.76 | 0.68 | 0.72 |
| Pneumothorax | 0.88 | 0.81 | 0.84 |
| **Média** | **0.84** | - | - |

**Interpretação:**
- AUC-ROC 0.84 = bom desempenho
- Varia por achado (pneumonia é mais difícil)
- Comparável a radiologista generalista
- Inferior a radiologista especialista

## 2.4 Transfer Learning vs Training from Scratch

### Comparação

| Aspecto | Transfer Learning | From Scratch |
|---------|-------------------|--------------|
| Dados necessários | 1.000 - 10.000 | 100.000+ |
| Tempo de treino | Horas | Dias/Semanas |
| Compute | 1 GPU | Múltiplas GPUs |
| Performance | Boa | Melhor (se dados suficientes) |
| Custo | Baixo | Alto |

### Por que usamos Transfer Learning?

**Neste projeto:**
- ✅ Modelo TorchXRayVision já treinado em 224.316 raio-X
- ✅ Pronto para uso (inference apenas)
- ✅ Sem necessidade de treino adicional
- ✅ Foco na aplicação clínica, não em pesquisa

**Alternativa (se fosse treinar):**
```python
# Pseudo-código de fine-tuning

# 1. Carregar modelo pré-treinado
model = xrv.models.DenseNet(weights="densenet121-res224-all")

# 2. Congelar features iniciais
for param in model.features.parameters():
    param.requires_grad = False

# 3. Treinar apenas classificador
optimizer = torch.optim.Adam(model.classifier.parameters(), lr=0.001)

# 4. Treinar em dataset local
for epoch in range(10):
    for batch in dataloader:
        loss = criterion(model(batch.images), batch.labels)
        loss.backward()
        optimizer.step()
```

---

**Módulo anterior:** [Módulo 1: Fundamentos PACS e DICOM](./modulo1-fundamentos-pacs-dicom.md)
**Próximo módulo:** [Módulo 3: Explicabilidade e Interpretabilidade](./modulo3-explicabilidade.md)
