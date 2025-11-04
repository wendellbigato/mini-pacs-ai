# Módulo 1: Fundamentos de Imagens Médicas

> **Parte da:** [Academia Mini PACS AI](../ACADEMY.md)
> **Duração estimada:** 45-60 minutos
> **Pré-requisitos:** Nenhum

---

## 1.1 O que é PACS?

### Definição

**PACS** (Picture Archiving and Communication System) é um sistema completo para:
- **Armazenar** imagens médicas digitais
- **Recuperar** exames rapidamente
- **Distribuir** imagens para estações de trabalho
- **Arquivar** exames de longo prazo

### Contexto Histórico

**Antes do PACS (anos 1980):**
- Radiografias em filme físico
- Armazenamento em envelopes
- Perda frequente de exames
- Impossível visualizar remotamente
- Degradação do filme com o tempo

**Depois do PACS (anos 1990+):**
- Imagens digitais (DICOM)
- Armazenamento em servidores
- Acesso instantâneo de qualquer lugar
- Backups automáticos
- Integração com RIS/HIS

### Componentes de um PACS

```
┌─────────────────────────────────────────────────┐
│                    PACS                         │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Aquisição│  │Armazena- │  │Visualiza-│     │
│  │ Imagens  │→ │  mento   │→ │   ção    │     │
│  └──────────┘  └──────────┘  └──────────┘     │
│       ↓              ↓              ↓          │
│   Modalidades    Servidor      Estações       │
│   (CT, MRI...)   (Storage)   (Workstations)   │
└─────────────────────────────────────────────────┘
```

**1. Modalidades de Aquisição:**
- CT (Tomografia Computadorizada)
- MRI (Ressonância Magnética)
- CR/DR (Raio-X Digital)
- Ultrassom
- PET, Mamografia, etc.

**2. Servidor de Armazenamento:**
- Banco de dados DICOM
- Redundância (RAID)
- Backups automáticos

**3. Estações de Visualização:**
- Laudos radiológicos
- Consultas médicas
- Ensino/pesquisa

### Por que PACS é importante?

**Eficiência:**
- Elimina transporte físico de filmes
- Múltiplos médicos veem mesma imagem simultaneamente
- Busca por paciente/data/modalidade instantânea

**Qualidade:**
- Imagens digitais não degradam
- Ferramentas de pós-processamento (zoom, contraste, medidas)
- Comparação com exames anteriores lado-a-lado

**Integração:**
- RIS (Radiology Information System) - agendamento, laudos
- HIS (Hospital Information System) - prontuário eletrônico
- HL7/DICOM para interoperabilidade

## 1.2 O padrão DICOM

### O que é DICOM?

**DICOM** (Digital Imaging and Communications in Medicine) é o **padrão mundial** para:
- Formato de arquivo de imagens médicas
- Protocolo de comunicação entre equipamentos
- Metadados clínicos estruturados

**Analogia simples:**
```
DICOM está para imagens médicas
       assim como
JPEG/PNG estão para fotos comuns
```

Mas DICOM é **muito mais rico** porque inclui:
- Dados do paciente
- Dados do estudo (data, modalidade)
- Dados do equipamento
- Pixels da imagem
- Orientação espacial (3D)

### Estrutura de um arquivo DICOM

```
arquivo.dcm
│
├─ HEADER (Metadados)
│  ├─ Patient Information
│  │  ├─ Patient ID
│  │  ├─ Patient Name
│  │  ├─ Date of Birth
│  │  └─ Sex
│  │
│  ├─ Study Information
│  │  ├─ Study Date
│  │  ├─ Study Time
│  │  ├─ Study Description
│  │  └─ Accession Number
│  │
│  ├─ Series Information
│  │  ├─ Modality (CR, CT, MRI...)
│  │  ├─ Series Number
│  │  └─ Body Part Examined
│  │
│  └─ Image Information
│     ├─ Image Position
│     ├─ Image Orientation
│     ├─ Pixel Spacing
│     └─ Rows/Columns
│
└─ PIXEL DATA (Imagem)
   └─ Array 2D/3D de intensidades
```

### Exemplo Prático com PyDICOM

```python
import pydicom

# Ler arquivo DICOM
dcm = pydicom.dcmread("exame.dcm")

# Acessar metadados
print(f"Paciente: {dcm.PatientName}")
print(f"Modalidade: {dcm.Modality}")
print(f"Data: {dcm.StudyDate}")

# Acessar imagem
pixels = dcm.pixel_array  # numpy array
print(f"Dimensões: {pixels.shape}")
print(f"Range: {pixels.min()} - {pixels.max()}")
```

### Tags DICOM

Cada metadado tem uma **tag** única (grupo, elemento):

```python
# Exemplos de tags
(0010, 0010)  # Patient Name
(0008, 0060)  # Modality
(0028, 0010)  # Rows
(0028, 0011)  # Columns
(7FE0, 0010)  # Pixel Data
```

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

### Modalidades DICOM Comuns

| Código | Nome Completo | Descrição |
|--------|---------------|-----------|
| CR | Computed Radiography | Raio-X digital (cassete) |
| DX | Digital Radiography | Raio-X digital (detector direto) |
| CT | Computed Tomography | Tomografia |
| MR | Magnetic Resonance | Ressonância Magnética |
| US | Ultrasound | Ultrassom |
| PT | Positron Emission Tomography | PET |
| MG | Mammography | Mamografia |
| XA | X-Ray Angiography | Angiografia |

### DICOM vs Imagens Comuns

| Característica | JPEG/PNG | DICOM |
|----------------|----------|-------|
| Metadados | Mínimos (EXIF) | Completos (paciente, estudo, equipamento) |
| Profundidade | 8 bits (0-255) | 12-16 bits (0-4095+) |
| Compressão | Lossy/Lossless | Lossless preferível |
| Orientação 3D | ❌ Não | ✅ Sim |
| Padrão Médico | ❌ Não | ✅ Sim (FDA, ANVISA) |

### Protocolo de Comunicação DICOM

**C-STORE** - Enviar imagens
```
Modalidade → PACS
(Ex: CT envia exame para Orthanc)
```

**C-FIND** - Buscar estudos
```
Estação → PACS
(Ex: buscar exames de "João Silva")
```

**C-MOVE** - Recuperar imagens
```
PACS → Estação
(Ex: baixar exame específico)
```

**C-ECHO** - Testar conexão
```
Sistema A ↔ Sistema B
(Ex: verificar se PACS está acessível)
```

## 1.3 Orthanc: PACS Open Source

### O que é Orthanc?

**Orthanc** é um servidor PACS:
- ✅ Open source (GPL)
- ✅ Leve (roda em Docker, Raspberry Pi)
- ✅ Completo (storage, query/retrieve, viewer)
- ✅ Extensível (plugins para HL7, DICOMweb, PostgreSQL)
- ✅ REST API completa

**Site oficial:** https://www.orthanc-server.com/

### Por que escolhemos Orthanc?

**Alternativas comerciais:**
- DCM4CHEE (Java, mais pesado)
- Horos (macOS only)
- Osirix (macOS only, comercial)
- Conquestpacs (Linux, mais complexo)

**Vantagens do Orthanc para este projeto:**
1. **Docker-friendly** - container oficial mantido
2. **REST API** - fácil integração com Python
3. **Leveza** - ideal para desenvolvimento local
4. **Documentação** - excelente (The Orthanc Book)
5. **Comunidade** - ativa no Google Groups

### Arquitetura do Orthanc

```
┌────────────────────────────────────────┐
│          ORTHANC SERVER                │
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  DICOM SCP   │  │   REST API   │  │
│  │  (porta 4242)│  │ (porta 8042) │  │
│  └──────────────┘  └──────────────┘  │
│         ↓                  ↓          │
│  ┌────────────────────────────────┐  │
│  │      SQLite Database           │  │
│  │  (Patients, Studies, Series)   │  │
│  └────────────────────────────────┘  │
│         ↓                             │
│  ┌────────────────────────────────┐  │
│  │    Filesystem Storage          │  │
│  │  (DICOM files, attachments)    │  │
│  └────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### REST API do Orthanc

**Endpoints principais:**

```bash
# Listar todos os pacientes
GET /patients

# Listar estudos de um paciente
GET /patients/{id}/studies

# Listar instâncias (imagens)
GET /instances

# Obter metadados de uma instância
GET /instances/{id}/tags

# Baixar DICOM original
GET /instances/{id}/file

# Preview PNG
GET /instances/{id}/preview

# Sistema
GET /system
GET /statistics
```

**Exemplo de uso:**

```python
import requests

# Listar todas as imagens no Orthanc
response = requests.get("http://localhost:8042/instances")
instance_ids = response.json()

# Baixar primeiro DICOM
dicom_bytes = requests.get(
    f"http://localhost:8042/instances/{instance_ids[0]}/file"
).content

# Ver metadados
metadata = requests.get(
    f"http://localhost:8042/instances/{instance_ids[0]}/tags"
).json()
```

### Configuração do Orthanc

**Arquivo:** `orthanc/orthanc.json`

```json
{
  "Name": "MiniPacsAI",
  "AuthenticationEnabled": false,  // ⚠️ Apenas dev!
  "RemoteAccessAllowed": true,
  "DicomAet": "ORTHANC",
  "DicomPort": 4242,
  "HttpPort": 8042,
  "StorageDirectory": "/var/lib/orthanc/db",
  "OverwriteInstances": true
}
```

**Opções importantes:**

- `AuthenticationEnabled: false` - **APENAS DESENVOLVIMENTO**
  - Em produção: use autenticação!
- `RemoteAccessAllowed: true` - aceita conexões externas
- `DicomAet` - Application Entity Title (identificador DICOM)
- `StorageDirectory` - onde os DICOMs são salvos

### Orthanc no Docker

**docker-compose.yml:**

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

**Persistência de dados:**
- Volume `./orthanc/data` mapeia o storage interno
- DICOMs sobrevivem a `docker compose down`
- Backup = copiar pasta `orthanc/data/`

## 1.4 Workflow Radiológico

### Fluxo Tradicional (sem IA)

```
1. AQUISIÇÃO
   Técnico → Equipamento (CT/MRI/CR) → DICOM gerado

2. ENVIO
   Modalidade → PACS (C-STORE)

3. DISTRIBUIÇÃO
   PACS → Worklist do Radiologista

4. VISUALIZAÇÃO
   Radiologista → Estação de Laudo → Ferramentas (zoom, janela)

5. LAUDO
   Radiologista → Dictation/Typing → RIS

6. APROVAÇÃO
   Radiologista Senior → Revisão → Laudo Final

7. DISTRIBUIÇÃO
   RIS → Médico Solicitante → Prontuário
```

### Fluxo com IA (Mini PACS AI)

```
1. AQUISIÇÃO
   Técnico → Equipamento → DICOM gerado

2. ENVIO
   Modalidade → Orthanc (PACS)

3. IA PROCESSING ⭐ (NOVO)
   Orthanc → API de Inferência → Predições + Grad-CAM

4. VISUALIZAÇÃO ASSISTIDA
   Radiologista → Jupyter/Viewer → Imagem + Máscaras + Probabilidades

5. LAUDO ASSISTIDO
   Radiologista → Valida/Refuta IA → Laudo Final

6. APROVAÇÃO
   (mesmo fluxo tradicional)
```

### Integração HL7

**HL7** (Health Level Seven) é o padrão para troca de dados administrativos:

```
RIS → PACS (HL7 message)
  ↓
"Novo exame agendado para João Silva"
  ↓
PACS cria Worklist
  ↓
Técnico vê na modalidade
```

**Mensagens HL7 comuns:**
- ADT (Admission/Discharge/Transfer) - movimentação de pacientes
- ORM (Order Message) - solicitação de exame
- ORU (Observation Result) - resultado de exame

**Neste projeto:**
- Não implementamos HL7 (fora do escopo)
- Upload manual de DICOMs via Orthanc UI
- Em produção real: integração RIS ↔ Orthanc via HL7/FHIR

---

**Próximo módulo:** [Módulo 2: Inteligência Artificial em Radiologia](./modulo2-ia-radiologia.md)
