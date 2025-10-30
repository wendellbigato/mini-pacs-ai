
# mini-pacs-ai — Plano de Implementação

## 0. Objetivo do Projeto

Criar um ambiente Docker com múltiplos serviços que simule um fluxo real de imagens médicas:
- Um PACS (Orthanc) rodando em container Docker para armazenar e servir exames DICOM.
- Uma API REST em outro container Docker expondo `/predict`, que:
  - recebe um arquivo DICOM via POST,
  - carrega a imagem,
  - executa um modelo pré-treinado TorchXRayVision em PyTorch
  - retorna probabilidades de achados radiológicos em formato JSON.
- Um notebook Jupyter que:
  1. lê todas as instâncias DICOM armazenadas no Orthanc via REST API,
  2. envia cada instância para `/predict`,
  3. exibe tanto a imagem (matplotlib) quanto as probabilidades retornadas.

Esse fluxo implementa exatamente os itens 1, 2 e 3 do enunciado do desafio. :contentReference[oaicite:1]{index=1}


---

## 1. Entregáveis finais exigidos

Ao final, o repositório GitHub privado deve conter (estrutura sugerida):

```text
mini-pacs-ai/
├─ docker-compose.yml
├─ README.md
├─ report/
│  └─ desafio_neuralmind.pdf          # relatório final
├─ orthanc/
│  ├─ orthanc.json                    # config do Orthanc
│  └─ data/                           # volume local (persistente)
├─ inference_api/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py                      # FastAPI + /predict
│     ├─ model.py                     # carregamento TorchXRayVision
│     ├─ preprocess.py                # DICOM -> tensor
│     └─ schemas.py                   # (pydantic response)
└─ notebooks/
   └─ orthanc_inference.ipynb         # notebook de integração Orthanc -> /predict
````

Além disso:

* `README.md` com instruções de uso para rodar os serviços, testar `/predict`, e executar o notebook.
* `desafio_neuralmind.pdf` com:

  * visão geral da solução,
  * dificuldades técnicas,
  * o que foi aprendizado novo,
  * o que já era conhecimento prévio.
    Isso é explicitamente pedido no enunciado. 

Links relevantes citados no desafio (devem aparecer no README):

* Orthanc: [https://www.orthanc-server.com/](https://www.orthanc-server.com/)
* Docker: [https://www.docker.com/](https://www.docker.com/)
* TorchXRayVision: [https://github.com/mlmed/torchxrayvision](https://github.com/mlmed/torchxrayvision)
* Dataset DICOM de teste (link fornecido pela banca):
  [https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing](https://drive.google.com/file/d/1Decc3rX_5oxF-4VvQxtWVqkV91O_Auf9/view?usp=sharing)
  Esses links foram fornecidos diretamente no enunciado oficial. 

---

## 2. Fases do trabalho

### Fase 1 — Infraestrutura Docker + Orthanc (PACS)

**Meta:** Subir um PACS Orthanc em container Docker, com dados persistentes e acesso via browser.

Tarefas:

1. Criar pasta `orthanc/` com:

   * `orthanc.json` (arquivo de configuração).
   * subpasta `data/` (vai virar volume local ligado ao /var/lib/orthanc/db no container).
2. Criar/atualizar `docker-compose.yml` com serviço `orthanc`:

   * imagem base: `orthanc/orthanc:latest`
   * portas expostas:

     * `8042:8042` → HTTP UI do Orthanc e REST API
     * `4242:4242` → porta DICOM
   * volumes:

     * `./orthanc/data:/var/lib/orthanc/db`
     * `./orthanc/orthanc.json:/etc/orthanc/orthanc.json:ro`
   * `restart: unless-stopped`
3. No `orthanc.json`, deixar desenvolvimento sem autenticação para facilitar testes:

   ```json
   {
     "Name": "LocalOrthanc",
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
4. Subir o serviço:

   ```bash
   docker compose up orthanc
   ```
5. Testar no browser:

   * Acessar `http://localhost:8042`
   * Ver a interface web do Orthanc.
6. Fazer upload manual de pelo menos um arquivo DICOM pelo painel web do Orthanc.

   * Esse passo cumpre a exigência de "acessar a interface web do Orthanc e enviar arquivos DICOM para armazenamento". 
   * IMPORTANTE: Os DICOMs mencionados no enunciado estão no link de Google Drive citado acima. 

Resultado esperado da fase:

* Orthanc rodando localmente em Docker.
* Volume persistente funcionando (dados não somem após `docker compose down`).
* Ao menos um exame armazenado.

### Fase 2 — API de Inferência `/predict`

**Meta:** Implementar uma API REST (FastAPI) que roda em outro container Docker e recebe um DICOM via POST `/predict`, retornando um dicionário com probabilidades encontradas pelo modelo pré-treinado TorchXRayVision. Isso atende o passo 2 do enunciado. 

Tarefas:

1. Criar pasta `inference_api/` com:

   * `Dockerfile`
   * `requirements.txt`
   * subpasta `app/` contendo `main.py`, `model.py`, `preprocess.py`, `schemas.py`.

2. `requirements.txt` deve incluir (mínimo):

   ```txt
   fastapi
   uvicorn[standard]
   pydantic
   pydicom
   pillow
   torch
   torchxrayvision
   numpy
   scikit-image
   matplotlib
   ```

3. `Dockerfile` base (CPU):

   ```dockerfile
   FROM python:3.11-slim

   ENV DEBIAN_FRONTEND=noninteractive \
       PYTHONUNBUFFERED=1 \
       PIP_NO_CACHE_DIR=1

   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential \
       git \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --upgrade pip && pip install -r requirements.txt

   COPY app ./app

   EXPOSE 8000
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

4. `model.py`:

   * Carregar o modelo pré-treinado `torchxrayvision` (por exemplo, `DenseNet` para raio-x de tórax).
   * Colocar o modelo em `eval()` e rodar em `cpu` por padrão.
   * Expor um método `predict(tensor)` que retorna `{label: probabilidade}`.

5. `preprocess.py`:

   * Ler o DICOM recebido.
   * Extrair `pixel_array` com `pydicom`.
   * Normalizar e redimensionar para o tamanho esperado pelo modelo (`224x224` para os modelos DenseNet).
   * Gerar um tensor `[1, 1, H, W]` com `torch.float32`.
   * Observação: o enunciado alerta explicitamente que o pré-processamento adequado do DICOM deve acontecer dentro do `/predict`. 

6. `schemas.py`:

   * Definir um `PredictionResponse` (Pydantic) para documentar o retorno em OpenAPI.

7. `main.py` (FastAPI):

   * endpoint `POST /predict`
   * recebe `UploadFile` (campo `"dicom_file"`)
   * roda o pré-processamento
   * roda o modelo
   * retorna JSON com as probabilidades.

8. Adicionar esse serviço ao `docker-compose.yml`:

   ```yaml
   inference-api:
     build: ./inference_api
     container_name: inference-api
     restart: unless-stopped
     ports:
       - "8000:8000"
     depends_on:
       - orthanc
   ```

9. Subir tudo:

   ```bash
   docker compose up --build
   ```

10. Testar manualmente em `http://localhost:8000/docs` (FastAPI gera Swagger UI automática):

    * Fazer upload do mesmo DICOM que foi armazenado no Orthanc.
    * Verificar se a resposta é um dicionário `{ "probabilities": { "finding1": 0.123, ... } }`.

Resultado esperado da fase:

* API de inferência funcional.
* Modelo TorchXRayVision rodando localmente em CPU.
* Rota `/predict` aceita um único arquivo DICOM e retorna probabilidades, conforme requerido. 

### Fase 3 — Notebook de Integração Orthanc → `/predict`

**Meta:** Criar um notebook Jupyter (`notebooks/orthanc_inference.ipynb`) que automatiza o fluxo pedido no passo 3 do enunciado. 

O notebook deve fazer, para TODAS as instâncias DICOM armazenadas no Orthanc:

1. Usar a API REST do Orthanc para listar instâncias DICOM.

   * `GET /instances` no Orthanc retorna uma lista de IDs das instâncias.
2. Baixar cada instância individualmente.

   * `GET /instances/{id}/file` retorna o arquivo DICOM bruto (.dcm).
3. Enviar esse arquivo DICOM (em memória) via `requests.post` para `http://localhost:8000/predict`.
4. Plotar a imagem da instância com `matplotlib` (usando `pydicom.dcmread` e `pixel_array`) e exibir também as probabilidades retornadas pela API.

Checklist das células principais do notebook:

* Imports + configuração (`requests`, `pydicom`, `matplotlib.pyplot`).
* Função `list_instances()` chamando `GET /instances`.
* Função `download_dicom(instance_id)` chamando `GET /instances/{id}/file`.
* Função `call_inference_api(dicom_bytes)` que faz POST multipart em `/predict`.
* Loop `for` sobre todas as instâncias:

  * baixar bytes
  * desenhar imagem com `plt.imshow(..., cmap='gray')`
  * imprimir resultados de inferência.

Resultado esperado da fase:

* O notebook roda localmente (com Orthanc e inference-api ativos).
* Para cada estudo salvo no Orthanc, você gera:

  * visualização da imagem,
  * probabilidades previstas.

Esse notebook é explicitamente um requisito de entrega. 

---

## 3. O que o Claude Code deve gerar / automatizar

### Arquivos de infra

* `docker-compose.yml` com serviços `orthanc` e `inference-api`.
* `orthanc/orthanc.json`.

### API de inferência

* `inference_api/requirements.txt`
* `inference_api/Dockerfile`
* `inference_api/app/model.py`
* `inference_api/app/preprocess.py`
* `inference_api/app/schemas.py`
* `inference_api/app/main.py`

### Notebook

* `notebooks/orthanc_inference.ipynb`

  * O Claude Code pode primeiro gerar uma versão `.py` sequencial (células marcadas com comentários `# %%`) que depois você converte manualmente em notebook via Jupyter/Lab/VSC.

### Documentação

* `README.md`

  * Descrevendo setup rápido, portas, como subir o compose, como testar `/predict`, como rodar o notebook, e apontando para os links oficiais (Orthanc, TorchXRayVision, Docker, dataset DICOM).
* `report/desafio_neuralmind.pdf`

  * O Claude Code pode gerar um `report/desafio_neuralmind.md` com as seções:

    1. Arquitetura da solução
    2. Fluxo técnico (Orthanc → API → Notebook)
    3. Dificuldades encontradas
    4. O que foi aprendizado novo
    5. O que já era conhecimento prévio
  * Depois você exporta esse `.md` para `.pdf` e coloca no repositório como pedido. 

---

## 4. Checklist de validação final

Use isso antes de entregar o repo:

* [ ] `docker-compose.yml` sobe `orthanc` e `inference-api` sem erro de build.
* [ ] Consigo acessar `http://localhost:8042` (Orthanc).
* [ ] Consigo fazer upload de um DICOM manualmente pela UI do Orthanc.
* [ ] O DICOM continua disponível depois de reiniciar os containers (volumes OK).
* [ ] Consigo acessar `http://localhost:8000/docs` (FastAPI/Swagger).
* [ ] Consigo fazer POST `/predict` enviando um DICOM qualquer e recebo probabilidades.
* [ ] Notebook:

  * [ ] Lista instâncias do Orthanc via `GET /instances`.
  * [ ] Baixa cada DICOM via `GET /instances/{id}/file`.
  * [ ] Faz POST `/predict` com cada DICOM.
  * [ ] Plota a imagem e imprime as probabilidades.
* [ ] README.md explica como rodar tudo.
* [ ] `report/desafio_neuralmind.pdf` existe e cobre:

  * funcionamento técnico da solução,
  * dificuldades,
  * aprendizado,
  * conhecimento prévio.
    Isso é obrigatório de acordo com o enunciado. 

---

## 5. Observações técnicas / pontos de atenção

1. **Persistência de dados DICOM**
   É obrigatório montar um volume Docker para o Orthanc, senão os arquivos somem ao parar o container. 

2. **Pré-processamento DICOM**
   O enunciado pede cuidado com o pré-processamento do DICOM dentro do `/predict` (redimensionar, normalizar, formato de tensor). Isso precisa ficar explícito no código da API e documentado no README. 

3. **TorchXRayVision**
   O TorchXRayVision já vem com modelos pré-treinados e retorna um dicionário de probabilidades de achados radiológicos, que é exatamente o que a rota `/predict` deve expor. 

4. **Segurança/credenciais**
   Para o desafio técnico local, `AuthenticationEnabled: false` no Orthanc acelera o desenvolvimento. Mas no PDF final você pode comentar que isso NÃO é seguro em produção (mostra maturidade).

5. **GPU vs CPU**
   A solução pode rodar inteiramente em CPU. Deixe isso claro no README para evitar expectativa de CUDA.

6. **Linguagem**
   A API pode ser implementada em Flask, FastAPI ou similar. Vamos seguir com FastAPI porque:

   * retorno JSON tipado (Pydantic),
   * documentação automática Swagger/UI,
   * mais "bonito" para avaliação.

7. **Comunicação entre serviços**
   O notebook roda fora do cluster Docker ou em outro container separado. Ele vai chamar:

   * Orthanc em `http://localhost:8042`
   * API em `http://localhost:8000`
     Isso simplifica a demonstração e evita ter que criar rede interna especial, e está dentro do escopo pedido. 

---

## 6. Próximo passo imediato

1. Criar o repositório privado `mini-pacs-ai`.
2. Adicionar este arquivo como `PLAN.md`.
3. Pedir ao Claude Code (ou gerar você mesmo) os seguintes artefatos, nesta ordem:

   * `docker-compose.yml` com serviços `orthanc` e `inference-api`.
   * `orthanc/orthanc.json`.
   * `inference_api/requirements.txt`.
   * `inference_api/Dockerfile`.
   * `inference_api/app/*.py` (main, model, preprocess, schemas).
4. Subir os serviços e testar manualmente `/predict`.
5. Criar o notebook `notebooks/orthanc_inference.ipynb` usando o fluxo descrito na Fase 3.
6. Criar `README.md` + rascunho de `report/desafio_neuralmind.md` (que depois vira PDF).

Quando tudo disso estiver funcional e versionado, o desafio está pronto para entrega. 

