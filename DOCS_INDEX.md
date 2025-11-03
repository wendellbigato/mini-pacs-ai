# 📚 Índice de Documentação - Mini PACS AI v1.3.0

> Guia completo de navegação pela documentação do projeto

---

## 🚀 Começando

### Para Médicos Radiologistas
1. **[CLINICAL_USAGE.md](./CLINICAL_USAGE.md)** ⭐ **COMECE AQUI**
   - Guia completo de uso clínico
   - Grad-CAM vs Ground Truth explicado
   - Fluxo de trabalho recomendado
   - Limitações e responsabilidades
   - Evidência científica

2. **[README.md](./README.md)** - Seção "Uso Clínico"
   - Tabela comparativa (6 critérios)
   - Quando usar cada abordagem
   - Link para guia completo

### Para Desenvolvedores/Técnicos
1. **[README.md](./README.md)** ⭐ **COMECE AQUI**
   - Visão geral da arquitetura
   - Instruções de instalação
   - Comandos disponíveis
   - Troubleshooting

2. **[CHANGELOG.md](./CHANGELOG.md)**
   - Histórico completo de versões
   - v1.3.0: Máscaras Grad-CAM + Validação
   - v1.2.0: Grad-CAM + Pré-processamento
   - v1.0.1: Bug fixes
   - v1.0.0: Versão inicial

---

## 📡 Testando a API

### [TESTE_API.md](./TESTE_API.md)
**O que contém:**
- Como testar todos os endpoints
- `/predict` - Predição básica
- `/predict_with_heatmap` - Predição + máscaras ⭐
- `/compare_preprocessing` - Comparar métodos
- `/masks` - Ground truth (opcional)
- `/validate_masks` - Validação (opcional)
- Exemplos curl e Swagger UI
- Troubleshooting de erros comuns

**Quando usar:**
- Testar API manualmente
- Entender formato das respostas
- Debug de problemas

---

## 📓 Usando os Notebooks

### [GUIA_NOTEBOOK.md](./GUIA_NOTEBOOK.md)
**O que contém:**
- Como usar 2 notebooks disponíveis
- `orthanc_inference.ipynb` - Básico
- `comparison_analysis.ipynb` - **Avançado** ⭐
  - PARTE 1: Comparação pré-processamento
  - PARTE 2: Heatmaps Grad-CAM
  - PARTE 3: Análise consolidada
  - PARTE 4: **Máscaras de segmentação** (NOVO)
- Instalação local vs Docker
- Pré-requisitos e checklist

**Quando usar:**
- Visualizar resultados das predições
- Analisar múltiplos exames
- Ver máscaras de segmentação

### [notebooks/QUICK_START.md](./notebooks/QUICK_START.md)
- Guia rápido para começar
- 3 passos simples

---

## 🔧 Configuração e Manutenção

### [REBUILD_INSTRUCOES.md](./REBUILD_INSTRUCOES.md)
**O que contém:**
- Quando fazer rebuild vs restart
- Como fazer rebuild corretamente
- Troubleshooting de build

**Quando usar:**
- Após modificar código Python
- Após atualizar dependências
- Containers não sobem

### [ATUALIZACOES_v1.0.1.md](./ATUALIZACOES_v1.0.1.md)
- Correções específicas v1.0.1
- Bug fixes detalhados

---

## 🏗️ Arquitetura e Decisões

### [JUPYTER_IMPLEMENTADO.md](./JUPYTER_IMPLEMENTADO.md)
**O que contém:**
- Por que container dedicado?
- Justificativas técnicas
- Comparação de opções
- Melhores práticas

**Quando usar:**
- Entender arquitetura Jupyter
- Questões sobre design

### [JUPYTER_DOCKER_OPCOES.md](./JUPYTER_DOCKER_OPCOES.md)
- Análise de 3 opções de implementação
- Decisão técnica detalhada

---

## 📋 Planejamento e Roadmap

### [docs/plans/inprogress/](./docs/plans/inprogress/)
- **visualizacao-preprocessing.md**
  - Plano Grad-CAM + Pré-processamento
  - Fases de implementação
  - Critérios de sucesso
  - **Status:** ✅ Concluído (v1.2.0)

- **todos-implementacao.md**
  - TODOs gerais do projeto
  - Funcionalidades pendentes

### [docs/plans/extras-futuras.md](./docs/plans/extras-futuras.md)
- Melhorias opcionais (baixa prioridade)
- GPU, AWS S3, batch processing, etc.

---

## 📊 Relatório Técnico

### [report/desafio_neuralmind.md](./report/desafio_neuralmind.md)
**O que contém:**
- Arquitetura da solução
- Fluxo técnico detalhado
- Dificuldades encontradas
- Aprendizados novos

**Quando usar:**
- Apresentações técnicas
- Documentação formal
- Entender decisões de design

---

## 🔬 Referências Científicas

### Papers Citados

1. **Grad-CAM Original**
   - Selvaraju et al. (2017)
   - https://arxiv.org/abs/1610.02391
   - Citado em: CLINICAL_USAGE.md, README.md, CHANGELOG.md

2. **TorchXRayVision**
   - https://github.com/mlmed/torchxrayvision
   - **xray_masks.ipynb**: https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb
   - Citado em: README.md, CHANGELOG.md, notebooks

3. **Probabilistic-CAM Pooling**
   - Ye et al. (2020)
   - Citado em: CHANGELOG.md

### Validação Clínica
- Nature Communications (2024)
- Radiology - RSNA (2024)
- Lancet Digital Health (2023)
- Detalhes em: CLINICAL_USAGE.md

---

## 🎯 Mapa de Navegação por Persona

### Médico Radiologista
```
1. CLINICAL_USAGE.md (LEITURA OBRIGATÓRIA)
2. GUIA_NOTEBOOK.md → comparison_analysis.ipynb PARTE 4
3. README.md → Seção "Uso Clínico"
4. TESTE_API.md → /predict_with_heatmap
```

### Desenvolvedor Backend
```
1. README.md (visão geral)
2. CHANGELOG.md (o que mudou)
3. TESTE_API.md (como testar)
4. REBUILD_INSTRUCOES.md (manutenção)
5. Code: inference_api/app/
```

### Data Scientist / Pesquisador
```
1. GUIA_NOTEBOOK.md
2. notebooks/comparison_analysis.ipynb (TODAS as partes)
3. README.md → Seção "Validação Científica"
4. CLINICAL_USAGE.md → Evidência científica
5. docs/plans/inprogress/visualizacao-preprocessing.md
```

### DevOps / SysAdmin
```
1. README.md → Comandos Make
2. REBUILD_INSTRUCOES.md
3. docker-compose.yml
4. Makefile
5. TESTE_API.md → Health checks
```

### Gestor / Product Owner
```
1. CLINICAL_USAGE.md → Fluxo de trabalho
2. README.md → Features
3. CHANGELOG.md → Evoluções
4. report/desafio_neuralmind.md → Visão técnica
```

---

## 📁 Estrutura de Arquivos

```
mini-pacs-ai/
├── 📖 DOCS_INDEX.md ⭐ (este arquivo)
├── 📖 README.md ⭐ (início para todos)
├── 📖 CLINICAL_USAGE.md ⭐ (médicos)
├── 📖 CHANGELOG.md (histórico)
├── 📖 TESTE_API.md (testar endpoints)
├── 📖 GUIA_NOTEBOOK.md (notebooks)
├── 📖 REBUILD_INSTRUCOES.md (manutenção)
├── 📖 ATUALIZACOES_v1.0.1.md (bug fixes)
├── 📖 JUPYTER_IMPLEMENTADO.md (arquitetura)
├── 📖 JUPYTER_DOCKER_OPCOES.md (decisões)
│
├── notebooks/
│   ├── 📖 QUICK_START.md
│   ├── 📓 orthanc_inference.ipynb
│   └── 📓 comparison_analysis.ipynb ⭐ (4 partes)
│
├── docs/
│   └── plans/
│       ├── inprogress/
│       │   ├── 📖 visualizacao-preprocessing.md
│       │   └── 📖 todos-implementacao.md
│       └── 📖 extras-futuras.md
│
└── report/
    └── 📖 desafio_neuralmind.md
```

---

## 🔄 Fluxo de Leitura Recomendado

### 1️⃣ Primeiro Contato (15 min)
```
README.md → overview completo
```

### 2️⃣ Instalação e Teste (30 min)
```
README.md → Instalação
TESTE_API.md → Testar /predict_with_heatmap
GUIA_NOTEBOOK.md → Abrir comparison_analysis.ipynb
```

### 3️⃣ Uso Clínico (1 hora)
```
CLINICAL_USAGE.md → Ler completo
notebooks/comparison_analysis.ipynb → PARTE 4
README.md → Seção "Uso Clínico"
```

### 4️⃣ Entendimento Técnico (2 horas)
```
CHANGELOG.md → v1.3.0, v1.2.0, v1.0.0
JUPYTER_IMPLEMENTADO.md → Arquitetura
docs/plans/inprogress/visualizacao-preprocessing.md → Plano
Code review: inference_api/app/
```

---

## 📞 Próximos Passos

**Após ler a documentação:**

1. **Testar localmente**
   ```bash
   make up
   make test
   ```

2. **Explorar notebooks**
   - http://localhost:8888/notebooks/comparison_analysis.ipynb

3. **Testar API**
   - http://localhost:8000/docs

4. **Para médicos:** Ler guia clínico
   - `CLINICAL_USAGE.md`

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Documentos:** 15 arquivos principais
**Notebooks:** 2 (básico + avançado)

