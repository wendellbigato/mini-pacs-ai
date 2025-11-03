# Plano: Visualização Grad-CAM e Pré-processamento Otimizado

**Data início:** 2025-11-02
**Status:** Em Progresso
**Prioridade:** Alta

---

## 🎯 Objetivos

Implementar duas melhorias críticas para acurácia e interpretabilidade:

1. **Pré-processamento Oficial TorchXRayVision** - Corrigir pipeline atual que não segue as recomendações do modelo
2. **Visualização Grad-CAM** - Adicionar heatmaps de atenção como visualizadores profissionais (Sante DICOM, Horos)
3. **Análise Comparativa** - Notebook demonstrando impacto das melhorias

---

## 📊 Problema Identificado

### Pré-processamento Atual (Incorreto)

**Arquivo:** `inference_api/app/preprocess.py:52-67`

```python
# PROBLEMA: Normalização não segue recomendações TorchXRayVision
pixel_array = pixel_array / pixel_array.max()  # → [0, 1]
# Z-score depois...
```

**Issue:** Modelo foi treinado com normalização [-1024, 1024] (escala HU de Hounsfield Units), não [0, 1]!

### Pipeline Recomendado (Oficial)

Segundo documentação TorchXRayVision:

```python
# CORRETO:
img = xrv.datasets.normalize(img, 255)  # → [-1024, 1024]
transform = torchvision.transforms.Compose([
    xrv.datasets.XRayCenterCrop(),
    xrv.datasets.XRayResizer(224)
])
```

**Referências:**
- https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py
- https://github.com/mlmed/torchxrayvision/issues/9

---

## 🏗️ Arquitetura das Melhorias

### 1. Pré-processamento Otimizado

**Arquivo:** `inference_api/app/preprocess_official.py` (NOVO)

```python
import torchxrayvision as xrv
import torch

def preprocess_dicom_official(dicom_path: str) -> torch.Tensor:
    """
    Pré-processamento usando pipeline oficial TorchXRayVision.

    Diferenças vs. atual:
    - Normalização [-1024, 1024] (HU scale)
    - XRayCenterCrop() para focar região torácica
    - XRayResizer(224) com interpolação apropriada
    """
    dcm = pydicom.dcmread(dicom_path)
    img = dcm.pixel_array

    # Normalização oficial
    img = xrv.datasets.normalize(img, 255)

    # Transformações
    transform = torchvision.transforms.Compose([
        xrv.datasets.XRayCenterCrop(),
        xrv.datasets.XRayResizer(224)
    ])

    img = transform(img)

    # Preparar tensor
    img = torch.from_numpy(img[None, ...])
    if len(img.shape) == 3:
        img = img[None, ...]

    return img
```

### 2. Visualização Grad-CAM

**Biblioteca:** `pytorch-grad-cam` (adicionar a requirements.txt)

**Arquivo:** `inference_api/app/gradcam.py` (NOVO)

```python
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
import numpy as np

def generate_gradcam(model, input_tensor, target_class_idx):
    """
    Gera heatmap Grad-CAM para interpretação da predição.

    Args:
        model: Modelo TorchXRayVision
        input_tensor: Imagem pré-processada [1, 1, 224, 224]
        target_class_idx: Índice da classe (achado radiológico)

    Returns:
        heatmap_overlay: Imagem com heatmap sobreposto
        heatmap: Heatmap raw (0-1)
    """
    # Target layer: última conv do DenseNet121
    target_layers = [model.model.features[-1]]

    cam = GradCAM(model=model, target_layers=target_layers)

    # Gera CAM
    grayscale_cam = cam(input_tensor=input_tensor,
                        targets=None)  # None = classe com maior score

    # Converte para RGB overlay
    heatmap = grayscale_cam[0, :]

    return heatmap
```

**Novo Endpoint:** `POST /predict_with_heatmap`

```python
@app.post("/predict_with_heatmap")
async def predict_with_heatmap(
    dicom_file: UploadFile = File(...),
    top_n: int = 3  # Top N achados para gerar heatmaps
):
    """
    Retorna predições + heatmaps Grad-CAM das top N classes.
    """
    # 1. Pré-processar
    img_tensor = preprocess_official(dicom_file)

    # 2. Predição
    probabilities = model(img_tensor)

    # 3. Top N classes
    top_classes = torch.topk(probabilities, top_n)

    # 4. Gerar heatmap para cada
    heatmaps = {}
    for idx in top_classes.indices[0]:
        label = model.pathologies[idx]
        heatmap = generate_gradcam(model, img_tensor, idx)
        heatmaps[label] = heatmap.tolist()

    return {
        "probabilities": dict(zip(model.pathologies, probabilities[0].tolist())),
        "heatmaps": heatmaps,
        "metadata": extract_metadata(dicom_file)
    }
```

### 3. Endpoint de Comparação

**Novo Endpoint:** `POST /compare_preprocessing`

```python
@app.post("/compare_preprocessing")
async def compare_preprocessing(dicom_file: UploadFile = File(...)):
    """
    Compara predições usando pré-processamento atual vs. oficial.

    Returns:
        - probabilities_current: Usando preprocess.py atual
        - probabilities_official: Usando preprocess_official.py
        - differences: Dict com diferenças absolutas
    """
    # Processar com ambos métodos
    img_current = preprocess_dicom(dicom_file)  # Atual
    img_official = preprocess_dicom_official(dicom_file)  # Novo

    # Predições
    probs_current = model(img_current)
    probs_official = model(img_official)

    # Calcular diferenças
    diff = torch.abs(probs_current - probs_official)

    return {
        "current": dict(zip(model.pathologies, probs_current[0].tolist())),
        "official": dict(zip(model.pathologies, probs_official[0].tolist())),
        "absolute_differences": dict(zip(model.pathologies, diff[0].tolist())),
        "max_difference": float(diff.max()),
        "mean_difference": float(diff.mean())
    }
```

---

## 📝 Implementação Passo a Passo

### Fase 1: Corrigir Pré-processamento ⭐ (Prioridade 1)

**Impacto:** Pode melhorar acurácia imediatamente

- [ ] Criar `inference_api/app/preprocess_official.py`
- [ ] Adicionar `torchxrayvision` como dependência explícita em `requirements.txt`
- [ ] Atualizar `main.py` para usar novo pré-processamento (ou adicionar flag)
- [ ] Criar endpoint `/compare_preprocessing` para validação
- [ ] Testar com DICOMs existentes e comparar diferenças
- [ ] **Decisão:** Se diferenças significativas, substituir `preprocess.py` completamente

**Critério de sucesso:**
- `mean_difference < 0.05` → Manter atual (já está próximo)
- `mean_difference >= 0.05` → Trocar para oficial (melhoria esperada)

### Fase 2: Adicionar Grad-CAM ⭐ (Prioridade 2)

**Impacto:** Interpretabilidade clínica (padrão-ouro em visualizadores)

- [ ] Adicionar `pytorch-grad-cam==1.4.8` em `requirements.txt`
- [ ] Criar `inference_api/app/gradcam.py`
- [ ] Implementar endpoint `POST /predict_with_heatmap`
- [ ] Adicionar documentação Swagger para novo endpoint
- [ ] Testar com diferentes achados radiológicos
- [ ] Validar se heatmaps fazem sentido clinicamente (ex: Cardiomegaly deve destacar região cardíaca)

**Output esperado:**
```json
{
  "probabilities": {...},
  "heatmaps": {
    "Cardiomegaly": [[0.1, 0.2, ...], ...],  // 224x224 heatmap
    "Pleural Effusion": [[...], ...]
  }
}
```

### Fase 3: Notebook de Análise Comparativa 📊 (Prioridade 3)

**Arquivo:** `notebooks/comparison_analysis.ipynb` (NOVO)

**Células:**

1. **Comparação de Pré-processamento**
   - Mesma imagem processada com ambos métodos
   - Visualização lado-a-lado
   - Tabela de diferenças nas probabilidades

2. **Visualização Grad-CAM**
   - Para cada achado no top 5:
     - Imagem original
     - Heatmap Grad-CAM
     - Overlay (imagem + heatmap)
     - Probabilidade

3. **Análise Consolidada**
   - Processar todas as 9 instâncias do Orthanc
   - Comparar acurácia percebida (visual check se heatmaps fazem sentido)
   - Estatísticas de diferenças no pré-processamento

**Exemplo de célula:**

```python
# Célula: Comparação de Pré-processamento
instance_id = instances[0]
dicom_bytes = download_dicom(instance_id)

# Chamar endpoint de comparação
response = requests.post(
    f"{API_URL}/compare_preprocessing",
    files={"dicom_file": ("test.dcm", dicom_bytes, "application/dicom")}
)
comparison = response.json()

# Plotar diferenças
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Current
# Plot 2: Official
# Plot 3: Differences

# Tabela de top diferenças
diff_df = pd.DataFrame({
    "Achado": comparison["absolute_differences"].keys(),
    "Diferença": comparison["absolute_differences"].values()
}).sort_values("Diferença", ascending=False).head(10)

print(diff_df)
```

---

## 📦 Mudanças em Arquivos

### Novos Arquivos

1. `inference_api/app/preprocess_official.py` - Pipeline TorchXRayVision oficial
2. `inference_api/app/gradcam.py` - Geração de heatmaps
3. `notebooks/comparison_analysis.ipynb` - Análise comparativa
4. `docs/plans/inprogress/visualizacao-preprocessing.md` - Este arquivo

### Arquivos Modificados

1. `inference_api/requirements.txt`
   ```diff
   + pytorch-grad-cam==1.4.8
   + torchxrayvision  # Explicitamente (já era dependência implícita)
   ```

2. `inference_api/app/main.py`
   ```diff
   + from app.preprocess_official import preprocess_dicom_official
   + from app.gradcam import generate_gradcam
   +
   + @app.post("/compare_preprocessing")
   + async def compare_preprocessing(...):
   +     ...
   +
   + @app.post("/predict_with_heatmap")
   + async def predict_with_heatmap(...):
   +     ...
   ```

3. `README.md` - Seção "Jupyter Container: Melhores Práticas"
   - Justificativas técnicas da escolha do container dedicado
   - Comparação com alternativas (Opção 2 e 3)
   - Benefícios: segurança, eficiência, escalabilidade

4. `CHANGELOG.md` - Versão 1.2.0
   - [FEATURE] Pré-processamento oficial TorchXRayVision
   - [FEATURE] Endpoint /predict_with_heatmap (Grad-CAM)
   - [FEATURE] Endpoint /compare_preprocessing
   - [DOCS] Notebook de análise comparativa
   - [DOCS] Justificativas de arquitetura Jupyter

5. `Makefile`
   ```diff
   + test-preprocessing: ## Compara pré-processamentos (requer DICOM)
   +     @python test_preprocessing_comparison.py
   ```

---

## 🧪 Testes

### Teste 1: Validar Pré-processamento

```bash
# 1. Rebuild da API com novo código
make rebuild

# 2. Testar endpoint de comparação
curl -X POST "http://localhost:8000/compare_preprocessing" \
  -F "dicom_file=@/path/to/dicom.dcm" | jq '.mean_difference'

# Esperado: < 0.1 (se já estava próximo) ou > 0.1 (melhoria significativa)
```

### Teste 2: Validar Grad-CAM

```bash
# Testar heatmap
curl -X POST "http://localhost:8000/predict_with_heatmap" \
  -F "dicom_file=@/path/to/dicom.dcm" \
  -F "top_n=3" | jq '.heatmaps | keys'

# Esperado: ["Cardiomegaly", "Pleural Effusion", ...]
```

### Teste 3: Notebook Completo

```bash
# Abrir Jupyter
make jupyter

# Executar notebooks/comparison_analysis.ipynb
# Verificar:
# - Heatmaps fazem sentido clinicamente
# - Diferenças de pré-processamento < 10% (ou justificar)
```

---

## 🎯 Critérios de Sucesso

### Pré-processamento

- ✅ Endpoint `/compare_preprocessing` retorna diferenças
- ✅ Diferenças documentadas e justificadas
- ✅ Se `mean_difference >= 0.05`: substituir pipeline atual
- ✅ Se `mean_difference < 0.05`: manter atual, adicionar oficial como opção

### Grad-CAM

- ✅ Heatmaps são gerados para top N classes
- ✅ Heatmaps visualmente fazem sentido (ex: Cardiomegaly destaca coração)
- ✅ Performance aceitável (< 2s por inferência com heatmap)
- ✅ Documentação Swagger atualizada

### Notebook

- ✅ Comparação lado-a-lado visual
- ✅ Tabelas de diferenças estatísticas
- ✅ Análise de todas as 9 instâncias do Orthanc
- ✅ Conclusões sobre qual pré-processamento usar

### Documentação

- ✅ README.md justifica escolhas de arquitetura Jupyter
- ✅ CHANGELOG.md documenta v1.2.0
- ✅ Swagger docs atualizados com novos endpoints

---

## 📚 Referências Técnicas

### Pré-processamento TorchXRayVision

- **Documentação oficial:** https://mlmed.org/torchxrayvision/
- **Issue normalização:** https://github.com/mlmed/torchxrayvision/issues/9
- **Dataset utils:** https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py

### Grad-CAM

- **Paper original:** https://arxiv.org/abs/1610.02391
- **pytorch-grad-cam:** https://github.com/jacobgil/pytorch-grad-cam
- **Tutorial médico:** https://glassboxmedicine.com/2020/05/29/grad-cam-visual-explanations-from-deep-networks/

### Visualizadores Profissionais (Benchmarks)

- **Sante DICOM Viewer:** Usa CAM/Grad-CAM para AI findings
- **Horos (macOS):** Plugins com heatmaps
- **3D Slicer:** Módulo de AI visualization

---

## ⏱️ Estimativa de Tempo

| Fase | Tempo | Complexidade |
|------|-------|--------------|
| Fase 1: Pré-processamento | 2-3h | Média |
| Fase 2: Grad-CAM | 3-4h | Alta |
| Fase 3: Notebook Análise | 2-3h | Média |
| Documentação | 1-2h | Baixa |
| **TOTAL** | **8-12h** | |

---

## 🚨 Riscos e Mitigações

### Risco 1: Pré-processamento oficial piora resultados

- **Probabilidade:** Baixa (modelo foi treinado com esse pipeline)
- **Impacto:** Médio
- **Mitigação:** Manter ambas opções, adicionar flag `use_official_preprocessing=True/False`

### Risco 2: Grad-CAM lento em CPU

- **Probabilidade:** Média
- **Impacto:** Médio (> 5s por inferência)
- **Mitigação:**
  - Cachear heatmaps já gerados
  - Tornar opcional (endpoint separado)
  - Considerar aproximações mais rápidas (Score-CAM)

### Risco 3: Heatmaps não fazem sentido clinicamente

- **Probabilidade:** Baixa (Grad-CAM é padrão)
- **Impacto:** Alto (perda de confiança no sistema)
- **Mitigação:**
  - Validar com médicos (se disponível)
  - Comparar com literatura (papers usando TorchXRayVision + Grad-CAM)
  - Adicionar disclaimer: "Heatmaps são indicativos, não diagnósticos"

---

## 🎓 Justificativas de Melhores Práticas

### Por que Container Jupyter Dedicado? (Resposta para README.md)

**Contexto:** Escolha entre 3 opções de arquitetura.

**Decisão:** Opção 1 - Container dedicado no mesmo `docker-compose.yml`

**Justificativas:**

1. **Segurança** (Princípio de Menor Privilégio)
   - Jupyter isolado em container próprio
   - Breach no Jupyter ≠ acesso ao código da API
   - Sem acesso direto ao modelo PyTorch
   - Network policy: Jupyter → API (somente REST), não acesso direto a memória

2. **Eficiência** (Recursos)
   - Imagem: ~500 MB (vs. 2 GB de imagens oficiais Jupyter)
   - RAM: 200-500 MB (vs. 1-2 GB)
   - Pode ser desligado independentemente (`make jupyter-stop`)
   - Não compete por recursos com inferência

3. **Escalabilidade** (Separation of Concerns)
   - Jupyter escala independentemente da API
   - Pode ter N analistas rodando notebooks simultaneamente
   - API escala baseado em carga de inferência, não notebooks
   - Deploy independente (CI/CD separado)

4. **Manutenibilidade** (Single Responsibility Principle)
   - API: Servir predições
   - Jupyter: Análise exploratória
   - Mudanças no notebook não requerem rebuild da API
   - Dockerfile de cada serviço focado em uma responsabilidade

**Alternativas consideradas e rejeitadas:**

- ❌ **Opção 2:** Jupyter dentro do container da API
  - Viola SoC (API + notebook no mesmo processo)
  - Mudança em notebook requer rebuild de toda API
  - Segurança: breach tem acesso direto ao modelo

- ❌ **Opção 3:** Imagem oficial Jupyter
  - 2 GB (vs. 500 MB customizada)
  - Inclui pacotes desnecessários (Julia, R)
  - Menos controle sobre versões

**Padrão da indústria:**
- Google Colab, Kaggle, SageMaker: notebooks sempre separados da infraestrutura de inferência
- Microservices pattern: "one concern per container"

---

**Status:** ✅ Plano aprovado, iniciando implementação

**Próximo passo:** Fase 1 - Corrigir pré-processamento
