# Como Testar a API /predict (Corrigido)

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

**Data da correção:** 2025-11-02
**Status:** ✅ Totalmente corrigido e testado
