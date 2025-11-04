# 🧪 Testes da API - Mini PACS AI

> **Versão:** 1.3.0+
> **Autor:** Wendell Barreto

---

## 📁 Scripts de Teste Disponíveis

### 1. test_predict.py
**Testa endpoint básico de predição**

```bash
python tests/test_predict.py <arquivo.dcm>
```

**O que faz:**
- Envia DICOM para `/predict`
- Retorna probabilidades dos 18 achados
- Mostra top 10 com barras visuais
- Exibe metadados DICOM

**Exemplo:**
```bash
python tests/test_predict.py ~/Downloads/chest_xray.dcm
```

---

### 2. test_generate_masks.py ⭐ (Recomendado)
**Testa endpoint de geração de máscaras Grad-CAM**

```bash
python tests/test_generate_masks.py <arquivo.dcm> [top_n]
```

**O que faz:**
- Envia DICOM para `/generate_masks`
- Gera máscaras Grad-CAM automáticas
- Retorna heatmaps + máscaras binárias
- Método oficial TorchXRayVision (v1.3.0+)

**Parâmetros:**
- `arquivo.dcm` - Caminho para DICOM (obrigatório)
- `top_n` - Número de máscaras a gerar (padrão: 3)

**Exemplos:**
```bash
# Top 3 máscaras (padrão)
python tests/test_generate_masks.py ~/Downloads/chest_xray.dcm

# Top 5 máscaras
python tests/test_generate_masks.py ~/Downloads/chest_xray.dcm 5
```

**Saída esperada:**
```
✅ Geração de máscaras bem-sucedida!

📊 Probabilidades:
 1. Effusion                      66.3% ████████████████████
 2. Lung Opacity                  66.1% ████████████████████
...

🎭 Máscaras Grad-CAM Geradas: 3
1. Effusion                      66.3%
   ✓ Heatmap: Sim
   ✓ Máscara: Sim
...
```

---

### 3. test_compare_preprocessing.py
**Compara método anterior vs oficial**

```bash
python tests/test_compare_preprocessing.py <arquivo.dcm>
```

**O que faz:**
- Envia DICOM para `/compare_preprocessing`
- Processa com ambos métodos
- Calcula diferenças absolutas
- Mostra estatísticas de comparação
- Recomenda qual método usar

**Exemplo:**
```bash
python tests/test_compare_preprocessing.py ~/Downloads/chest_xray.dcm
```

**Saída esperada:**
```
📊 Estatísticas da Comparação:
  Diferença Média:  0.1132 (11.32%)
  Diferença Máxima: 0.1609 (16.09%)
  Desvio Padrão:    0.0411

⚠️  ATENÇÃO: Diferença > 5% - Considere usar método oficial

🎯 DECISÃO TÉCNICA:
   → Use método oficial (use_official_preprocessing=True)
   → Diferença justifica mudança de padrão
```

---

## 🚀 Pré-requisitos

### 1. Serviços Rodando

```bash
# Verificar status
docker compose ps

# Se não estiverem rodando
docker compose up -d

# Aguardar inicialização (~10s)
sleep 10
```

**Serviços necessários:**
- ✅ orthanc (porta 8042)
- ✅ inference-api (porta 8000)

### 2. Arquivo DICOM de Teste

**Opção 1: Dataset de teste (Google Drive)**
```bash
# Download via navegador
https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view

# Extrair
unzip ChestXray-NIHCC-sample.zip
```

**Opção 2: Upload no Orthanc**
1. Acesse http://localhost:8042
2. Clique em "Upload"
3. Selecione arquivos .dcm
4. Use GET /instances/{id}/file para baixar

### 3. Dependências Python

```bash
pip install requests
```

---

## 📊 Testes Via Makefile

### Teste Rápido (Serviços)
```bash
make test
```
Verifica se Orthanc e API estão respondendo.

**Saída esperada:**
```
✓ Orthanc está respondendo em http://localhost:8042
✓ API está respondendo em http://localhost:8000/docs
```

### Teste de Saúde da API
```bash
make test-health
```
Verifica saúde e labels do modelo.

**Saída esperada:**
```
{
  "status": "healthy",
  "model_loaded": true
}

📊 Labels detectáveis pelo modelo:
18
```

---

## 🐛 Troubleshooting

### Erro: "Não foi possível conectar à API"

```bash
# 1. Verificar se serviços estão rodando
docker compose ps

# 2. Verificar logs
docker compose logs inference-api

# 3. Restart se necessário
docker compose restart inference-api

# 4. Rebuild se mudou código
make rebuild
```

### Erro: "Timeout na requisição (>60s)"

**Causas:**
- Primeira requisição demora mais (carregamento do modelo)
- DICOM muito grande
- Memória insuficiente

**Solução:**
```bash
# Aguardar primeira requisição completar
# Ou aumentar timeout no script Python
```

### Erro 422: "Unprocessable Entity"

**Causa:** Arquivo não é DICOM válido

**Solução:**
```bash
# Verificar extensão
file arquivo.dcm

# Deve retornar: DICOM medical imaging data
```

### Erro 500: "Internal Server Error"

**Causas comuns:**
- Modelo não carregou
- Erro no pré-processamento
- DICOM corrompido

**Debug:**
```bash
# Ver logs detalhados
docker compose logs -f inference-api

# Verificar saúde
curl http://localhost:8000/health
```

---

## 📈 Comparação dos Endpoints

| Endpoint | Uso | Tempo | Retorno |
|----------|-----|-------|---------|
| `/predict` | Predição básica | ~2s | Probabilidades |
| `/generate_masks` ⭐ | Produção (recomendado) | ~5s | Probabilidades + Máscaras |
| `/predict_with_heatmap` | Legacy | ~5s | Igual ao `/generate_masks` |
| `/compare_preprocessing` | Pesquisa/validação | ~7s | Comparação de métodos |

---

## 💡 Dicas

### Teste com Múltiplos DICOMs

```bash
# Loop em uma pasta
for dcm in ~/Downloads/dicoms/*.dcm; do
    echo "Testando: $dcm"
    python tests/test_predict.py "$dcm"
    echo "---"
done
```

### Salvar Resultados

```bash
python tests/test_predict.py ~/Downloads/exam.dcm > results.txt 2>&1
```

### Uso em Scripts

```python
# Exemplo de integração
import subprocess

result = subprocess.run(
    ["python", "tests/test_predict.py", "exam.dcm"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Teste passou")
else:
    print("❌ Teste falhou")
```

---

## 🔗 Referências

- **Documentação API:** [../docs/API.md](../docs/API.md)
- **Troubleshooting:** [../docs/TESTE_API.md](../docs/TESTE_API.md)
- **Notebook:** [../notebooks/orthanc_analysis.ipynb](../notebooks/orthanc_analysis.ipynb)
- **Swagger UI:** http://localhost:8000/docs (quando API rodando)

---

**Última atualização:** 2025-11-04 | **Versão:** 1.3.0+
