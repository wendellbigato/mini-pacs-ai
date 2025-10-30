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

## [Unreleased]

### Planejado
- Testes unitários e de integração
- Suporte a GPU para inferência
- Autenticação no Orthanc
- Batch processing de múltiplos DICOMs
- Cache de resultados
- Métricas com Prometheus/Grafana
- CI/CD pipeline

[1.0.0]: https://github.com/wendellbarreto/mini-pacs-ai/releases/tag/v1.0.0
