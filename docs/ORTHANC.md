# 📦 Orthanc PACS - Configuração e Uso

> **Autor:** Wendell Barreto (wendellbarreto@gmail.com)
> **Versão:** 1.3.0
> **Orthanc Version:** 1.12+

---

## 📋 Índice

- [O que é Orthanc?](#o-que-é-orthanc)
- [Arquitetura](#arquitetura)
- [Configuração](#configuração)
- [Acessando o Orthanc](#acessando-o-orthanc)
- [Upload de DICOMs](#upload-de-dicoms)
- [REST API](#rest-api)
- [Persistência de Dados](#persistência-de-dados)
- [Troubleshooting](#troubleshooting)

---

## O que é Orthanc?

**Orthanc** é um servidor PACS (Picture Archiving and Communication System) open-source leve e standalone:

- ✅ **Open Source:** GPL License
- ✅ **Leve:** Roda em Docker, Raspberry Pi, ou servidor dedicado
- ✅ **Completo:** Storage, Query/Retrieve, Web Viewer
- ✅ **Extensível:** Plugins para HL7, DICOMweb, PostgreSQL, etc.
- ✅ **REST API:** Interface HTTP completa para integração

**Site Oficial:** https://www.orthanc-server.com/

**Documentação:** https://book.orthanc-server.com/

### Por que Orthanc neste projeto?

| Alternativa | Por que NÃO usamos |
|-------------|-------------------|
| DCM4CHEE | Java-based, mais pesado, configuração complexa |
| Horos | macOS only |
| Osirix | macOS only, comercial |
| Conquest PACS | Linux only, menos documentação |

**Vantagens do Orthanc:**
1. **Docker-friendly** - Container oficial bem mantido
2. **REST API completa** - Fácil integração com Python/FastAPI
3. **Leveza** - Ideal para desenvolvimento local (~100 MB imagem)
4. **Documentação excelente** - "The Orthanc Book"
5. **Comunidade ativa** - Google Groups, GitHub

---

## Arquitetura

```
┌────────────────────────────────────────┐
│          ORTHANC SERVER                │
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  DICOM SCP   │  │   REST API   │  │
│  │  (porta 4242)│  │ (porta 8042) │  │
│  └──────┬───────┘  └──────┬───────┘  │
│         │                  │          │
│         └────────┬─────────┘          │
│                  │                    │
│  ┌───────────────▼────────────────┐  │
│  │      SQLite Database           │  │
│  │  (Patients, Studies, Series)   │  │
│  └───────────────┬────────────────┘  │
│                  │                    │
│  ┌───────────────▼────────────────┐  │
│  │    Filesystem Storage          │  │
│  │  (DICOM files, attachments)    │  │
│  └────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### Componentes

**1. DICOM SCP (Service Class Provider)**
- Porta: 4242
- Protocolo: DICOM (C-STORE, C-FIND, C-MOVE, C-ECHO)
- Uso: Receber DICOMs de modalidades (CT, MRI, CR, etc.)

**2. REST API HTTP**
- Porta: 8042
- Protocolo: HTTP/HTTPS
- Endpoints: /patients, /studies, /series, /instances
- Uso: Integração com aplicações (nosso caso)

**3. SQLite Database**
- Localização: `/var/lib/orthanc/db/index`
- Conteúdo: Metadados DICOM indexados
- Hierarquia: Patient → Study → Series → Instance

**4. Filesystem Storage**
- Localização: `/var/lib/orthanc/db/`
- Conteúdo: Arquivos DICOM completos
- Estrutura: UUID-based folders

---

## Configuração

### Arquivo: orthanc/orthanc.json

```json
{
  "Name": "MiniPacsAI",
  "AuthenticationEnabled": false,
  "RemoteAccessAllowed": true,
  "DicomAet": "ORTHANC",
  "DicomPort": 4242,
  "HttpPort": 8042,
  "StorageDirectory": "/var/lib/orthanc/db",
  "OverwriteInstances": true,
  "Plugins": []
}
```

### Parâmetros Principais

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `Name` | "MiniPacsAI" | Nome identificador do servidor |
| `AuthenticationEnabled` | false | ⚠️ **Apenas dev!** Habilitar em produção |
| `RemoteAccessAllowed` | true | Aceita conexões externas (não localhost) |
| `DicomAet` | "ORTHANC" | Application Entity Title (identificador DICOM) |
| `DicomPort` | 4242 | Porta para protocolo DICOM |
| `HttpPort` | 8042 | Porta para REST API HTTP |
| `StorageDirectory` | "/var/lib/orthanc/db" | Onde DICOMs são salvos |
| `OverwriteInstances` | true | Permite substituir DICOMs com mesmo ID |

### Configuração no Docker Compose

```yaml
orthanc:
  image: orthancteam/orthanc:latest
  container_name: orthanc
  ports:
    - "8042:8042"  # REST API + Web UI
    - "4242:4242"  # DICOM protocol
  volumes:
    - ./orthanc/data:/var/lib/orthanc/db
    - ./orthanc/orthanc.json:/etc/orthanc/orthanc.json:ro
  restart: unless-stopped
```

**Volumes:**
- `./orthanc/data` → Dados persistentes (DICOMs + SQLite)
- `./orthanc/orthanc.json` → Configuração (read-only)

**Portas:**
- `8042` → Web UI e REST API
- `4242` → DICOM (para modalidades enviarem exames)

---

## Acessando o Orthanc

### Web UI

**URL:** http://localhost:8042

**Interface:**
```
┌────────────────────────────────────┐
│   ORTHANC                          │
│   ┌──────────────────────────────┐ │
│   │ Upload  |  Explorer  |  Logs │ │
│   └──────────────────────────────┘ │
│                                    │
│   Patients:  3                     │
│   Studies:   5                     │
│   Series:    8                     │
│   Instances: 120                   │
│                                    │
│   Storage:   1.2 GB / 100 GB       │
└────────────────────────────────────┘
```

**Funcionalidades:**
- 📤 **Upload** - Enviar DICOMs manualmente
- 🔍 **Explorer** - Navegar hierarquia Patient/Study/Series
- 📊 **Logs** - Ver atividade do servidor
- 👁️ **Viewer** - Visualizar DICOMs no navegador

### Via Linha de Comando

```bash
# Status do container
docker compose ps orthanc

# Logs em tempo real
docker compose logs -f orthanc

# Estatísticas do sistema
curl http://localhost:8042/statistics | jq

# Shell dentro do container
docker compose exec orthanc bash
```

---

## Upload de DICOMs

### Método 1: Via Web UI (Recomendado)

1. Acesse http://localhost:8042
2. Clique em **"Upload"** no menu superior
3. Clique em **"Select files to upload"**
4. Selecione arquivos `.dcm` do seu computador
5. Aguarde upload concluir
6. Verifique em **"Explorer"**

### Método 2: Via REST API

```bash
# Upload único
curl -X POST http://localhost:8042/instances \
  --data-binary @exam.dcm \
  -H "Content-Type: application/dicom"

# Upload múltiplo (shell script)
for file in *.dcm; do
  curl -X POST http://localhost:8042/instances \
    --data-binary @"$file" \
    -H "Content-Type: application/dicom"
  echo "Uploaded: $file"
done
```

### Método 3: Via DICOM Protocol (C-STORE)

```bash
# Usando dcmtk (DICOM toolkit)
storescu -aec ORTHANC localhost 4242 exam.dcm

# Usando pynetdicom (Python)
python -m pynetdicom storescu \
  localhost 4242 \
  -aec ORTHANC \
  exam.dcm
```

### Dataset de Teste

**Link:** https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing

**Conteúdo:**
- Raio-X de tórax (PA e Lateral)
- Formato: DICOM (.dcm)
- Modalidade: CR (Computed Radiography)

---

## REST API

### Hierarquia DICOM

```
PATIENT (Paciente)
  └─ STUDY (Estudo/Exame)
      └─ SERIES (Série)
          └─ INSTANCE (Imagem)
```

**Exemplo:**
```
João Silva (Patient)
  └─ Raio-X Tórax PA + Perfil (Study) - 2025-11-03
      ├─ Série 1: PA (Series)
      │   └─ Imagem 1 (Instance)
      └─ Série 2: Perfil (Series)
          └─ Imagem 1 (Instance)
```

### Endpoints Principais

#### Listar Recursos

```bash
# Listar todos os pacientes
curl http://localhost:8042/patients

# Listar todos os estudos
curl http://localhost:8042/studies

# Listar todas as séries
curl http://localhost:8042/series

# Listar todas as instâncias (imagens)
curl http://localhost:8042/instances
```

**Response:**
```json
[
  "abc-123-def-456",
  "ghi-789-jkl-012",
  ...
]
```

#### Obter Detalhes

```bash
# Metadados de uma instância
curl http://localhost:8042/instances/{id}/tags

# Informações simplificadas
curl http://localhost:8042/instances/{id}/simplified-tags
```

**Response (simplified-tags):**
```json
{
  "PatientName": "João Silva",
  "PatientID": "123456",
  "StudyDate": "20251103",
  "Modality": "CR",
  "SeriesDescription": "Chest PA",
  "Rows": 2619,
  "Columns": 2000
}
```

#### Baixar DICOMs

```bash
# Baixar DICOM original
curl http://localhost:8042/instances/{id}/file -o exam.dcm

# Preview PNG (grayscale)
curl http://localhost:8042/instances/{id}/preview -o preview.png

# Preview JPEG
curl http://localhost:8042/instances/{id}/preview?quality=90 -o preview.jpg
```

#### Buscar

```bash
# Buscar por paciente
curl -X POST http://localhost:8042/tools/find \
  -H "Content-Type: application/json" \
  -d '{
    "Level": "Patient",
    "Query": {
      "PatientName": "*Silva*"
    }
  }'

# Buscar por data
curl -X POST http://localhost:8042/tools/find \
  -H "Content-Type: application/json" \
  -d '{
    "Level": "Study",
    "Query": {
      "StudyDate": "20251103"
    }
  }'
```

#### Deletar

```bash
# Deletar instância
curl -X DELETE http://localhost:8042/instances/{id}

# Deletar série completa
curl -X DELETE http://localhost:8042/series/{id}

# Deletar estudo completo
curl -X DELETE http://localhost:8042/studies/{id}

# Deletar paciente completo
curl -X DELETE http://localhost:8042/patients/{id}
```

### Integração com Python

```python
import requests

ORTHANC_URL = "http://localhost:8042"

# Listar instâncias
response = requests.get(f"{ORTHANC_URL}/instances")
instance_ids = response.json()
print(f"Total de instâncias: {len(instance_ids)}")

# Baixar primeiro DICOM
instance_id = instance_ids[0]
dicom_bytes = requests.get(
    f"{ORTHANC_URL}/instances/{instance_id}/file"
).content

# Obter metadados
metadata = requests.get(
    f"{ORTHANC_URL}/instances/{instance_id}/simplified-tags"
).json()

print(f"Paciente: {metadata['PatientName']}")
print(f"Data: {metadata['StudyDate']}")
print(f"Modalidade: {metadata['Modality']}")
```

---

## Persistência de Dados

### Estrutura de Diretórios

```
orthanc/data/
├── index                    # SQLite database
├── [UUID-1]/
│   ├── [UUID]              # DICOM file
│   └── [UUID].json         # Metadata cache
├── [UUID-2]/
│   ├── [UUID]
│   └── [UUID].json
└── ...
```

### Backup

**Método 1: Backup simples (parar Orthanc)**

```bash
# 1. Parar Orthanc
docker compose stop orthanc

# 2. Copiar dados
tar -czf orthanc-backup-$(date +%Y%m%d).tar.gz orthanc/data/

# 3. Reiniciar
docker compose start orthanc
```

**Método 2: Backup contínuo (sem parar)**

```bash
# Usar rsync (copia apenas mudanças)
rsync -av --delete orthanc/data/ /path/to/backup/orthanc-data/

# Agendar com cron (backup diário 2AM)
0 2 * * * rsync -av --delete /path/to/mini-pacs-ai/orthanc/data/ /backup/orthanc/
```

### Restaurar Backup

```bash
# 1. Parar Orthanc
docker compose stop orthanc

# 2. Remover dados atuais
rm -rf orthanc/data/*

# 3. Extrair backup
tar -xzf orthanc-backup-20251103.tar.gz -C orthanc/

# 4. Reiniciar
docker compose start orthanc
```

### Migração para PostgreSQL (Produção)

**Por quê?**
- SQLite: <10.000 estudos
- PostgreSQL: >10.000 estudos, alta concorrência

**Como:**

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: orthancdb
      POSTGRES_USER: orthanc
      POSTGRES_PASSWORD: orthanc
    volumes:
      - postgres_data:/var/lib/postgresql/data

  orthanc:
    image: orthancteam/orthanc:latest
    environment:
      ORTHANC__POSTGRESQL__HOST: postgres
      ORTHANC__POSTGRESQL__DATABASE: orthancdb
      ORTHANC__POSTGRESQL__USERNAME: orthanc
      ORTHANC__POSTGRESQL__PASSWORD: orthanc
    depends_on:
      - postgres
```

---

## Troubleshooting

### Orthanc não inicia

**Causa 1:** Porta 8042 ou 4242 em uso

```bash
# Verificar portas em uso
lsof -i :8042
lsof -i :4242

# Matar processo ocupando porta
kill -9 <PID>

# Ou mudar porta no docker-compose.yml
ports:
  - "8043:8042"  # Usar 8043 no host
```

**Causa 2:** Permissões de volume

```bash
# Verificar permissões
ls -la orthanc/data/

# Corrigir (se necessário)
sudo chown -R $(whoami):$(whoami) orthanc/data/
```

### DICOMs não persistem após restart

**Causa:** Volume não mapeado corretamente

**Verificar:**
```bash
# Inspecionar container
docker compose inspect orthanc | grep -A5 Mounts

# Deve mostrar:
# "Source": "/path/to/mini-pacs-ai/orthanc/data"
# "Destination": "/var/lib/orthanc/db"
```

**Solução:**
```yaml
# docker-compose.yml
volumes:
  - ./orthanc/data:/var/lib/orthanc/db  # ✅ Path relativo
  # Não usar absolute path a menos que necessário
```

### Upload falha com erro 400

**Causa:** Arquivo não é DICOM válido

**Verificar:**
```bash
# Testar leitura com pydicom
python -c "import pydicom; dcm = pydicom.dcmread('exam.dcm'); print(dcm)"

# Verificar extensão
file exam.dcm
# Deve mostrar: DICOM medical imaging data
```

### API retorna 404 para instância existente

**Causa:** ID incorreto (deve ser UUID completo)

**Solução:**
```bash
# ❌ Errado (ID parcial)
curl http://localhost:8042/instances/abc-123

# ✅ Correto (UUID completo)
curl http://localhost:8042/instances/abc-123-def-456-ghi-789-jkl-012
```

### Orthanc lento com muitas instâncias

**Causa:** SQLite não é ideal para >10k estudos

**Soluções:**
1. **Curto prazo:** Deletar estudos antigos
2. **Longo prazo:** Migrar para PostgreSQL (ver seção acima)

```bash
# Ver estatísticas
curl http://localhost:8042/statistics

# Deletar estudos > 1 ano
# (implementar script Python com data filtering)
```

### Erro "Disk full"

**Causa:** Espaço em disco insuficiente

**Verificar:**
```bash
# Espaço disponível
df -h

# Tamanho do Orthanc
du -sh orthanc/data/
```

**Soluções:**
1. Deletar estudos antigos
2. Compactar DICOMs (lossless)
3. Mover para disco maior
4. Configurar storage para outro local:

```json
// orthanc.json
{
  "StorageDirectory": "/mnt/large-disk/orthanc-storage"
}
```

---

## Documentação Complementar

- **Site Oficial:** https://www.orthanc-server.com/
- **The Orthanc Book:** https://book.orthanc-server.com/
- **REST API Reference:** https://book.orthanc-server.com/users/rest.html
- **Plugins:** https://book.orthanc-server.com/plugins/
- **Forum:** https://groups.google.com/g/orthanc-users

**Arquivos do projeto:**
- Configuração: `orthanc/orthanc.json`
- Docker Compose: `docker-compose.yml`
- Academy (aprender PACS/DICOM): `docs/ACADEMY.md`

---

**Última atualização:** 2025-11-03 (v1.3.0)
**Autor:** Wendell Barreto (wendellbarreto@gmail.com)
