# ============================================
# OPÇÃO 1: Jupyter Dedicado (RECOMENDADO)
# ============================================
# Serviço Jupyter separado com dependências mínimas

FROM python:3.11-slim

LABEL maintainer="Wendell Barreto"
LABEL description="Jupyter notebook para Mini PACS AI"

WORKDIR /workspace

# Copia requirements do notebook
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expõe porta Jupyter
EXPOSE 8888

# Comando padrão: Jupyter sem senha, aceita conexões externas
CMD ["jupyter", "notebook", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''"]
