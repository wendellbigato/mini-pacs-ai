# Como Testar a API - Guia Completo

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0+
> **Endpoints:** `/predict`, `/generate_masks` ⭐, `/predict_with_heatmap` (legacy), `/compare_preprocessing`, `/masks`, `/validate_masks`

## ✅ Problemas Resolvidos

### Erro 1: `422 Unprocessable Entity`
**Mensagem:** `Expected UploadFile, received: <class 'str'>`

**Correção:**
- Adicionado `media_type="application/dicom"` no parâmetro `File()` do endpoint `/predict`
- Removido atributo `version` obsoleto do `docker-compose.yml`

### Erro 2: `500 Internal Server Error`
**Mensagem:** `metadata.image_shape - Input should be a valid string [type=string_type, input_value=(2619, 2000), input_type=tuple]`

**Correção:**
- Convertido `image_shape` de tupla para string no `preprocess.py:71`
- Agora retorna `"(2619, 2000)"` em vez de `(2619, 2000)`

**Status:** ✅ Ambos corrigidos e testados

---

## 🧪 Métodos de Teste

### 1. Via Swagger UI (Recomendado)

```bash
# 1. Acesse no navegador:
http://localhost:8000/docs

# 2. Expanda "POST /predict"
# 3. Clique em "Try it out"
# 4. Clique em "Choose File" e selecione seu arquivo .dcm
# 5. Clique em "Execute"
```

**Resposta esperada:**
```json
{
  "probabilities": {
    "Pleural Effusion": 0.567,
    "Cardiomegaly": 0.456,
    ...
  },
  "metadata": {
    "patient_id": "123456",
    "study_date": "20240101",
    "modality": "CR"
  }
}
```

---

### 2. Via Script Python

```bash
# Usar o script de teste criado
python test_predict.py /caminho/para/seu/arquivo.dcm

# Exemplo:
python test_predict.py ~/Downloads/chest_xray.dcm
```

O script mostra:
- ✅ Status da predição
- 📊 Top 10 achados radiológicos com barra de progresso
- 📋 Metadados DICOM

---

### 3. Via cURL

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "dicom_file=@/caminho/para/arquivo.dcm" \
  | jq
```

---

## 📁 Onde Conseguir Arquivos DICOM de Teste?

### Dataset Oficial do Desafio
https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

### Datasets Públicos
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- MIMIC-CXR: https://physionet.org/content/mimic-cxr/2.0.0/

---

## 🔍 Verificação de Saúde

Antes de testar, certifique-se que a API está saudável:

```bash
# Health check
curl http://localhost:8000/health

# Resposta esperada:
# {"status":"healthy","model_loaded":true}
```

---

## 🐛 Troubleshooting

### Erro: Connection refused
```bash
# Verifique se os containers estão rodando
docker compose ps

# Se não estiverem, suba-os
docker compose up -d
```

### Erro: Model not loaded
```bash
# Verifique os logs da API
docker compose logs inference-api

# Reinicie o container
docker compose restart inference-api
```

### Ainda recebe erro 422 ou 500?

**IMPORTANTE:** Após modificar o código Python, você DEVE fazer rebuild:

```bash
# Pare os containers
docker compose down

# Reconstrua a imagem da API (aplica mudanças no código)
docker compose build inference-api

# Suba os containers novamente
docker compose up -d

# Aguarde ~10 segundos para o modelo carregar
# Verifique saúde
curl http://localhost:8000/health
```

⚠️ **Apenas `docker compose restart` NÃO funciona** - precisa rebuild!

---

## 📝 Arquivos Modificados

1. **inference_api/app/main.py:70**
   - Adicionado `media_type="application/dicom"` ao parâmetro File
   - Corrige erro 422

2. **inference_api/app/preprocess.py:71**
   - Convertido `image_shape` de tupla para string: `str(dcm.pixel_array.shape)`
   - Corrige erro 500

3. **docker-compose.yml:1**
   - Removido `version: '3.8'` (obsoleto no Docker Compose v2+)

4. **test_predict.py** (novo)
   - Script Python para testar o endpoint facilmente

5. **TESTE_API.md** (novo)
   - Documentação completa de troubleshooting

---

## 🆕 Endpoints de Visualização

### 1. POST /generate_masks ⭐ - Máscaras Grad-CAM (Recomendado v1.3.0+)

**O que faz:**
- Predição de achados radiológicos
- Gera máscaras binárias de segmentação Grad-CAM
- Método oficial TorchXRayVision como padrão

**Via Swagger UI:**
```bash
# 1. Acesse: http://localhost:8000/docs
# 2. Expanda "POST /generate_masks"
# 3. Try it out
# 4. Upload DICOM
# 5. Parâmetros opcionais:
#    - top_n: 3 (número de máscaras - padrão mais focado)
#    - use_official_preprocessing: true (padrão)
# 6. Execute
```

**Via curl:**
```bash
curl -X POST "http://localhost:8000/generate_masks?top_n=3" \
  -H "Content-Type: multipart/form-data" \
  -F "dicom_file=@exemplo.dcm"
```

**Resposta:**
```json
{
  "probabilities": { ... },
  "heatmaps": [
    {
      "pathology": "Cardiomegaly",
      "probability": 0.78,
      "heatmap_base64": "data:image/png;base64,...",
      "mask_base64": "data:image/png;base64,..."
    }
  ],
  "metadata": { ... }
}
```

**Uso:**
- Ver máscaras no notebook: `orthanc_analysis.ipynb` Seção 4
- Heatmap: mostra intensidade da atenção (cores)
- Máscara: segmentação binária da região de atenção
- **Decisão:** Método oficial adotado após pesquisa (~11% diferença)

---

### 2. POST /predict_with_heatmap - Legacy (compatibilidade)

**Endpoint legado** mantido para compatibilidade. Use `/generate_masks` ao invés.

**Diferenças:**
- top_n padrão: 5 (menos focado)
- Mantido para código existente

---

### 3. POST /compare_preprocessing - Comparar Métodos (Pesquisa)

**O que faz:**
- Compara pré-processamento atual vs oficial TorchXRayVision
- Retorna probabilidades de ambos métodos
- Calcula diferenças e estatísticas

**Via curl:**
```bash
curl -X POST "http://localhost:8000/compare_preprocessing" \
  -F "dicom_file=@exemplo.dcm"
```

**Resposta:**
```json
{
  "current_method": { "Effusion": 0.66, ... },
  "official_method": { "Effusion": 0.50, ... },
  "absolute_differences": { "Effusion": 0.16, ... },
  "statistics": {
    "mean_difference": 0.1132,
    "max_difference": 0.1609,
    "std_difference": 0.0411
  },
  "preprocessing_stats": { ... }
}
```

**Uso:**
- Validar decisão de usar método oficial (~11% diferença confirmada)
- Ver análise completa no notebook: `orthanc_analysis.ipynb` Seção 2

---

### 3. GET /masks - Máscaras Ground Truth (Opcional)

**O que faz:**
- Retorna máscaras ground truth do NIH Dataset
- Usado para validação científica (não produção)
- Requer NIH_DATASET_PATH configurado

**Via curl:**
```bash
# Obter amostra específica
curl "http://localhost:8000/masks?sample_idx=0"

# Buscar por patologia
curl "http://localhost:8000/masks?pathology=Cardiomegaly"
```

**Resposta:**
```json
{
  "dataset_available": false,
  "message": "NIH Dataset não configurado..."
}
```

**Nota:** NIH Dataset **NÃO é necessário** para uso normal. Apenas para validação científica.

---

### 4. POST /validate_masks - Validar Grad-CAM vs Ground Truth (Opcional)

**O que faz:**
- Compara predições Grad-CAM com máscaras ground truth
- Calcula IoU (Intersection over Union)
- Avalia precisão: excellent/good/fair/poor

**Via curl:**
```bash
curl -X POST "http://localhost:8000/validate_masks?nih_sample_idx=0" \
  -F "dicom_file=@exemplo.dcm"
```

**Resposta:**
```json
{
  "dataset_available": false,
  "message": "NIH Dataset não configurado..."
}
```

**Nota:** Requer NIH Dataset. Ver `README.md` seção "Validação Científica" para configurar.

---

## 📊 Fluxo de Uso Recomendado

### Para Uso Clínico (Médico Radiologista):

1. **Upload DICOM no Orthanc** → automático via PACS
2. **Chamar `/generate_masks`** ⭐ → obtém probabilidades + máscaras (método oficial)
3. **Visualizar no notebook** → `orthanc_analysis.ipynb` Seção 4
4. **Analisar resultados** → médico emite laudo final

### Para Validação/Pesquisa:

1. **Configurar NIH Dataset** (opcional)
2. **Chamar `/compare_preprocessing`** → decidir método
3. **Chamar `/validate_masks`** → medir precisão (IoU)
4. **Ajustar thresholds** → melhorar performance

---

## 📚 Documentação Complementar

- **Uso Clínico:** Ver `CLINICAL_USAGE.md` (guia completo para médicos)
- **Notebooks:** Ver `GUIA_NOTEBOOK.md` (como usar Jupyter)
- **Changelog:** Ver `CHANGELOG.md` v1.3.0 (todas as mudanças)
- **README:** Ver seção "Uso Clínico" (comparação Grad-CAM vs Ground Truth)

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Status:** ✅ Todos endpoints funcionando
