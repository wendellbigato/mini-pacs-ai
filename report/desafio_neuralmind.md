# Desafio Técnico NeuralMind - Mini PACS AI

## 1. Arquitetura da Solução

### Visão Geral

O projeto implementa um sistema completo de inferência de achados radiológicos usando três componentes principais:

1. **Orthanc PACS** (Port 8042)
   - Servidor DICOM para armazenamento e gerenciamento de imagens médicas
   - Persistência de dados em volume Docker
   - Interface web para upload e visualização

2. **API de Inferência** (Port 8000)
   - FastAPI com endpoint `/predict`
   - Modelo TorchXRayVision (DenseNet121) pré-treinado
   - Pré-processamento automático de arquivos DICOM
   - Documentação automática via Swagger/ReDoc

3. **Notebook Jupyter**
   - Integração automática Orthanc → API
   - Visualização de imagens e resultados
   - Análise consolidada de múltiplos exames

### Fluxo de Dados

```
DICOM Upload → Orthanc → Notebook/Cliente → API /predict → Modelo → Probabilidades
```

## 2. Fluxo Técnico

### 2.1. Upload e Armazenamento (Orthanc)

- Arquivos DICOM enviados via interface web do Orthanc
- Armazenamento persistente em `/var/lib/orthanc/db` (volume Docker)
- API REST do Orthanc expõe endpoints:
  - `GET /instances` - lista todas as instâncias
  - `GET /instances/{id}/file` - baixa arquivo DICOM
  - `GET /instances/{id}/simplified-tags` - metadados

### 2.2. Pré-processamento (API)

Pipeline implementado em `inference_api/app/preprocess.py`:

1. Leitura do DICOM com `pydicom.dcmread()`
2. Extração do `pixel_array`
3. Normalização para [0, 1]
4. Redimensionamento para 224x224 (esperado pelo modelo)
5. Conversão para tensor PyTorch [1, 1, 224, 224]
6. Normalização estatística (média 0, std 1)

### 2.3. Inferência (Modelo)

- Modelo: DenseNet121 do TorchXRayVision
- Carregamento lazy (singleton) na inicialização da API
- Forward pass retorna logits para 18 classes
- Aplicação de sigmoid para obter probabilidades [0, 1]
- Ordenação decrescente das probabilidades

### 2.4. Integração (Notebook)

Workflow implementado em `notebooks/orthanc_inference.ipynb`:

1. Lista todas as instâncias do Orthanc
2. Para cada instância:
   - Baixa o arquivo DICOM
   - Envia para `/predict`
   - Renderiza imagem com matplotlib
   - Exibe top 5 achados radiológicos

## 3. Dificuldades Encontradas

### 3.1. Normalização DICOM

**Problema**: Imagens DICOM podem ter diferentes ranges de pixel values (window/level).

**Solução**: Implementação de normalização min-max antes do redimensionamento, garantindo valores [0, 1] independentemente do range original.

### 3.2. Tamanho das Imagens Docker

**Problema**: Imagem Docker da API ficou grande (~2GB) devido ao PyTorch e dependências.

**Solução**: 
- Uso de `python:3.11-slim` como base
- Limpeza de cache apt após instalação de dependências
- `PIP_NO_CACHE_DIR=1` para evitar cache do pip

### 3.3. Persistência de Dados Orthanc

**Problema**: Dados DICOM sumiam ao reiniciar containers.

**Solução**: Volume Docker mapeando `./orthanc/data:/var/lib/orthanc/db` no docker-compose.yml.

### 3.4. Compatibilidade de Versões

**Problema**: Conflitos entre versões de numpy/torch/torchxrayvision.

**Solução**: Pin de versões específicas no `requirements.txt` após testes de compatibilidade.

## 4. Aprendizados Novos

### 4.1. TorchXRayVision

- Descoberta de biblioteca especializada em raio-x médicos
- Modelos pré-treinados em datasets clínicos (ChestX-ray14, MIMIC-CXR)
- Arquitetura DenseNet adaptada para single-channel (grayscale)

### 4.2. Orthanc

- Primeiro contato com PACS open-source
- Entendimento de arquitetura DICOM (Patient → Study → Series → Instance)
- API REST do Orthanc para integração programática

### 4.3. FastAPI

- Integração com Pydantic para validação automática
- Geração automática de documentação OpenAPI
- Upload de arquivos multipart/form-data

### 4.4. Docker Multi-Service

- Orquestração de múltiplos serviços com docker-compose
- Redes bridge para comunicação entre containers
- Estratégias de healthcheck e depends_on

## 5. Conhecimento Prévio

### 5.1. Deep Learning

- PyTorch para inferência
- Pré-processamento de imagens (normalização, resize)
- Transfer learning com modelos pré-treinados

### 5.2. Docker

- Criação de Dockerfiles
- Uso de docker-compose
- Volumes e redes

### 5.3. APIs REST

- Design de endpoints RESTful
- Versionamento de APIs
- Tratamento de erros HTTP

### 5.4. Python

- Estruturação de projetos Python
- Type hints e Pydantic
- Logging e debugging

### 5.5. Processamento de Imagens Médicas

- Formato DICOM
- Bibliotecas: pydicom, pillow, scikit-image
- Normalização e redimensionamento

## 6. Melhorias Futuras

### Curto Prazo

1. **Autenticação**: Implementar credenciais no Orthanc
2. **Testes**: Adicionar testes unitários e de integração
3. **GPU Support**: Configuração opcional para inferência em GPU
4. **Cache**: Cache de modelos e resultados para performance

### Médio Prazo

1. **Batch Processing**: Endpoint para processar múltiplos DICOMs
2. **Async API**: Endpoints assíncronos para processamento em background
3. **Métricas**: Prometheus/Grafana para monitoramento
4. **CI/CD**: Pipeline de build e deploy automático

### Longo Prazo

1. **Múltiplos Modelos**: Suporte a diferentes modelos especializados
2. **Visualização Avançada**: Heatmaps/Grad-CAM para explicabilidade
3. **DICOM Send**: Envio de resultados de volta ao PACS
4. **Auditoria**: Log de todas as predições para compliance

### Extras (Opcional)

1. **Persistência em Cloud (AWS S3)**: Migrar armazenamento de DICOMs para bucket S3
   - Integração com Orthanc S3 Plugin
   - Redução de custos de infraestrutura
   - Escalabilidade e backup automático
   - Acesso distribuído entre múltiplas instâncias
   - Ver `docs/plans/extras-futuras.md` para detalhes de implementação

## 7. Conclusão

O projeto demonstra um fluxo completo de processamento de imagens médicas, desde o armazenamento DICOM até a inferência com deep learning. A arquitetura modular permite fácil extensão e manutenção.

Os principais desafios envolveram integração entre tecnologias (DICOM, Docker, PyTorch) e garantia de qualidade no pré-processamento das imagens.

O sistema está pronto para uso em ambiente de desenvolvimento/POC, mas requer ajustes de segurança e performance para produção.

---

**Data**: 2025-10-29  
**Autor**: Wendell Barreto  
**Repositório**: mini-pacs-ai
