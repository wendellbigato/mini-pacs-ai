# Melhorias Extras e Funcionalidades Futuras

Este documento lista ideias e melhorias **extras** que não fazem parte do escopo original do projeto, mas podem agregar valor em cenários específicos.

---

## 🌟 Extras - Prioridade Baixa

### 1. Persistência de DICOMs em AWS S3

**Descrição:**
Migrar o armazenamento de arquivos DICOM do volume Docker local para um bucket AWS S3.

**Motivação:**
- Escalabilidade para grandes volumes de dados
- Backup automático e redundância geográfica
- Redução de custos de infraestrutura on-premise
- Acesso distribuído entre múltiplas instâncias do Orthanc
- Conformidade com regulamentações de retenção de dados médicos

**Implementação Sugerida:**
```yaml
# docker-compose.yml
orthanc:
  image: orthancteam/orthanc:latest
  environment:
    - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    - AWS_REGION=us-east-1
    - S3_BUCKET_NAME=mini-pacs-dicom-storage
  volumes:
    - ./orthanc/orthanc-s3.json:/etc/orthanc/orthanc.json:ro
```

**Configuração Orthanc S3 Plugin:**
```json
{
  "Name": "LocalOrthanc",
  "Plugins": ["libOrthancAwsS3Storage.so"],
  "AwsS3Storage": {
    "BucketName": "mini-pacs-dicom-storage",
    "Region": "us-east-1",
    "StorageStructure": "flat",
    "EnableLegacyUnknownFiles": false
  }
}
```

**Recursos Necessários:**
- Plugin Orthanc AWS S3 Storage
- Bucket S3 configurado com políticas de acesso
- Credenciais IAM com permissões:
  - `s3:PutObject`
  - `s3:GetObject`
  - `s3:DeleteObject`
  - `s3:ListBucket`

**Considerações:**
- ⚠️ Latência de acesso aos DICOMs (rede vs disco local)
- ⚠️ Custos de transferência de dados AWS
- ⚠️ Necessidade de VPN/VPC para ambientes hospitalares
- ✅ Backup e disaster recovery simplificados
- ✅ Conformidade HIPAA/LGPD com criptografia S3

**Links:**
- [Orthanc AWS S3 Plugin](https://book.orthanc-server.com/plugins/object-storage.html)
- [AWS S3 Healthcare Best Practices](https://aws.amazon.com/health/solutions/)

---

### 2. Suporte a GPU para Inferência

**Status:** Listado mas considerado extra

Acelerar inferência usando CUDA em ambientes com GPU disponível.

---

### 3. Batch Processing de Múltiplos DICOMs

**Status:** Listado mas considerado extra

Endpoint para processar múltiplos arquivos em uma única request.

---

### 4. Multi-stage Docker Build

**Status:** Listado mas considerado extra

Otimizar tamanho da imagem Docker da API usando builds em múltiplos estágios.

---

### 5. Documentação OpenAPI 3.1 Avançada

**Status:** Listado mas considerado extra

Expandir documentação da API com exemplos, callbacks e webhooks.

---

## 📝 Notas

- Estes itens **NÃO** fazem parte do roadmap principal
- São melhorias **opcionais** para casos de uso específicos
- Implementação deve ser avaliada caso a caso conforme necessidade
- Prioridade **baixa** em relação a requisitos funcionais e de segurança

---

**Última atualização:** 2025-11-02
**Status:** Documentação de ideias futuras
