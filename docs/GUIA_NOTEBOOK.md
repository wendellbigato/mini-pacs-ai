# 📓 Guia de Uso do Notebook Jupyter

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0+
> **Notebook:** `orthanc_analysis.ipynb` - Análise completa do sistema

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
# orthanc_analysis.ipynb

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

# 3. Abrir orthanc_analysis.ipynb
```

### Opção 3: VS Code

```bash
# 1. Instalar extensão Jupyter no VS Code

# 2. Abrir arquivo
code notebooks/orthanc_analysis.ipynb

# 3. Selecionar kernel Python
# 4. Executar células com Shift+Enter
```

---

## 📋 O Que o Notebook Faz

### Seção 1: Setup e Configuração
- Imports (requests, pydicom, matplotlib, pandas, numpy)
- Configuração de URLs do Orthanc e API
- Funções auxiliares para processar DICOMs
- Verificação de status dos serviços

### Seção 2: Pesquisa - Escolha do Pré-processamento
🔬 **Comparação científica:**
- Testa 2 métodos de pré-processamento
- Visualiza diferenças lado a lado
- Gráficos comparativos (Anterior vs Oficial)
- **Conclusão:** Método oficial é ~11% mais preciso
- **Decisão:** Método oficial adotado como padrão

### Seção 3: Inferência Básica
📊 **Predição de achados radiológicos:**
- Processa todos os DICOMs do Orthanc
- Usa método oficial TorchXRayVision (padrão)
- Exibe imagem + top 5 achados por exame
- Tabela consolidada com todos os resultados

### Seção 4: Máscaras de Segmentação
🏥 **Localização automática via Grad-CAM:**
- Máscaras binárias geradas automaticamente
- Estilo TorchXRayVision (xray_masks.ipynb)
- Overlay com transparência (alpha=0.5)
- Mostra regiões de maior atenção do modelo
- **Importante:** Máscaras automáticas, não ground truth
- ~2-3s adicional por exame

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

## ✅ Checklist Pré-Execução

- [ ] Containers rodando (`docker compose ps`)
- [ ] Orthanc acessível (http://localhost:8042)
- [ ] API healthy (`curl http://localhost:8000/health`)
- [ ] DICOMs carregados no Orthanc (mínimo 1)
- [ ] Dependências instaladas (`pip install -r notebooks/requirements.txt`)
- [ ] Jupyter iniciado (`jupyter notebook` ou via Docker)

---

**Última atualização:** 2025-11-04 (v1.3.0+)
**Notebook:** 1 (orthanc_analysis.ipynb - análise completa)
**Compatível com:** Python 3.8+

