# Módulo 6: Discovery e Insights de Desenvolvimento

> **[← Voltar para Academia Mini PACS AI](../ACADEMY.md)**

**Duração estimada:** 1-2 horas
**Pré-requisitos:** Módulo 1-5 (todos os módulos anteriores)

---

## 6.1 Desafios Encontrados

### 1. Erro 422: Media Type DICOM

**Problema inicial:**
```bash
curl -F "dicom_file=@exam.dcm" http://localhost:8000/predict
→ 422 Unprocessable Entity: Expected UploadFile, received <class 'str'>
```

**Causa:**
- FastAPI não reconhecia DICOM como formato válido
- `File()` sem `media_type` aceitava apenas formatos comuns

**Solução:**
```python
# Antes
async def predict(dicom_file: UploadFile = File(...)):

# Depois
async def predict(
    dicom_file: UploadFile = File(..., media_type="application/dicom")
):
```

**Aprendizado:**
> DICOM tem media type específico (`application/dicom`) que precisa ser explicitamente declarado.

### 2. Erro 500: image_shape como tupla

**Problema:**
```python
metadata = {
    "image_shape": (2619, 2000)  # Tupla
}
→ 500 Internal Server Error: Expected string, received tuple
```

**Causa:**
- Pydantic schema esperava `str`
- `pixel_array.shape` retorna `tuple`

**Solução:**
```python
# preprocess.py linha 71
metadata.image_shape = str(dcm.pixel_array.shape)
# Retorna "(2619, 2000)" em vez de (2619, 2000)
```

**Aprendizado:**
> Sempre validar tipos antes de retornar em API (Pydantic ajuda mas não é mágico).

### 3. Rebuild vs Restart

**Confusão inicial:**
```bash
# Modificar código Python
# Apenas restart (NÃO FUNCIONA!)
docker compose restart inference-api
→ Código antigo ainda rodando
```

**Motivo:**
- `restart` apenas para/inicia container existente
- Não reconstrói a imagem Docker

**Solução correta:**
```bash
# Sequência correta após modificar código
docker compose down
docker compose build inference-api
docker compose up -d
```

**Aprendizado:**
> Mudanças em código Python dentro do container exigem rebuild da imagem.

**Exceção:** Jupyter com volume montado
```yaml
jupyter:
  volumes:
    - ./notebooks:/home/jovyan/work
# Notebooks são editados diretamente, sem rebuild!
```

### 4. Pré-processamento: Qual método usar?

**Dilema:**
- TorchXRayVision tem método oficial
- Código inicial usava normalização simples
- Diferença de 11% nas probabilidades!

**Investigação:**
```python
# Teste comparativo (PARTE 1 do notebook)
diff = abs(probs_official - probs_current)
print(f"Mean difference: {diff.mean():.4f}")
# Output: 0.1132

if diff.mean() > 0.05:
    print("⚠️ Usar método oficial!")
```

**Decisão:**
> Sempre usar método oficial TorchXRayVision (`xrv.datasets.normalize`) porque o modelo foi treinado com ele.

**Documentação:**
- Comparação completa em `CHANGELOG.md` v1.2.0
- Notebook PARTE 1 demonstra diferença

### 5. Grad-CAM vs Ground Truth (Maior Insight!)

**Confusão inicial do usuário:**
> "Por que o notebook oficial TorchXRayVision não usa Grad-CAM?"

**Investigação:**
- Notebook `xray_masks.ipynb` mostra máscaras ground truth
- Nosso sistema gera máscaras via Grad-CAM
- São coisas **completamente diferentes**!

**Diferença fundamental:**

| TorchXRayVision xray_masks.ipynb | Mini PACS AI |
|----------------------------------|--------------|
| Mostra ground truth (anotações manuais) | Gera máscaras Grad-CAM (automáticas) |
| Dataset estático (NIH) | Exames novos do PACS |
| Educação/validação | Produção clínica |

**Decisão de design:**
> Para uso clínico PACS, Grad-CAM é a única abordagem viável porque funciona em exames novos sem anotação manual.

**Documentação criada:**
- `CLINICAL_USAGE.md` (400+ linhas explicando)
- README seção "Uso Clínico"
- Tabela comparativa com 6 critérios

**Aprendizado:**
> Explicabilidade em produção ≠ Validação em pesquisa. Cada contexto exige abordagem diferente.

## 6.2 Decisões de Arquitetura

### 1. Docker Compose (não Kubernetes)

**Alternativas consideradas:**
- ❌ Kubernetes - overkill para projeto educacional
- ❌ Docker Swarm - mais complexo
- ✅ Docker Compose - simples, suficiente

**Justificativa:**
> Para desenvolvimento local e demonstração, Docker Compose oferece melhor custo-benefício (simplicidade vs features).

### 2. Container Jupyter Dedicado

**Alternativas:**
1. Jupyter local (fora Docker)
2. Jupyter dentro da API
3. Jupyter em container separado ✅

**Escolha:** Container separado

**Vantagens:**
- ✅ Isolamento (mudanças na API não afetam notebooks)
- ✅ Volume montado (edição direta sem rebuild)
- ✅ Reprodutibilidade (mesmo ambiente para todos)

**Documentação:** `JUPYTER_IMPLEMENTADO.md`

### 3. FastAPI (não Flask)

**Por que FastAPI?**
- ✅ Docs automática (Swagger UI)
- ✅ Validação Pydantic
- ✅ Async nativo
- ✅ Performance superior
- ✅ Type hints modernos

**Comparação:**

| Feature | Flask | FastAPI |
|---------|-------|---------|
| Docs automática | ❌ (manual) | ✅ Swagger |
| Validação | ❌ (manual) | ✅ Pydantic |
| Performance | Moderada | Alta |
| Async | ❌ (addon) | ✅ Nativo |
| Learning curve | Baixa | Média |

### 4. SQLite no Orthanc (não PostgreSQL)

**Orthanc suporta:**
- SQLite (padrão)
- PostgreSQL (plugin)
- MySQL (plugin)

**Escolha:** SQLite

**Justificativa:**
- ✅ Suficiente para <10.000 estudos
- ✅ Zero configuração
- ✅ Backup = copiar arquivo
- ❌ Produção grande (>50k estudos) → PostgreSQL

### 5. CPU (não GPU)

**Decisão:**
> Rodar em CPU por padrão, GPU opcional.

**Motivos:**
- ✅ Acessível (qualquer desenvolvedor)
- ✅ Inferência aceitável (~2s)
- ✅ Sem dependências CUDA
- ✅ Deploy mais fácil

**GPU disponível:**
```python
# Detecta automaticamente
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
```

## 6.3 Evolução do Projeto

### Cronologia de Versões

**v1.0.0** (Release Inicial)
```
✅ Orthanc funcionando
✅ API /predict básica
✅ Docker Compose funcional
```

**v1.0.1** (Bug Fixes)
```
🐛 Fix: Erro 422 (media type DICOM)
🐛 Fix: Erro 500 (image_shape)
🐛 Fix: docker-compose.yml version obsoleto
📖 Criado TESTE_API.md
```

**v1.2.0** (Grad-CAM + Preprocessing)
```
✨ Novo: /predict_with_heatmap
✨ Novo: /compare_preprocessing
✨ Novo: Heatmaps Grad-CAM
📖 Expandido GUIA_NOTEBOOK.md
📖 Documentação científica (papers)
```

**v1.3.0** (Máscaras + Validação)
```
✨ Novo: Máscaras binárias automáticas
✨ Novo: /masks (ground truth opcional)
✨ Novo: /validate_masks (IoU)
✨ Novo: Threshold adaptativo
📖 Criado CLINICAL_USAGE.md (400+ linhas)
📖 Criado DOCS_INDEX.md (hub de navegação)
📖 Expandido README (seção clínica)
📖 CHANGELOG completo v1.3.0
```

**v1.3.0+** (Método Oficial + Unificação) ⭐ **ATUAL**
```
🔬 Pesquisa: Método oficial vs anterior (~11% diferença)
✅ Decisão: Método oficial adotado como padrão
✨ Novo: /generate_masks (endpoint recomendado)
📓 Unificado: orthanc_analysis.ipynb (4 seções didáticas)
📖 Documentação reorganizada (método oficial explicado)
⚡ Compatível: /predict_with_heatmap mantido (legacy)
```

### Features Implementadas vs Planejadas

**Implementado ✅:**
- [x] PACS Orthanc
- [x] API de Inferência
- [x] Predições multi-label
- [x] Grad-CAM heatmaps
- [x] Máscaras de segmentação
- [x] Comparação de pré-processamento
- [x] Validação científica (IoU)
- [x] Notebooks interativos
- [x] Documentação completa

**Planejado (baixa prioridade):**
- [ ] GPU support automático
- [ ] Batch processing
- [ ] AWS S3 storage
- [ ] Cache de predições
- [ ] Autenticação Orthanc
- [ ] Dashboard web

**Documentado em:** `docs/plans/extras-futuras.md`

## 6.4 Lições Aprendidas

### Técnicas

**1. DICOM é complexo**
- Não é apenas "imagem"
- Metadados são parte integral
- Normalização importa muito

**2. Pré-processamento é crítico**
- 11% de diferença entre métodos
- Sempre usar método do modelo original
- Documentar claramente

**3. Explicabilidade é essencial**
- IA sem explicação = não utilizável clinicamente
- Grad-CAM é "good enough"
- Ground truth só para validação

**4. Docker facilita reprodutibilidade**
- Sem "works on my machine"
- Containers isolam dependências
- Compose simplifica orquestração

### Científicas

**1. Transfer Learning funciona**
- Não é necessário treinar do zero
- Modelos TorchXRayVision são robustos
- Fine-tuning é opcional

**2. Multi-label ≠ Multi-class**
- Raio-X pode ter múltiplos achados
- Sigmoid (não Softmax) nas saídas
- Thresholds independentes

**3. Métricas de segmentação**
- IoU é padrão-ouro
- Dice é alternativa
- ~70% IoU é razoável para Grad-CAM

### Documentação

**1. Documentação é código**
- Tão importante quanto implementação
- Organização por persona (médico, dev, pesquisador)
- Índice é essencial

**2. Guias práticos > Teoria**
- "Como fazer X" > "O que é X"
- Exemplos executáveis
- Troubleshooting antecipado

**3. Versionamento de docs**
- CHANGELOG mantém histórico
- Cada versão tem docs atualizadas
- Links para papers/referências

### Regulamentação

**1. IA médica é regulada**
- FDA/ANVISA exigem explicabilidade
- CAD = Class II medical device
- Validação clínica obrigatória

**2. Responsabilidade do médico**
- IA é auxílio, não substituto
- Decisão final sempre do radiologista
- Documentar limitações claramente

**3. Ética em IA**
- Transparência sobre capacidades
- Evitar overclaiming
- Dados de pacientes são sensíveis

---

## Navegação

- **[← Módulo 5: Implementação Técnica](./modulo5-implementacao.md)**
- **[→ Módulo 7: Uso Clínico e Regulamentação](./modulo7-uso-clinico.md)**
- **[← Voltar para Academia](../ACADEMY.md)**

---

**Próximo passo:** Continue para o [Módulo 7](./modulo7-uso-clinico.md) para entender o uso clínico e aspectos regulatórios.
