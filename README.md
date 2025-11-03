# Mini PACS AI

Sistema de inferência de achados radiológicos em imagens DICOM usando TorchXRayVision, integrado com PACS Orthanc.

## 📋 Visão Geral

Este projeto implementa um ambiente Docker com múltiplos serviços para simular um fluxo real de imagens médicas:

1. **PACS Orthanc**: Servidor DICOM para armazenamento e gerenciamento de exames
2. **API de Inferência**: API REST que recebe arquivos DICOM e retorna probabilidades de achados radiológicos usando modelo pré-treinado TorchXRayVision
3. **Notebook Jupyter**: Interface para integração automática entre Orthanc e API de inferência

## 🏗️ Arquitetura

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  Orthanc PACS   │─────▶│  Inference API   │◀─────│  Jupyter        │
│  (Port 8042)    │      │  (Port 8000)     │      │  Notebook       │
│                 │      │  TorchXRayVision │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                        │
         │                        │
    DICOM Files            Deep Learning Model
    (Persistent)           (CPU-based)
```

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)
- Python 3.11+ (para executar o notebook localmente)

### 1. Clonar o repositório

```bash
git clone <repository-url>
cd mini-pacs-ai
```

### 2. Subir os serviços

```bash
# Usando Makefile (recomendado)
make build  # Constrói as imagens
make up     # Sobe os serviços em background

# Ou usando docker compose diretamente
docker compose build
docker compose up -d
```

### 3. Verificar status

```bash
make status  # Verifica status dos containers
make test    # Testa se os serviços estão respondendo
```

### 4. Acessar as interfaces

- **Orthanc Web UI**: http://localhost:8042
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## 📊 Usando o Sistema

### Upload de Arquivos DICOM no Orthanc

1. Acesse http://localhost:8042
2. Clique em "Upload" no menu superior
3. Selecione arquivos DICOM do seu computador
4. Os arquivos serão armazenados persistentemente em `orthanc/data/`

**Dataset de teste**: https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

### Testar a API de Inferência

#### Via Swagger UI (Interface Web)

1. Acesse http://localhost:8000/docs
2. Expanda o endpoint `POST /predict`
3. Clique em "Try it out"
4. Faça upload de um arquivo DICOM
5. Execute e veja os resultados

#### Via cURL

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "dicom_file=@/path/to/your/file.dcm"
```

#### Via Python

```python
import requests

url = "http://localhost:8000/predict"
files = {"dicom_file": open("path/to/file.dcm", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Executar o Notebook de Integração

1. Instale as dependências do notebook:

```bash
pip install requests pydicom matplotlib pandas
```

2. Abra o Jupyter:

```bash
jupyter notebook notebooks/orthanc_inference.ipynb
```

3. Execute as células sequencialmente. O notebook irá:
   - Listar todas as instâncias DICOM no Orthanc
   - Baixar cada instância
   - Enviar para a API de inferência
   - Exibir a imagem e as probabilidades

## 🛠️ Comandos Make Disponíveis

```bash
make help           # Mostra todos os comandos disponíveis
make build          # Constrói as imagens Docker
make up             # Sobe todos os serviços em background
make down           # Para e remove todos os containers
make restart        # Reinicia todos os serviços
make rebuild        # Rebuild completo da API (use após mudar código Python)
make logs           # Mostra logs de todos os serviços
make logs-orthanc   # Mostra logs apenas do Orthanc
make logs-api       # Mostra logs apenas da API
make status         # Mostra status dos containers
make test           # Testa se todos os serviços estão respondendo
make test-orthanc   # Testa apenas o Orthanc
make test-api       # Testa apenas a API
make test-health    # Testa saúde da API e mostra labels do modelo
make clean          # Remove containers, volumes e imagens
make shell-api      # Abre shell no container da API
make shell-orthanc  # Abre shell no container do Orthanc
make dev            # Sobe os serviços com logs visíveis
```

## 📁 Estrutura do Projeto

```
mini-pacs-ai/
├── Makefile                    # Comandos para gerenciar o projeto
├── docker-compose.yml          # Orquestração dos serviços
├── README.md                   # Este arquivo
├── CHANGELOG.md                # Histórico de mudanças
├── TESTE_API.md                # Guia de testes da API /predict
├── REBUILD_INSTRUCOES.md       # Quando fazer rebuild vs restart
├── test_predict.py             # Script de teste da API
├── orthanc/
│   ├── orthanc.json           # Configuração do Orthanc
│   └── data/                  # Volume persistente (criado automaticamente)
├── inference_api/
│   ├── Dockerfile             # Imagem da API
│   ├── requirements.txt       # Dependências Python
│   └── app/
│       ├── __init__.py
│       ├── main.py            # FastAPI + endpoint /predict
│       ├── model.py           # Carregamento TorchXRayVision
│       ├── preprocess.py      # Pré-processamento DICOM
│       └── schemas.py         # Schemas Pydantic
├── notebooks/
│   ├── orthanc_inference.ipynb # Notebook de integração
│   └── requirements.txt        # Dependências do notebook
├── docs/
│   └── plans/
│       ├── inprogress/
│       │   └── todos-implementacao.md
│       ├── done/
│       └── extras-futuras.md   # Melhorias extras (AWS S3, etc.)
└── report/
    └── desafio_neuralmind.md   # Relatório técnico (.pdf a ser gerado)
```

## 🔬 API Endpoints

### `POST /predict`

Recebe um arquivo DICOM e retorna probabilidades de achados radiológicos.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `dicom_file` (arquivo DICOM)

**Response:**
```json
{
  "probabilities": {
    "Atelectasis": 0.123,
    "Cardiomegaly": 0.456,
    "Consolidation": 0.078,
    "Edema": 0.234,
    "Pleural Effusion": 0.567,
    ...
  },
  "metadata": {
    "patient_id": "123456",
    "study_date": "20240101",
    "modality": "CR"
  }
}
```

### `GET /health`

Verifica status da API e do modelo.

### `GET /labels`

Retorna lista de achados radiológicos que o modelo pode predizer.

## 🧠 Modelo TorchXRayVision

O sistema utiliza o modelo **DenseNet121** pré-treinado do [TorchXRayVision](https://github.com/mlmed/torchxrayvision), que é capaz de detectar múltiplos achados radiológicos em imagens de raio-x de tórax.

**Achados detectados:**
- Atelectasis
- Cardiomegaly
- Consolidation
- Edema
- Pleural Effusion
- E outros (18 classes no total)

**Especificações técnicas:**
- Modelo: DenseNet121 (ResNet 224x224)
- Entrada: Imagens DICOM pré-processadas (grayscale, 224x224)
- Saída: Probabilidades entre 0 e 1 para cada achado
- Device: CPU (configurável para GPU)

## 🔧 Configuração

### Orthanc

O arquivo `orthanc/orthanc.json` contém a configuração do servidor PACS:

- **AuthenticationEnabled**: `false` (para desenvolvimento; ativar em produção)
- **DicomPort**: 4242
- **HttpPort**: 8042
- **StorageDirectory**: `/var/lib/orthanc/db` (mapeado para `orthanc/data/`)

### API de Inferência

Configurações podem ser ajustadas via variáveis de ambiente no `docker-compose.yml`:

- `PYTHONUNBUFFERED=1`: Logs em tempo real
- Device do modelo: Editar `inference_api/app/model.py` (padrão: CPU)

## 📝 Pré-processamento DICOM

A API aplica os seguintes passos de pré-processamento:

1. Leitura do arquivo DICOM com `pydicom`
2. Extração do `pixel_array`
3. Normalização para [0, 1]
4. Redimensionamento para 224x224 pixels
5. Conversão para tensor PyTorch [1, 1, 224, 224]
6. Normalização para média 0 e desvio padrão 1

Esse pipeline garante que as imagens sejam compatíveis com o modelo TorchXRayVision.

## 🐛 Troubleshooting

### Containers não sobem

```bash
# Verifica logs
make logs

# Reconstrói as imagens
make down
make build
make up
```

### API retorna erro 500

```bash
# Verifica logs da API
make logs-api

# Verifica se o modelo foi carregado
curl http://localhost:8000/health
```

### Orthanc não persiste dados

Verifique se a pasta `orthanc/data/` tem permissões adequadas:

```bash
ls -la orthanc/data/
```

### Notebook não consegue conectar

Certifique-se de que os serviços estão rodando:

```bash
make test
```

### Erro 422 ou 500 ao testar /predict

Se modificou o código Python da API:

```bash
# IMPORTANTE: Não basta fazer restart, precisa rebuild
make rebuild

# Isso faz automaticamente:
# - Para os containers
# - Reconstrói a imagem com código atualizado
# - Sobe os containers
# - Testa saúde da API
```

**Documentação completa:** Ver `TESTE_API.md` e `REBUILD_INSTRUCOES.md`

### Script de teste rápido

```bash
# Testar endpoint /predict com arquivo DICOM
python test_predict.py /caminho/para/arquivo.dcm

# Mostra:
# - Top 10 achados radiológicos com probabilidades
# - Metadados do DICOM
# - Barra de progresso visual
```

## 📚 Referências

- **Orthanc**: https://www.orthanc-server.com/
- **Docker**: https://www.docker.com/
- **TorchXRayVision**: https://github.com/mlmed/torchxrayvision
- **FastAPI**: https://fastapi.tiangolo.com/
- **PyDICOM**: https://pydicom.github.io/

## ⚠️ Avisos Importantes

1. **Segurança**: Esta configuração desabilita autenticação no Orthanc para facilitar desenvolvimento. **NÃO use em produção sem configurar credenciais adequadas.**

2. **Performance**: O modelo roda em CPU por padrão. Para melhor performance em produção, configure GPU.

3. **Persistência**: Os dados DICOM são armazenados em `orthanc/data/`. Faça backup regularmente.

4. **Recursos**: O build da imagem Docker da API pode levar vários minutos devido ao download do PyTorch e dependências.

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte de um desafio técnico.

## 👤 Autor

Wendell Barreto

---

**Última atualização**: 2025-10-29
