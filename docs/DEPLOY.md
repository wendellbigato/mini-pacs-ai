# 🚀 Guia de Deploy - Mini PACS AI

> **Versão:** 1.4.0+
> **Data:** 2025-11-04
> **Autor:** Wendell Barreto

---

## 📋 Visão Geral

Este documento descreve como fazer deploy do Mini PACS AI em clusters Kubernetes em diferentes cloud providers usando GitHub Actions e Kustomize.

### Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────┐
│              GitHub Actions (CI/CD)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PR → main  ──→  Build  ──→  Push  ──→  Deploy    │
│                    ↓          ↓          ↓         │
│                 Docker     Registry   Kubernetes   │
└─────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────┼────────────────┐
         ↓                ↓                ↓
    ┌────────┐      ┌────────┐      ┌────────┐
    │  AWS   │      │ Azure  │      │ Oracle │
    │  EKS   │      │  AKS   │      │  OKE   │
    └────────┘      └────────┘      └────────┘
```

### 🏷️ Seleção de Cloud Provider

Os workflows usam **labels no Pull Request** para determinar onde fazer deploy:

| Label | Cloud | Workflow Acionado |
|-------|-------|------------------|
| `deploy:aws` | Amazon Web Services | `.github/workflows/deploy-aws-eks.yml` |
| `deploy:azure` | Microsoft Azure | `.github/workflows/deploy-azure-aks.yml` |
| `deploy:oracle` | Oracle Cloud | `.github/workflows/deploy-oracle-oke.yml` |

**Como usar:**
1. Crie um Pull Request para a branch `main`
2. Adicione a label correspondente ao cloud desejado
3. O workflow será executado automaticamente

**Exemplos:**
- ✅ Adicionar label `deploy:aws` → Deploy apenas na AWS
- ✅ Adicionar labels `deploy:aws` + `deploy:azure` → Deploy nas duas clouds
- ❌ Sem label → Nenhum deploy é executado

### Componentes Deployados

- **Orthanc PACS Server** (porta 8042) - Gerenciamento de imagens DICOM
- **Inference API** (porta 8000) - API de inferência ML com TorchXRayVision
- **Persistent Storage** - Armazenamento de imagens DICOM
- **Load Balancers** - Exposição pública dos serviços

---

## 🔧 Pré-requisitos Gerais

### 1. Cluster Kubernetes

Você precisa ter um cluster Kubernetes rodando em um dos seguintes providers:
- **AWS EKS** (Elastic Kubernetes Service)
- **Azure AKS** (Azure Kubernetes Service)
- **Oracle OKE** (Oracle Kubernetes Engine)

### 2. Container Registry

- **AWS:** Amazon ECR (Elastic Container Registry)
- **Azure:** Azure Container Registry (ACR)
- **Oracle:** Oracle Container Infrastructure Registry (OCIR)

### 3. GitHub Repository Secrets

Configure os secrets necessários no GitHub:
- Settings → Secrets and variables → Actions → New repository secret

---

## ☁️ Deploy na AWS (EKS)

### Pré-requisitos AWS

#### 1. Criar Cluster EKS

```bash
# Via AWS CLI
aws eks create-cluster \
  --name mini-pacs-ai-cluster \
  --region us-east-1 \
  --kubernetes-version 1.28 \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/EKSClusterRole \
  --resources-vpc-config subnetIds=subnet-xxx,subnet-yyy,securityGroupIds=sg-xxx

# Via eksctl (recomendado)
eksctl create cluster \
  --name mini-pacs-ai-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5
```

#### 2. Criar ECR Repository

```bash
aws ecr create-repository \
  --repository-name mini-pacs-ai/inference-api \
  --region us-east-1
```

#### 3. Configurar IAM Role para GitHub Actions

```bash
# Criar trust policy para GitHub OIDC
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
EOF

# Criar role
aws iam create-role \
  --role-name GitHubActionsEKSRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name GitHubActionsEKSRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

aws iam attach-role-policy \
  --role-name GitHubActionsEKSRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

### GitHub Secrets para AWS

Configure os seguintes secrets no GitHub:

| Secret Name | Descrição | Exemplo |
|-------------|-----------|---------|
| `AWS_ROLE_TO_ASSUME` | ARN da role IAM | `arn:aws:iam::123456789012:role/GitHubActionsEKSRole` |
| `AWS_ACCOUNT_ID` | ID da conta AWS | `123456789012` |

### Personalização do Workflow AWS

Edite `.github/workflows/deploy-aws-eks.yml`:

```yaml
env:
  AWS_REGION: us-east-1              # Sua região
  EKS_CLUSTER_NAME: mini-pacs-ai-cluster
  ECR_REPOSITORY: mini-pacs-ai/inference-api
```

### Deploy

```bash
# Criar PR para main
git checkout -b feature/my-feature
git add .
git commit -m "feat: my new feature"
git push origin feature/my-feature

# Abrir PR no GitHub → Workflow inicia automaticamente
```

### Verificar Deploy

```bash
# Configurar kubectl
aws eks update-kubeconfig \
  --region us-east-1 \
  --name mini-pacs-ai-cluster

# Verificar pods
kubectl get pods -n mini-pacs-ai

# Verificar services
kubectl get svc -n mini-pacs-ai

# Testar API
LOAD_BALANCER=$(kubectl get svc aws-inference-api -n mini-pacs-ai -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://${LOAD_BALANCER}:8000/health
```

---

## ☁️ Deploy no Azure (AKS)

### Pré-requisitos Azure

#### 1. Criar Resource Group

```bash
az group create \
  --name mini-pacs-ai-rg \
  --location eastus
```

#### 2. Criar Cluster AKS

```bash
az aks create \
  --resource-group mini-pacs-ai-rg \
  --name mini-pacs-ai-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --kubernetes-version 1.28.0 \
  --enable-managed-identity \
  --generate-ssh-keys
```

#### 3. Criar Azure Container Registry

```bash
az acr create \
  --resource-group mini-pacs-ai-rg \
  --name minpacsaiacr \
  --sku Premium

# Attach ACR to AKS
az aks update \
  --resource-group mini-pacs-ai-rg \
  --name mini-pacs-ai-cluster \
  --attach-acr minpacsaiacr
```

#### 4. Criar Service Principal para GitHub Actions

```bash
# Criar service principal
az ad sp create-for-rbac \
  --name "GitHubActionsAKS" \
  --role contributor \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/mini-pacs-ai-rg \
  --sdk-auth

# Output será usado no secret AZURE_CREDENTIALS
```

### GitHub Secrets para Azure

| Secret Name | Descrição | Formato |
|-------------|-----------|---------|
| `AZURE_CREDENTIALS` | JSON do service principal | `{"clientId": "...", "clientSecret": "...", ...}` |

### Personalização do Workflow Azure

Edite `.github/workflows/deploy-azure-aks.yml`:

```yaml
env:
  AZURE_REGION: eastus
  AKS_CLUSTER_NAME: mini-pacs-ai-cluster
  ACR_NAME: minpacsaiacr
  RESOURCE_GROUP: mini-pacs-ai-rg
```

### Deploy

```bash
# Criar PR para main → Workflow inicia automaticamente
git push origin feature/my-feature
```

### Verificar Deploy

```bash
# Configurar kubectl
az aks get-credentials \
  --resource-group mini-pacs-ai-rg \
  --name mini-pacs-ai-cluster

# Verificar pods
kubectl get pods -n mini-pacs-ai

# Testar API
LOAD_BALANCER=$(kubectl get svc azure-inference-api -n mini-pacs-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://${LOAD_BALANCER}:8000/health
```

---

## ☁️ Deploy no Oracle (OKE)

### Pré-requisitos Oracle

#### 1. Criar Cluster OKE

```bash
# Via OCI Console ou CLI
oci ce cluster create \
  --compartment-id ocid1.compartment.oc1..xxx \
  --name mini-pacs-ai-cluster \
  --vcn-id ocid1.vcn.oc1.iad.xxx \
  --kubernetes-version v1.28.0 \
  --service-lb-subnet-ids '["ocid1.subnet.oc1.iad.xxx"]'
```

#### 2. Configurar OCI CLI

```bash
# Gerar API key
mkdir -p ~/.oci
oci setup config

# Output:
# - ~/.oci/config (configuração)
# - ~/.oci/oci_api_key.pem (chave privada)
```

#### 3. Criar Auth Token para OCIR

```bash
# Via OCI Console:
# Identity → Users → Your User → Auth Tokens → Generate Token
# Salve o token (não será exibido novamente)
```

### GitHub Secrets para Oracle

| Secret Name | Descrição | Exemplo |
|-------------|-----------|---------|
| `OCI_USERNAME` | Username OCIR | `tenancy-namespace/oracleidentitycloudservice/user@example.com` |
| `OCI_AUTH_TOKEN` | Auth token gerado | `<auth-token>` |
| `OCI_CLI_CONFIG` | Conteúdo de ~/.oci/config | `[DEFAULT]\nuser=ocid1...` |
| `OCI_CLI_KEY_CONTENT` | Conteúdo de ~/.oci/oci_api_key.pem | `-----BEGIN RSA PRIVATE KEY-----\n...` |

### Personalização do Workflow Oracle

Edite `.github/workflows/deploy-oracle-oke.yml`:

```yaml
env:
  OCI_REGION: us-ashburn-1
  OKE_CLUSTER_ID: ocid1.cluster.oc1.iad.xxxxx  # Seu cluster OCID
  OCIR_REGION: iad
  OCI_TENANCY_NAMESPACE: your-tenancy-namespace
```

### Deploy

```bash
# Criar PR para main → Workflow inicia automaticamente
git push origin feature/my-feature
```

### Verificar Deploy

```bash
# Configurar kubectl
oci ce cluster create-kubeconfig \
  --cluster-id ocid1.cluster.oc1.iad.xxx \
  --file $HOME/.kube/config \
  --region us-ashburn-1

# Verificar pods
kubectl get pods -n mini-pacs-ai

# Testar API
LOAD_BALANCER=$(kubectl get svc oci-inference-api -n mini-pacs-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://${LOAD_BALANCER}:8000/health
```

---

## 🔒 Segurança

### Security Scanning

Todos os workflows incluem **Trivy vulnerability scanner**:
- Scans automáticos de imagens Docker
- Upload de resultados para GitHub Security
- Bloqueio de deploy em caso de vulnerabilidades críticas

### Secrets Management

**Não commite secrets no código!**

✅ **Correto:**
```yaml
# Usar GitHub Secrets
password: ${{ secrets.DB_PASSWORD }}
```

❌ **Errado:**
```yaml
# NUNCA faça isso
password: mySecretPassword123
```

### Network Security

- LoadBalancers configurados para acesso público (alterar se necessário)
- DICOM port (4242) exposto apenas para Orthanc
- API port (8000) exposto publicamente

**Para ambiente produção, considere:**
- Usar ingress controllers (NGINX, Traefik)
- Configurar SSL/TLS certificates
- Implementar network policies
- Usar private endpoints

---

## 🎯 Workflows GitHub Actions

### Trigger

Todos os workflows são acionados por **Pull Requests para main**:

```yaml
on:
  pull_request:
    branches:
      - main
    types: [opened, synchronize, reopened]
```

### Jobs

Cada workflow tem 3 jobs principais:

1. **build-and-push** - Build e push da imagem Docker
2. **deploy-to-{cloud}** - Deploy no cluster Kubernetes
3. **security-scan** - Scan de vulnerabilidades

### Outputs

Cada workflow comenta no PR com:
- ✅ Imagem Docker buildada (tag, digest)
- ✅ Endpoints dos serviços deployados
- ✅ Comandos para verificar e testar

---

## 📊 Recursos Kubernetes

### Namespaces

- **mini-pacs-ai** - Namespace principal do projeto

### Deployments

| Nome | Replicas | CPU | Memory |
|------|----------|-----|--------|
| `{cloud}-orthanc` | 1 | 250m-1000m | 512Mi-2Gi |
| `{cloud}-inference-api` | 2 | 1000m-2000m | 4Gi-8Gi |

### Services

| Nome | Type | Ports |
|------|------|-------|
| `{cloud}-orthanc` | LoadBalancer | 8042 (HTTP), 4242 (DICOM) |
| `{cloud}-inference-api` | LoadBalancer | 8000 (HTTP) |

### Storage

| Nome | Type | Size | StorageClass |
|------|------|------|--------------|
| `orthanc-storage` | PVC | 50Gi | AWS: gp3, Azure: managed-premium, OCI: oci-bv |

---

## 🧪 Testando o Deploy

### 1. Health Check

```bash
# Get API endpoint
API_URL=$(kubectl get svc {cloud}-inference-api -n mini-pacs-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health
curl http://${API_URL}:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### 2. Test Prediction

```bash
# Upload DICOM e fazer predição
curl -X POST http://${API_URL}:8000/predict \
  -F "dicom_file=@exam.dcm"
```

### 3. Test Mask Generation

```bash
# Gerar máscaras Grad-CAM
curl -X POST http://${API_URL}:8000/generate_masks \
  -F "dicom_file=@exam.dcm" \
  -F "top_n=3"
```

### 4. Access Orthanc

```bash
# Get Orthanc endpoint
ORTHANC_URL=$(kubectl get svc {cloud}-orthanc -n mini-pacs-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Open in browser
open http://${ORTHANC_URL}:8042
```

---

## 🐛 Troubleshooting

### Pod não inicia

```bash
# Ver logs
kubectl logs -n mini-pacs-ai {cloud}-inference-api-xxx

# Descrever pod
kubectl describe pod -n mini-pacs-ai {cloud}-inference-api-xxx
```

### Imagem não encontrada

```bash
# Verificar se imagem existe no registry
# AWS
aws ecr describe-images --repository-name mini-pacs-ai/inference-api

# Azure
az acr repository show-tags --name minpacsaiacr --repository mini-pacs-ai/inference-api

# Oracle
oci artifacts container image list --compartment-id xxx
```

### LoadBalancer pending

```bash
# Verificar eventos
kubectl get events -n mini-pacs-ai --sort-by='.lastTimestamp'

# Verificar service
kubectl describe svc {cloud}-inference-api -n mini-pacs-ai
```

### Storage issues

```bash
# Verificar PVC
kubectl get pvc -n mini-pacs-ai

# Descrever PVC
kubectl describe pvc orthanc-storage -n mini-pacs-ai
```

---

## 📚 Referências

### Kustomize

- **Base:** `k8s/base/` - Manifestos comuns a todos os clouds
- **Overlays:** `k8s/overlays/{aws,azure,oracle}/` - Customizações por cloud

### GitHub Actions

- **Workflows:** `.github/workflows/deploy-{aws,azure,oracle}-*.yml`
- **Docs:** https://docs.github.com/en/actions

### Cloud Providers

- **AWS EKS:** https://docs.aws.amazon.com/eks/
- **Azure AKS:** https://docs.microsoft.com/azure/aks/
- **Oracle OKE:** https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm

---

## 🔄 Rollback

### Via kubectl

```bash
# Listar revisions
kubectl rollout history deployment/{cloud}-inference-api -n mini-pacs-ai

# Rollback para versão anterior
kubectl rollout undo deployment/{cloud}-inference-api -n mini-pacs-ai

# Rollback para versão específica
kubectl rollout undo deployment/{cloud}-inference-api -n mini-pacs-ai --to-revision=2
```

### Via Kustomize

```bash
# Deploy versão anterior
cd k8s/overlays/{cloud}
kustomize edit set image mini-pacs-ai/inference-api=registry/repo:previous-tag
kustomize build . | kubectl apply -f -
```

---

## 🚦 Monitoramento

### Logs

```bash
# Logs em tempo real
kubectl logs -f -n mini-pacs-ai {cloud}-inference-api-xxx

# Logs de todos os pods
kubectl logs -n mini-pacs-ai -l app=inference-api --tail=100
```

### Métricas

```bash
# Top pods (CPU/Memory)
kubectl top pods -n mini-pacs-ai

# Top nodes
kubectl top nodes
```

### Recomendações

Para produção, considere:
- **Prometheus + Grafana** - Métricas e dashboards
- **ELK Stack** - Logs centralizados
- **Jaeger** - Distributed tracing
- **Cloud provider monitoring** - CloudWatch, Azure Monitor, OCI Monitoring

---

**Última atualização:** 2025-11-04 | **Versão:** 1.4.0+
