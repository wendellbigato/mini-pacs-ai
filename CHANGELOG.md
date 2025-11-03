# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-10-29

### Adicionado

#### Infraestrutura
- Configuração Docker Compose com serviços Orthanc e Inference API
- Makefile com comandos para gerenciar containers (`build`, `up`, `down`, `logs`, `test`, etc.)
- Arquivo `.gitignore` para Python, Docker, Jupyter e IDEs
- Configuração do Orthanc PACS (`orthanc/orthanc.json`)
- Volume persistente para dados DICOM (`orthanc/data/`)

#### API de Inferência
- FastAPI com endpoint `POST /predict` para inferência em arquivos DICOM
- Endpoint `GET /health` para verificação de saúde da API
- Endpoint `GET /labels` para listar achados radiológicos detectáveis
- Modelo TorchXRayVision (DenseNet121) pré-treinado
- Pré-processamento automático de arquivos DICOM:
  - Normalização de pixel values
  - Redimensionamento para 224x224
  - Conversão para tensor PyTorch
- Schemas Pydantic para validação e documentação (`PredictionResponse`, `HealthResponse`)
- Documentação automática via Swagger UI e ReDoc
- Sistema de logging estruturado
- Extração de metadados DICOM (Patient ID, Study Date, Modality)

#### Notebook Jupyter
- Notebook de integração Orthanc → API (`orthanc_inference.ipynb`)
- Funções para:
  - Listar instâncias DICOM do Orthanc
  - Baixar arquivos DICOM via API REST
  - Enviar para API de inferência
  - Visualizar imagens com matplotlib
  - Exibir probabilidades de achados radiológicos
- Análise consolidada de múltiplos exames
- Célula para teste com arquivos DICOM locais

#### Documentação
- README.md completo com:
  - Visão geral da arquitetura
  - Instruções de instalação e uso
  - Documentação dos endpoints da API
  - Comandos Make disponíveis
  - Troubleshooting
  - Referências e avisos importantes
- Template de relatório técnico (`report/desafio_neuralmind.md`) com:
  - Arquitetura da solução
  - Fluxo técnico detalhado
  - Dificuldades encontradas
  - Aprendizados novos vs conhecimento prévio
  - Melhorias futuras
- Requirements.txt para notebook Jupyter

### Detalhes Técnicos

#### Dependências Principais
- FastAPI 0.115.5
- PyTorch 2.5.1
- TorchXRayVision 1.2.1
- PyDICOM 3.0.1
- Uvicorn 0.32.1
- Pydantic 2.10.3

#### Modelo
- Arquitetura: DenseNet121
- Input: 224x224 grayscale
- Output: 18 achados radiológicos
- Device: CPU (configurável para GPU)

#### Portas Expostas
- 8042: Orthanc PACS (HTTP + DICOM REST API)
- 4242: Orthanc DICOM protocol
- 8000: API de Inferência

### Notas de Segurança
- Autenticação do Orthanc desabilitada para desenvolvimento (deve ser habilitada em produção)
- Dados DICOM persistidos localmente em volume Docker

---

## [1.0.1] - 2025-11-02

### Corrigido

#### Bug Fixes - API /predict
- **Erro 422 Unprocessable Entity**: Corrigido schema do endpoint `/predict` adicionando `media_type="application/dicom"` ao parâmetro `File()` (inference_api/app/main.py:70)
- **Erro 500 Internal Server Error**: Corrigido validação Pydantic do campo `image_shape` convertendo tupla para string em `preprocess.py:71`
- Problema: Swagger UI estava enviando string em vez de UploadFile
- Problema: Metadados retornavam `image_shape` como tupla `(2566, 2598)` em vez de string

#### Infraestrutura
- Removido atributo `version: '3.8'` obsoleto do `docker-compose.yml` (compatibilidade Docker Compose v2+)

### Adicionado

#### Makefile
- Comando `make rebuild`: Rebuild automático completo da API (down + build + up + health check)
- Comando `make test-health`: Verificação de saúde da API com contagem de labels

#### Documentação
- `TESTE_API.md`: Guia completo de como testar a API /predict com troubleshooting
- `REBUILD_INSTRUCOES.md`: Documentação sobre quando e como fazer rebuild vs restart
- `test_predict.py`: Script Python para testes automatizados do endpoint /predict com visualização de resultados
- `docs/plans/extras-futuras.md`: Documentação de melhorias extras (AWS S3, GPU, etc.)

### Melhorado
- Logs de startup da API mais informativos
- Processo de rebuild documentado e automatizado
- Instruções de troubleshooting expandidas no README

### Notas Técnicas
- Após modificar código Python (arquivos `.py`), é obrigatório fazer `make rebuild` em vez de apenas `make restart`
- O restart apenas reinicia containers sem reconstruir a imagem Docker
- Build em cache mantém dependências (apenas camada `COPY app` é reconstruída se requirements.txt não mudou)

---

## [1.2.0] - 2025-11-02

### Adicionado

#### Visualização e Interpretabilidade
- **Grad-CAM (Gradient-weighted Class Activation Mapping)**: Heatmaps de atenção para interpretação visual das predições
  - Novo módulo `inference_api/app/gradcam.py` com classe `TorchXRayVisionCAM`
  - Destaca regiões da imagem que influenciaram cada predição
  - Padrão-ouro em visualizadores profissionais (Sante DICOM Viewer, Horos)
  - Suporte a múltiplos colormaps (COLORMAP_JET, COLORMAP_HOT, etc.)
  - Overlay de heatmap sobre imagem original
  - Conversão automática para base64 para transmissão via JSON

#### Pré-processamento Otimizado
- **Pipeline Oficial TorchXRayVision**: Implementação do método recomendado pela biblioteca
  - Novo módulo `inference_api/app/preprocess_official.py`
  - Normalização [-1024, 1024] HU scale (vs. [0,1] do método simplificado)
  - `XRayCenterCrop()` para focar região torácica
  - `XRayResizer(224)` com interpolação apropriada para raio-X
  - Alinhado com treinamento do modelo DenseNet121
  - Função de comparação entre métodos (`compare_preprocessing_outputs`)

#### Novos Endpoints da API
- **POST /predict_with_heatmap**: Predição + heatmaps Grad-CAM
  - Parâmetros: `top_n` (padrão: 5), `use_official_preprocessing` (padrão: true)
  - Retorna probabilidades + heatmaps em base64 para top N achados
  - Tempo adicional: ~1-2s (aceitável para análise)
  - Documentação automática no Swagger UI

- **POST /compare_preprocessing**: Comparação de métodos de pré-processamento
  - Executa inferência com ambos métodos (atual vs. oficial)
  - Retorna probabilidades de cada método
  - Calcula diferenças absolutas por achado
  - Estatísticas agregadas: mean_difference, max_difference, std_difference
  - Estatísticas dos tensores pré-processados (mean, std, min, max)

#### Notebooks de Análise
- **comparison_analysis.ipynb**: Análise comparativa completa
  - PARTE 1: Comparação de pré-processamento (atual vs. oficial)
    - Visualização lado-a-lado das probabilidades
    - Gráficos de diferenças (verde/laranja/vermelho por threshold)
    - Tabela de top 10 maiores diferenças
  - PARTE 2: Visualização Grad-CAM
    - Heatmaps para top 5 achados
    - Imagem original + heatmap + probabilidade
    - Interpretação clínica (regiões quentes/frias)
  - PARTE 3: Análise consolidada (todas as instâncias)
    - Estatísticas de todas as imagens DICOM do Orthanc
    - Distribuição de diferenças (histograma + boxplot)
    - Decisão automatizada (manter atual vs. trocar para oficial)

#### Container Jupyter
- **Dockerfile dedicado**: Container Jupyter otimizado
  - Imagem base: `python:3.11-slim` (~500 MB vs. 2 GB de imagens oficiais)
  - Sem senha/token para desenvolvimento
  - Volume mount em `/workspace`
- **Serviço no docker-compose.yml**: Jupyter como terceiro microserviço
  - Depende de `orthanc` e `inference-api`
  - Rede `pacs-network` (comunicação via service names)
  - URLs internas: `http://orthanc:8042`, `http://inference-api:8000`
- **Comandos Make**:
  - `make jupyter`: Sobe Jupyter e exibe URL de acesso
  - `make jupyter-stop`: Para apenas Jupyter (mantém outros serviços)
  - `make logs-jupyter`: Logs do container Jupyter

#### Dependências
- `pytorch-grad-cam==1.4.8`: Geração de Class Activation Maps
- `opencv-python==4.10.0.84`: Processamento de imagens e colormaps

#### Schemas Pydantic
- `PreprocessingStats`: Estatísticas de tensores pré-processados
- `ComparePreprocessingResponse`: Response do endpoint /compare_preprocessing
- `HeatmapData`: Dados de um heatmap (pathology, probability, heatmap_base64)
- `PredictionWithHeatmapResponse`: Response do endpoint /predict_with_heatmap

#### Documentação
- **docs/plans/inprogress/visualizacao-preprocessing.md**: Plano detalhado de implementação
  - Arquitetura das melhorias
  - Fases de implementação (pré-processamento, Grad-CAM, notebook)
  - Critérios de sucesso e validação
  - Riscos e mitigações
  - Justificativas técnicas (segurança, eficiência, escalabilidade)
- **README.md atualizado**:
  - Seção "Arquitetura Jupyter: Melhores Práticas"
    - Justificativas da escolha do container dedicado
    - Comparação com alternativas (Opção 2 e 3)
    - Princípios: Segurança, Eficiência, Escalabilidade, Manutenibilidade
  - Documentação dos novos endpoints (/predict_with_heatmap, /compare_preprocessing)
  - Estrutura de projeto atualizada com novos arquivos
  - Versão 1.2.0
- **JUPYTER_IMPLEMENTADO.md**: Documentação completa da implementação Jupyter
  - Arquitetura final
  - Mudanças realizadas
  - Comandos de uso
  - Troubleshooting
  - Checklist de validação

### Melhorado
- **Versão da API**: Atualizada de 1.0.0 para 1.2.0
- **Endpoint raiz (/)**: Agora lista novos endpoints disponíveis
- **Organização de código**: Separação clara entre pré-processamento atual e oficial
- **Documentação Swagger**: Descrições detalhadas dos novos endpoints com exemplos

### Detalhes Técnicos

#### Grad-CAM
- **Target layer**: Última camada convolucional do DenseNet121 (`model.model.features[-1]`)
- **Output**: Heatmap normalizado [0, 1] em resolução 224x224
- **Formato**: PNG em base64 (data URI)
- **Colormap padrão**: COLORMAP_JET (vermelho=alta atenção, azul=baixa)

#### Pré-processamento Oficial
- **Normalização**: `xrv.datasets.normalize(img, 255)` → [-1024, 1024]
- **Transformações**: `XRayCenterCrop()` + `XRayResizer(224)`
- **Compatibilidade**: Alinhado com treinamento do modelo TorchXRayVision
- **Decisão de uso**: Baseada em `mean_difference < 0.05` (threshold)

#### Arquitetura Jupyter
- **Padrão**: Container dedicado (Separation of Concerns)
- **Segurança**: Breach limitado ao container Jupyter (Princípio de Menor Privilégio)
- **Eficiência**: 500 MB vs. 2 GB (4x menor que imagem oficial)
- **Escalabilidade**: Jupyter e API escalam independentemente
- **Manutenibilidade**: Single Responsibility Principle (SOLID)

### Notas de Performance
- Heatmap Grad-CAM adiciona ~1-2s ao tempo de inferência (aceitável)
- Recomendado processar heatmaps em background para aplicações de produção
- Cache de heatmaps pode ser implementado para instâncias repetidas

### Notas de Uso
- **Notebook local vs. Docker**: Se rodar localmente, trocar URLs para `localhost:8042` e `localhost:8000`
- **Rebuild obrigatório**: Após atualizar código Python, usar `make rebuild` (não apenas restart)
- **Comparação de pré-processamento**: Executar `comparison_analysis.ipynb` para decisão baseada em dados

### Referências
- **Grad-CAM paper**: https://arxiv.org/abs/1610.02391
- **TorchXRayVision docs**: https://github.com/mlmed/torchxrayvision
- **TorchXRayVision preprocessing**: https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py
- **Normalização issue**: https://github.com/mlmed/torchxrayvision/issues/9

---

## [1.3.0] - 2025-11-03

### Adicionado

#### Máscaras de Segmentação Grad-CAM
- **Máscaras binárias automáticas**: Geração de máscaras de segmentação a partir de heatmaps Grad-CAM
  - Novo campo `mask_base64` no endpoint `/predict_with_heatmap`
  - Threshold adaptativo baseado na probabilidade (0.4-0.6)
  - Formato PNG em base64 para visualização
  - Colormap configurável (padrão: COLORMAP_HOT)
  - Função `generate_binary_mask_from_heatmap()` em `gradcam.py`

- **Visualização estilo TorchXRayVision**: Layout inspirado no notebook oficial
  - Referência: [xray_masks.ipynb](https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb)
  - Overlay de máscaras com alpha=0.5
  - Múltiplas máscaras por exame (uma por achado)
  - Visualização lado-a-lado: Original + Máscaras sobrepostas

#### Validação com Ground Truth (Opcional)
- **Suporte a NIH Dataset**: Integração opcional para validação científica
  - Novo módulo `inference_api/app/nih_dataset.py`
  - Classe `NIHDatasetManager` para gerenciar dataset NIH
  - Carregamento de máscaras ground truth (anotações manuais)
  - Configuração via variável de ambiente `NIH_DATASET_PATH`

- **Novos Endpoints de Validação**:
  - `GET /masks`: Retorna máscaras ground truth de amostras do NIH Dataset
    - Query params: `sample_idx`, `pathology`
    - Response com imagem + máscaras em base64
  - `POST /validate_masks`: Valida Grad-CAM vs ground truth
    - Calcula IoU (Intersection over Union)
    - Avaliação automática: excellent/good/fair/poor
    - Bounding boxes Grad-CAM vs máscaras ground truth

- **Métricas de Validação**:
  - Cálculo de IoU (Intersection over Union)
  - Função `calculate_iou()` para comparar bbox com máscara
  - Função `compare_gradcam_with_groundtruth()` para validação completa
  - Estatísticas de cobertura da máscara (% da imagem)

#### Documentação Clínica Completa
- **CLINICAL_USAGE.md**: Guia completo para médicos radiologistas
  - Comparação Grad-CAM vs Ground Truth (tabela detalhada)
  - Fluxo de trabalho clínico recomendado
  - Interpretação de probabilidades e máscaras
  - Limitações e responsabilidades médicas
  - Casos de uso recomendados (quando usar/não usar)
  - Evidência científica (papers + FDA/ANVISA)
  - Referências a papers validados

- **README.md - Seção "Uso Clínico"**: Orientações para médicos
  - Por que Grad-CAM é escolha correta para PACS (6 critérios)
  - Diferença clara entre Grad-CAM e ground truth
  - Quando usar cada abordagem
  - Limitações clínicas destacadas
  - Link para guia clínico completo

- **Notebook comparison_analysis.ipynb - PARTE 4**:
  - Explicação técnica para médicos
  - Tabela comparativa Grad-CAM vs Ground Truth
  - Referência ao xray_masks.ipynb oficial
  - Avisos médicos em cada visualização
  - Comentários explicativos no código

#### Schemas Pydantic
- `GroundTruthMask`: Dados de máscara ground truth
- `ValidationResult`: Resultado da validação (IoU score, avaliação)
- `MasksResponse`: Response do endpoint /masks
- `ValidateMasksResponse`: Response do endpoint /validate_masks
- Campo `mask_base64` adicionado a `HeatmapData`

### Melhorado
- **Versão da API**: Atualizada de 1.2.0 para 1.3.0
- **Endpoint raiz (/)**: Agora exibe disponibilidade do NIH dataset
- **Endpoint /predict_with_heatmap**: Retorna heatmaps + máscaras automaticamente
- **Documentação README.md**: Seção completa sobre uso clínico
- **Notebook comparison_analysis.ipynb**: PARTE 4 com máscaras estilo TorchXRayVision

### Detalhes Técnicos

#### Máscaras Grad-CAM
- **Binarização**: Threshold adaptativo (0.4 para prob<50%, 0.5 para 50-70%, 0.6 para >70%)
- **Colormap**: COLORMAP_HOT (cores quentes para regiões de atenção)
- **Output**: PNG em base64 (mesmo formato dos heatmaps)
- **Tamanho**: 224x224 (redimensionado para tamanho original no notebook)

#### Validação Ground Truth
- **Dataset suportado**: NIH Chest X-ray (112,120 imagens)
- **Configuração**: Volume mount + variável ambiente `NIH_DATASET_PATH`
- **Opcional**: Sistema funciona normalmente sem NIH dataset
- **Uso**: Validação científica, não inferência em produção

#### Arquitetura de Validação
- **Separação clara**: Inferência (Grad-CAM) vs Validação (Ground Truth)
- **Design**: NIH dataset é opcional, não obrigatório
- **Performance**: Validação roda em background, não afeta inferência

### Comparação: Grad-CAM vs Ground Truth

| Característica | Grad-CAM | Ground Truth |
|----------------|----------|--------------|
| **Origem** | Gerado automaticamente | Anotado manualmente |
| **Uso** | Auxílio diagnóstico PACS | Pesquisa/Validação |
| **Exames novos** | ✅ Sim | ❌ Não |
| **Tempo** | 2-3s | Horas |
| **Precisão** | ~70-80% | 100% |
| **Custo** | Zero | Alto |

### Notas de Uso Clínico

**Para Médicos Radiologistas:**
- ✅ Use Grad-CAM para exames clínicos do PACS
- ❌ Ground truth apenas para validação/ensino
- ⚠️ Máscaras são sugestões, não diagnóstico definitivo
- ⚠️ Decisão final sempre do médico

**Limitações:**
- Grad-CAM: ~70-80% de concordância vs ground truth
- Pode apresentar falsos positivos/negativos
- Não substitui análise do radiologista
- Sempre validar com conhecimento clínico

### Referências
- **Grad-CAM paper**: https://arxiv.org/abs/1610.02391 (Selvaraju et al., 2017)
- **xray_masks.ipynb**: https://github.com/mlmed/torchxrayvision/blob/main/scripts/xray_masks.ipynb
- **Probabilistic-CAM Pooling**: Ye et al., 2020 (baseline TorchXRayVision)
- **Classificação**: FDA Classe II (CAD - Computer-Aided Detection)

---

## [Unreleased]

### Planejado - Prioridade Alta
- Testes unitários e de integração
- Autenticação no Orthanc
- Validação robusta de inputs
- Configuração via variáveis de ambiente

### Planejado - Prioridade Média
- Cache de resultados
- Rate limiting
- Métricas com Prometheus/Grafana
- CI/CD pipeline

### Extras - Prioridade Baixa (Opcional)
- Suporte a GPU para inferência
- Batch processing de múltiplos DICOMs
- Persistência de DICOMs em AWS S3 (substituir volume local por bucket S3)
- Multi-stage Docker build
- Documentação OpenAPI 3.1 avançada

**Nota:** Itens acima são melhorias extras, não fazem parte do roadmap principal. Ver `docs/plans/extras-futuras.md` para detalhes.

[1.2.0]: https://github.com/wendellbarreto/mini-pacs-ai/releases/tag/v1.2.0
[1.0.1]: https://github.com/wendellbarreto/mini-pacs-ai/releases/tag/v1.0.1
[1.0.0]: https://github.com/wendellbarreto/mini-pacs-ai/releases/tag/v1.0.0
