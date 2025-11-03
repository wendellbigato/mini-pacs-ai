# 📓 Guia de Uso dos Notebooks Jupyter

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0
> **Notebooks disponíveis:**
> - `orthanc_inference.ipynb` - Integração básica Orthanc → API
> - `comparison_analysis.ipynb` - **Análise completa + Máscaras Grad-CAM** (Recomendado)

---

## ✅ Pré-requisitos

### 1. Serviços Rodando
```bash
# Verifique se os containers estão ativos
docker compose ps

# Devem estar UP:
# - orthanc (porta 8042)
# - inference-api (porta 8000)

# Se não estiverem rodando:
docker compose up -d
```

### 2. DICOMs no Orthanc

**O notebook processa DICOMs já armazenados no Orthanc.**

Para adicionar DICOMs:
1. Acesse: http://localhost:8042
2. Clique em **"Upload"** no menu superior
3. Selecione arquivos `.dcm` do seu computador
4. Aguarde o upload concluir

**Dataset de teste:**
https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

---

## 🚀 Como Executar o Notebook

### Opção 1: Jupyter Notebook (Recomendado)

```bash
# 1. Instalar dependências
pip install -r notebooks/requirements.txt

# Ou com conda:
conda install --file notebooks/requirements.txt

# 2. Subir Jupyter
cd notebooks
jupyter notebook

# 3. No navegador, abrir:
# orthanc_inference.ipynb

# 4. Executar todas as células:
# Menu → Cell → Run All
```

### Opção 2: JupyterLab

```bash
# 1. Instalar JupyterLab
pip install jupyterlab

# 2. Subir JupyterLab
cd notebooks
jupyter lab

# 3. Abrir orthanc_inference.ipynb
```

### Opção 3: VS Code

```bash
# 1. Instalar extensão Jupyter no VS Code

# 2. Abrir arquivo
code notebooks/orthanc_inference.ipynb

# 3. Selecionar kernel Python
# 4. Executar células com Shift+Enter
```

---

## 📋 O Que o Notebook Faz

### Célula 1-2: Setup
- Imports (requests, pydicom, matplotlib, pandas)
- Configuração de URLs do Orthanc e API

### Célula 3-4: Funções Auxiliares
```python
list_instances()           # Lista DICOMs no Orthanc
download_dicom(id)         # Baixa DICOM específico
call_inference_api(bytes)  # Envia para /predict
display_image_and_predictions()  # Plota resultados
```

### Célula 5-6: Verificação de Status
✅ Testa conectividade com:
- Orthanc (http://localhost:8042)
- API de Inferência (http://localhost:8000)

### Célula 7-8: Listagem
📋 Lista todos os DICOMs armazenados no Orthanc

### Célula 9-10: Processamento Automático
🔄 **Loop principal:**
```
Para cada DICOM no Orthanc:
  1. Baixa o arquivo
  2. Envia para /predict
  3. Exibe imagem + top 5 achados
  4. Mostra metadados
```

### Célula 11-12: Análise Consolidada
📊 Cria tabela comparativa:
- Instância vs Top 3 achados
- Formato pandas DataFrame

### Célula 13-14: Teste com Arquivo Local
💾 Opcional: Testar com DICOM local sem usar Orthanc

---

## 🎯 Resultado Esperado

Após executar todas as células, você verá:

### 1. Status dos Serviços
```
✓ Orthanc está respondendo
  Versão: 1.12.x
✓ API de Inferência está respondendo
  Status: healthy
  Modelo carregado: True
```

### 2. Lista de Instâncias
```
Total de instâncias DICOM no Orthanc: 3
IDs das instâncias:
  1. abc123...
  2. def456...
  3. ghi789...
```

### 3. Para Cada DICOM
📊 **Gráfico duplo:**
- **Esquerda:** Imagem do raio-X (grayscale)
- **Direita:** Barra horizontal com top 5 achados

```
Top 5 Achados Radiológicos:
Effusion              0.663 ████████████████████████████████
Lung Opacity          0.661 ████████████████████████████████
Enlarged Cardio...    0.659 ███████████████████████████████
Cardiomegaly          0.648 ██████████████████████████████
Atelectasis           0.646 ██████████████████████████████
```

### 4. Metadados
```
Metadados DICOM:
  patient_id: id_0a0c2c8f-...
  study_date: 20150828
  modality: CR
  image_shape: (2566, 2598)
```

### 5. Tabela Consolidada
```
instance_id    Effusion  Lung Opacity  Enlarged...
abc123...      0.663     0.661         0.659
def456...      0.721     0.698         0.702
ghi789...      0.554     0.579         0.601
```

---

## 🐛 Troubleshooting

### Erro: "Nenhuma instância encontrada"
**Causa:** Orthanc está vazio

**Solução:**
```bash
# Adicione DICOMs via web UI
open http://localhost:8042

# Ou via linha de comando
curl -X POST http://localhost:8042/instances \
  --data-binary @arquivo.dcm \
  -H "Content-Type: application/dicom"
```

### Erro: "Erro ao conectar com Orthanc"
**Causa:** Serviço não está rodando

**Solução:**
```bash
docker compose up -d
sleep 5
make test
```

### Erro: "API de Inferência não responde"
**Causa:** Container inference-api parado ou modelo não carregado

**Solução:**
```bash
# Verificar logs
docker compose logs inference-api

# Rebuild se necessário
make rebuild

# Testar saúde
curl http://localhost:8000/health
```

### Erro: ModuleNotFoundError
**Causa:** Dependências não instaladas

**Solução:**
```bash
pip install -r notebooks/requirements.txt

# Ou instalar individualmente
pip install requests pydicom matplotlib pandas jupyter
```

### Erro: Kernel morreu / Crash
**Causa:** Memória insuficiente ou imagem DICOM muito grande

**Solução:**
1. Reiniciar kernel (Kernel → Restart)
2. Processar DICOMs um por um
3. Aumentar memória do Docker (Settings → Resources)

---

## 💡 Dicas de Uso

### Executar Célula por Célula
```
Shift + Enter  # Executa célula atual e vai para próxima
Ctrl + Enter   # Executa célula atual e fica nela
```

### Modificar URLs
Se os serviços estiverem em outras portas:
```python
ORTHANC_URL = "http://localhost:8042"        # Mudar porta se necessário
INFERENCE_API_URL = "http://localhost:8000"  # Mudar porta se necessário
```

### Processar Apenas 1 DICOM
```python
# Modifique a célula 10:
for idx, instance_id in enumerate(instances[:1], 1):  # Apenas primeiro
    # ... resto do código
```

### Salvar Resultados
```python
# Adicione ao final da célula 10:
import json

results = {
    "instance_id": instance_id,
    "predictions": predictions
}

with open(f"results_{instance_id[:8]}.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Exportar Imagens
```python
# Ao final da função display_image_and_predictions():
plt.savefig(f"resultado_{title}.png", dpi=300, bbox_inches="tight")
```

---

## 📊 Casos de Uso

### 1. Análise Rápida de Múltiplos Exames
```bash
# Upload batch de DICOMs via Orthanc UI
# Execute notebook completo
# Compare resultados na tabela consolidada
```

### 2. Validação de Modelo
```bash
# Envie DICOMs com diagnósticos conhecidos
# Compare predições do modelo com ground truth
# Analise acurácia por achado
```

### 3. Demo para Cliente
```bash
# Prepare DICOMs de exemplo
# Execute notebook ao vivo
# Mostre visualizações e probabilidades
```

---

## 🔗 Recursos Adicionais

- **Orthanc API Docs:** https://book.orthanc-server.com/users/rest.html
- **PyDICOM Guide:** https://pydicom.github.io/pydicom/stable/tutorials/
- **Matplotlib Gallery:** https://matplotlib.org/stable/gallery/index.html
- **Jupyter Tips:** https://jupyter-notebook.readthedocs.io/

---

## 🆕 Notebook Avançado: comparison_analysis.ipynb (v1.3.0)

### O que oferece:

Este notebook completo oferece 4 partes de análise:

#### PARTE 1: Comparação de Pré-processamento
- Compara método atual vs oficial TorchXRayVision
- Visualizações lado-a-lado das probabilidades
- Gráficos de diferenças (verde/laranja/vermelho)
- Decisão automatizada (qual método usar)

#### PARTE 2: Visualização Grad-CAM
- Heatmaps de atenção para interpretação visual
- Bounding boxes nos achados detectados
- Visualização profissional estilo CAD
- Processa TODOS os exames do Orthanc

#### PARTE 3: Análise Consolidada
- Estatísticas de todas as instâncias
- Distribuição de diferenças (histograma + boxplot)
- Top achados consolidados

#### **PARTE 4: Máscaras de Segmentação Grad-CAM** ⭐ (NOVO)
- Visualização estilo [TorchXRayVision oficial](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)
- Máscaras binárias geradas automaticamente
- Overlay de máscaras sobre imagem original (alpha=0.5)
- Layout: `[Original] [Máscara 1] [Máscara 2] ...`
- **Diferença importante:** xray_masks.ipynb mostra ground truth (anotações manuais), nossa implementação **gera máscaras via Grad-CAM**

### Como usar:

**Via Container Docker (Recomendado):**
```bash
# 1. Subir todos os serviços (incluindo Jupyter)
docker compose up -d

# 2. Acessar Jupyter
# URL exibida nos logs: http://localhost:8888
docker compose logs jupyter | grep token

# 3. Abrir notebook
http://localhost:8888/notebooks/comparison_analysis.ipynb

# 4. Executar células na ordem
```

**Localmente:**
```bash
# 1. Instalar dependências
pip install -r notebooks/requirements.txt

# 2. Modificar URLs no notebook
# Trocar:
#   ORTHANC_URL = "http://orthanc:8042"
#   API_URL = "http://inference-api:8000"
# Para:
#   ORTHANC_URL = "http://localhost:8042"
#   API_URL = "http://localhost:8000"

# 3. Subir Jupyter
cd notebooks
jupyter notebook

# 4. Abrir comparison_analysis.ipynb
```

### Para Médicos Radiologistas:

**PARTE 4 é a mais relevante clinicamente:**
- Mostra máscaras de segmentação das regiões suspeitas
- Visualização familiar (estilo TorchXRayVision)
- **IMPORTANTE:** Máscaras são geradas automaticamente via Grad-CAM
- **NÃO são** ground truth (anotações manuais)
- Use como **auxílio diagnóstico**, não como diagnóstico definitivo

**Limitações a considerar:**
- Precisão: ~70-80% vs ground truth
- Pode ter falsos positivos/negativos
- Decisão final sempre do médico

Ver guia completo: `CLINICAL_USAGE.md`

---

## ✅ Checklist Pré-Execução

- [ ] Containers rodando (`docker compose ps`)
- [ ] Orthanc acessível (http://localhost:8042)
- [ ] API healthy (`curl http://localhost:8000/health`)
- [ ] DICOMs carregados no Orthanc (mínimo 1)
- [ ] Dependências instaladas (`pip install -r notebooks/requirements.txt`)
- [ ] Jupyter iniciado (`jupyter notebook` ou via Docker)

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Notebooks:** 2 (orthanc_inference.ipynb, comparison_analysis.ipynb)
**Compatível com:** Python 3.8+

