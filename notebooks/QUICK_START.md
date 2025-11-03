# 🚀 Quick Start - Notebook Jupyter

## ✅ Status Atual

- ✅ **Orthanc:** Rodando (porta 8042)
- ✅ **API:** Rodando (porta 8000, modelo carregado)
- ✅ **DICOMs:** 9 arquivos disponíveis no Orthanc

---

## 🎯 Executar Agora (3 passos)

### 1. Instalar Dependências
```bash
pip install -r notebooks/requirements.txt
```

### 2. Subir Jupyter
```bash
jupyter notebook notebooks/orthanc_inference.ipynb
```

### 3. No Navegador
- ✅ Notebook abrirá automaticamente
- ✅ Menu → **Cell** → **Run All**
- ✅ Aguarde processamento (~1 min para 9 DICOMs)

---

## 📊 O Que Vai Acontecer

Para cada um dos **9 DICOMs** no Orthanc, você verá:

1. **Imagem do raio-X** (lado esquerdo)
2. **Top 5 achados radiológicos** (lado direito)
3. **Metadados** (Patient ID, Data, Modalidade)

**Exemplo de saída:**
```
================================================================
Instância 1/9 - ID: abc123def456
================================================================
  → Baixando arquivo DICOM...
    Tamanho: 2891234 bytes
  → Chamando API de inferência...
    Inferência concluída

[Gráfico com imagem + probabilidades]

Metadados DICOM:
  patient_id: id_0a0c2c8f-...
  study_date: 20150828
  modality: CR
  image_shape: (2566, 2598)
```

---

## 🔧 Alternativas

### Opção A: JupyterLab (Interface moderna)
```bash
pip install jupyterlab
jupyter lab notebooks/orthanc_inference.ipynb
```

### Opção B: VS Code
```bash
code notebooks/orthanc_inference.ipynb
# Selecione kernel Python
# Shift+Enter para executar células
```

### Opção C: Google Colab
```bash
# 1. Upload do notebook para Google Drive
# 2. Abrir com Google Colab
# 3. Mudar URLs:
#    ORTHANC_URL = "http://SEU_IP:8042"
#    INFERENCE_API_URL = "http://SEU_IP:8000"
```

---

## 💡 Comandos Úteis

```bash
# Ver DICOMs disponíveis
curl http://localhost:8042/instances | jq

# Ver detalhes de um DICOM
curl http://localhost:8042/instances/<ID>/simplified-tags | jq

# Testar API manualmente
python test_predict.py /caminho/arquivo.dcm

# Adicionar mais DICOMs
open http://localhost:8042  # Clique em Upload
```

---

## 🎨 Personalizar Notebook

### Processar apenas 1 DICOM (teste rápido)
Modifique a célula 10:
```python
for idx, instance_id in enumerate(instances[:1], 1):  # Apenas primeiro
```

### Mostrar top 10 achados (em vez de 5)
Modifique a função `display_image_and_predictions`:
```python
top_5 = dict(list(probs.items())[:10])  # Mudar 5 para 10
```

### Salvar gráficos como PNG
Adicione ao final da função `display_image_and_predictions`:
```python
plt.savefig(f"resultado_{instance_id[:8]}.png", dpi=300)
```

---

## ⚡ Comando de Uma Linha

```bash
pip install -r notebooks/requirements.txt && jupyter notebook notebooks/orthanc_inference.ipynb
```

---

**Pronto para começar! Execute o comando acima. 🚀**

