# 🎓 Academia Mini PACS AI - Guia Rápido

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0+
> **Duração:** 30 minutos
> **Objetivo:** Visão geral completa do projeto - do conceito à produção

---

## 🎯 O Que Você Vai Aprender

Em 30 minutos você vai entender:
- ✅ Como funciona um PACS e o padrão DICOM
- ✅ Como IA detecta patologias em raio-X
- ✅ Por que Grad-CAM é essencial para explicabilidade
- ✅ Arquitetura multi-container do sistema
- ✅ Como usar em ambiente clínico real
- ✅ Regulamentação e responsabilidades

> **Nota:** Versão detalhada (8h) disponível em [academy-detalhada/](./academy-detalhada/)

---

# 1. Fundamentos PACS e DICOM (5 min)

## O que é PACS?

**PACS** (Picture Archiving and Communication System) = sistema para armazenar, recuperar e distribuir imagens médicas digitais.

**Antes do PACS:** Filmes físicos, perda de exames, impossível ver remotamente
**Com PACS:** Tudo digital, backup automático, acesso instantâneo de qualquer lugar

## DICOM: O Padrão Mundial

**DICOM** = formato de arquivo + protocolo de comunicação para imagens médicas

```
arquivo.dcm
├─ HEADER (metadados: paciente, data, equipamento)
└─ PIXEL DATA (a imagem em si)
```

**Hierarquia DICOM:**
```
PATIENT → STUDY → SERIES → INSTANCE
```

**Exemplo:**
```
João Silva → Raio-X Tórax (2025-11-04) → Série PA → imagem_001.dcm
```

## Orthanc: PACS Open Source

**Por que Orthanc?**
- ✅ Open source, leve, roda em Docker
- ✅ REST API completa (GET /instances, POST /instances)
- ✅ Ideal para desenvolvimento e pequenos hospitais

**Endpoints principais:**
```bash
GET /instances          # Listar todas as imagens
GET /instances/{id}/file # Baixar DICOM
GET /instances/{id}/tags # Ver metadados
```

---

# 2. IA em Radiologia (5 min)

## TorchXRayVision

Biblioteca PyTorch especializada em raio-X com modelos pré-treinados.

**Modelo usado:** DenseNet121
- Treinado em 224.316 raio-X (NIH + CheXpert + MIMIC)
- Detecta 18 achados radiológicos
- AUC-ROC médio: 0.84 (bom desempenho)

## Como Funciona?

```python
import torchxrayvision as xrv

# 1. Carregar modelo (já treinado!)
model = xrv.models.DenseNet(weights="densenet121-res224-all")

# 2. Pré-processar imagem DICOM
img = preprocess_dicom(dicom_bytes)  # → [1, 1, 224, 224]

# 3. Predição
outputs = model(img)
probs = torch.sigmoid(outputs)  # Multi-label

# 4. Resultado
# {'Cardiomegaly': 0.85, 'Effusion': 0.72, ...}
```

## 18 Achados Detectados

Cardiomegaly, Effusion, Pneumonia, Pneumothorax, Atelectasis, Consolidation, Edema, Emphysema, Fibrosis, Mass, Nodule, Infiltration, Pleural_Thickening, Enlarged_Cardiomediastinum, Lung_Opacity, Lung_Lesion, Fracture, Support_Devices

---

# 3. Explicabilidade com Grad-CAM (5 min)

## O Problema da Caixa Preta

```
IA: "Probabilidade de pneumonia: 87%"
Médico: "ONDE você viu pneumonia?"
IA sem explicabilidade: "..." ❌
```

**Problemas:**
- Médico não pode validar
- FDA/ANVISA não aprovam
- Impossível ensinar residentes

## Grad-CAM: A Solução

**Grad-CAM** = mostra **onde** o modelo "olhou" para fazer a predição

**Como funciona:**
1. Modelo faz predição
2. Calcula gradientes da última camada convolucional
3. Gera heatmap mostrando regiões de atenção
4. Sobrepõe heatmap na imagem original

```python
def generate_gradcam(model, img, class_idx):
    # 1. Forward pass
    output = model(img)

    # 2. Backward pass
    target = output[0, class_idx]
    target.backward()

    # 3. Calcular pesos dos feature maps
    gradients = get_gradients()  # [C, H, W]
    weights = gradients.mean(axis=(1,2))  # [C]

    # 4. Weighted sum
    cam = (weights * features).sum(axis=0)  # [H, W]

    # 5. Normalizar e redimensionar
    cam = normalize(cam)  # [0, 1]
    cam = resize(cam, (224, 224))

    return cam  # Heatmap!
```

## Máscaras de Segmentação

**Threshold no heatmap = máscara binária**

```python
mask = (heatmap > 0.5).astype(uint8)  # {0, 1}
```

**Threshold adaptativo:**
- Prob > 0.7 → threshold 0.6 (mais focado)
- Prob > 0.5 → threshold 0.5 (médio)
- Prob < 0.5 → threshold 0.4 (mais amplo)

## Ground Truth vs Grad-CAM

| Aspecto | Ground Truth | Grad-CAM |
|---------|--------------|----------|
| Origem | Anotação manual (horas) | Automático (2s) |
| Exames novos? | ❌ Não | ✅ Sim |
| Custo | Alto | Zero |
| Uso | Pesquisa/validação | Produção PACS |

**Decisão:** Usamos Grad-CAM em produção porque funciona em exames novos sem anotação prévia.

---

# 4. Arquitetura do Sistema (5 min)

## Visão Geral

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
│   REST API           /generate_masks ⭐    Analysis     │
└──────────────────────────────────────────────────────────┘
```

## 3 Containers Docker

**1. Orthanc (PACS)**
```yaml
orthanc:
  image: orthancteam/orthanc:latest
  ports: ["8042:8042"]
  volumes: ["./orthanc/data:/var/lib/orthanc/db"]
```

**2. Inference API (FastAPI + TorchXRayVision)**
```yaml
inference-api:
  build: ./inference_api
  ports: ["8000:8000"]
```

**3. Jupyter (Análise)**
```yaml
jupyter:
  build: ./notebooks
  ports: ["8888:8888"]
  volumes: ["./notebooks:/home/jovyan/work"]
```

## Fluxo de Dados

```
1. DICOM → Orthanc (upload via UI)
2. Jupyter: GET /instances → lista exames
3. Jupyter: GET /instances/{id}/file → baixa DICOM
4. Jupyter: POST /generate_masks → envia para API
5. API: processa + Grad-CAM → retorna máscaras
6. Jupyter: visualiza resultados
```

---

# 5. Implementação Técnica (5 min)

## Pré-processamento DICOM

**Método oficial TorchXRayVision (adotado v1.3.0+):**

```python
def preprocess_dicom_official(dcm):
    # 1. Extrair pixels
    img = dcm.pixel_array.astype(float)

    # 2. Normalizar para HU scale [-1024, 1024]
    img = xrv.datasets.normalize(img, 255, reshape=True)

    # 3. Redimensionar 224x224
    img = cv2.resize(img, (224, 224))

    return torch.from_numpy(img).unsqueeze(0)
```

**Decisão v1.3.0+:** Método oficial como padrão (~11% melhor que anterior)

## Endpoints da API

### POST /predict
```bash
curl -X POST http://localhost:8000/predict \
  -F "dicom_file=@exam.dcm"
```
Retorna probabilidades dos 18 achados.

### POST /generate_masks ⭐ (Recomendado)
```bash
curl -X POST http://localhost:8000/generate_masks?top_n=3 \
  -F "dicom_file=@exam.dcm"
```
Retorna probabilidades + heatmaps + máscaras (Grad-CAM).

### POST /compare_preprocessing
```bash
curl -X POST http://localhost:8000/compare_preprocessing \
  -F "dicom_file=@exam.dcm"
```
Compara método anterior vs oficial (para pesquisa).

## Notebook: orthanc_analysis.ipynb

**4 Seções:**
1. **Setup:** Imports, configuração, verificação de serviços
2. **Pesquisa:** Comparação de métodos (por que oficial é melhor)
3. **Inferência:** Processa todos os DICOMs do Orthanc
4. **Máscaras:** Visualização Grad-CAM estilo TorchXRayVision

```python
# Exemplo: processar todos os exames
instances = requests.get(f"{ORTHANC_URL}/instances").json()

for instance_id in instances:
    # 1. Baixar DICOM
    dicom_bytes = requests.get(
        f"{ORTHANC_URL}/instances/{instance_id}/file"
    ).content

    # 2. Enviar para API
    result = requests.post(
        f"{API_URL}/generate_masks",
        files={"dicom_file": dicom_bytes},
        params={"top_n": 3}
    ).json()

    # 3. Visualizar
    display_results(result)
```

---

# 6. Uso Clínico e Regulamentação (5 min)

## ⚠️ AVISOS CRÍTICOS

### Este Sistema É:
- ✅ **Auxílio diagnóstico** (segunda opinião)
- ✅ **Ferramenta de triagem** (priorizar casos urgentes)
- ✅ **Suporte educacional** (ensinar residentes)

### Este Sistema NÃO É:
- ❌ **Diagnóstico automático** (decisão final é do médico)
- ❌ **Substituto do radiologista**
- ❌ **Aprovado por FDA/ANVISA** (ainda)

## Fluxo de Trabalho Clínico

```
1. Técnico → Raio-X → DICOM → Orthanc
2. Sistema → Processa → Máscaras + Probabilidades
3. Radiologista → Analisa:
   - Imagem original
   - Máscaras Grad-CAM (onde o modelo "viu")
   - Probabilidades (quão confiante)
4. Radiologista → Valida/Refuta → Laudo Final ✍️
```

**O médico é SEMPRE responsável pela decisão final!**

## Regulamentação

### FDA (USA) - Class II Medical Device
- Requer explicação das predições (✅ temos Grad-CAM)
- Validação clínica obrigatória
- Post-market surveillance

### ANVISA (Brasil) - RDC 44/2023
- Software como dispositivo médico
- Rastreabilidade das decisões (✅ temos)
- Documentação de validação clínica

### GDPR (Europa)
- "Right to explanation" (✅ Grad-CAM fornece)

## Responsabilidades do Médico

1. **Validar** predições do sistema (não confiar cegamente)
2. **Documentar** quando discordar da IA
3. **Atualizar** conhecimento sobre limitações do modelo
4. **Reportar** falsos positivos/negativos
5. **Assumir** responsabilidade legal pelo laudo final

## Limitações do Sistema

- ❌ Não detecta achados fora dos 18 treinados
- ❌ Sensível a qualidade da imagem (contraste, posicionamento)
- ❌ Pode errar em casos raros/atípicos
- ❌ Grad-CAM não é ground truth (precisão ~70-80%)
- ❌ Performance varia por patologia (pneumonia mais difícil)

## Quando NÃO Usar

- Paciente pediátrico (modelo treinado em adultos)
- Raio-X portátil (qualidade inferior)
- Imagens muito degradadas
- Casos emergenciais (não esperar pela IA)

---

# 📚 Próximos Passos

## Para Começar Agora

```bash
# 1. Clone o repositório
git clone <repo-url>
cd mini-pacs-ai

# 2. Suba os serviços
make build && make up

# 3. Verifique
make test  # Todos devem estar OK

# 4. Acesse
http://localhost:8042  # Orthanc UI
http://localhost:8000/docs  # API Swagger
http://localhost:8888  # Jupyter
```

## Para Aprofundar

- **Documentação detalhada:** [academy-detalhada/](./academy-detalhada/) (~8h de conteúdo)
- **API completa:** [API.md](./API.md)
- **Uso clínico:** [CLINICAL_USAGE.md](./CLINICAL_USAGE.md)
- **Troubleshooting:** [TESTE_API.md](./TESTE_API.md)

## Para Desenvolver

**Arquivos principais:**
```
inference_api/app/
├── main.py              # FastAPI endpoints
├── model.py             # Carrega TorchXRayVision
├── preprocess_official.py  # Pré-processamento
├── gradcam.py           # Geração de máscaras
└── schemas.py           # Pydantic models

notebooks/
└── orthanc_analysis.ipynb  # Análise completa
```

**Mudou código Python?**
```bash
make rebuild  # IMPORTANTE: restart não basta!
```

---

# 🎯 Checklist de Compreensão

Se você entendeu esta academia, deve conseguir responder:

- [ ] O que é PACS e por que é importante?
- [ ] Qual a diferença entre DICOM e JPEG?
- [ ] Como TorchXRayVision detecta patologias?
- [ ] Por que Grad-CAM é essencial em IA médica?
- [ ] Qual a arquitetura do sistema (3 containers)?
- [ ] Qual endpoint usar para gerar máscaras? (`/generate_masks`)
- [ ] Por que o método oficial de pré-processamento é melhor?
- [ ] Ground Truth vs Grad-CAM: quando usar cada um?
- [ ] O sistema substitui o radiologista? (NÃO!)
- [ ] Quais as limitações do sistema?

**Se respondeu tudo:** ✅ Você está pronto para usar o sistema!

**Se ficou dúvidas:** 📖 Consulte [academy-detalhada/](./academy-detalhada/)

---

# 📊 Referências Rápidas

**Papers:**
- Grad-CAM: https://arxiv.org/abs/1610.02391
- TorchXRayVision: https://arxiv.org/abs/2003.11968
- DenseNet: https://arxiv.org/abs/1608.06993

**Tecnologias:**
- Orthanc: https://www.orthanc-server.com/
- TorchXRayVision: https://github.com/mlmed/torchxrayvision
- FastAPI: https://fastapi.tiangolo.com/

**Datasets:**
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- Teste (Google Drive): https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view

---

**Versão:** 1.3.0+ | **Data:** 2025-11-04 | **Autor:** Wendell Barreto
**Tempo de leitura:** 30 minutos | **Documentação detalhada:** [academy-detalhada/](./academy-detalhada/)
