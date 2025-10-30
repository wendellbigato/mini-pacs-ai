"""
API REST para inferência de achados radiológicos em imagens DICOM.
Utiliza modelo TorchXRayVision pré-treinado.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import logging

from .model import get_model
from .preprocess import preprocess_dicom, get_dicom_metadata
from .schemas import PredictionResponse, HealthResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Cria aplicação FastAPI
app = FastAPI(
    title="Mini PACS AI - Inference API",
    description="API para predição de achados radiológicos em imagens DICOM usando TorchXRayVision",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """
    Carrega o modelo na inicialização da aplicação.
    """
    logger.info("Iniciando API de inferência...")
    try:
        model = get_model()
        logger.info(f"Modelo carregado com sucesso: {len(model.labels)} labels")
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        raise


@app.get("/", tags=["Health"])
async def root():
    """
    Endpoint raiz - informações básicas da API.
    """
    return {
        "message": "Mini PACS AI - Inference API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Verifica o status da API e do modelo.
    """
    try:
        model = get_model()
        return HealthResponse(status="healthy", model_loaded=True)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(status="unhealthy", model_loaded=False)


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
async def predict(dicom_file: UploadFile = File(..., description="Arquivo DICOM para inferência")):
    """
    Realiza predição de achados radiológicos em uma imagem DICOM.

    Args:
        dicom_file: Arquivo DICOM enviado via multipart/form-data

    Returns:
        PredictionResponse com probabilidades para cada achado radiológico

    Raises:
        HTTPException: Em caso de erro no processamento
    """
    try:
        # Lê bytes do arquivo
        logger.info(f"Recebendo arquivo DICOM: {dicom_file.filename}")
        dicom_bytes = await dicom_file.read()

        # Valida se arquivo não está vazio
        if not dicom_bytes:
            raise HTTPException(status_code=400, detail="Arquivo DICOM vazio")

        # Extrai metadados (opcional)
        try:
            metadata = get_dicom_metadata(dicom_bytes)
            logger.info(f"Metadados extraídos: {metadata}")
        except Exception as e:
            logger.warning(f"Erro ao extrair metadados: {e}")
            metadata = None

        # Pré-processa DICOM
        logger.info("Pré-processando imagem DICOM...")
        tensor = preprocess_dicom(dicom_bytes)
        logger.info(f"Tensor shape: {tensor.shape}")

        # Executa inferência
        logger.info("Executando inferência...")
        model = get_model()
        probabilities = model.predict(tensor)

        # Ordena probabilidades em ordem decrescente
        probabilities = dict(
            sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        )

        logger.info(f"Inferência concluída. Top 3: {list(probabilities.items())[:3]}")

        return PredictionResponse(probabilities=probabilities, metadata=metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /predict: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar DICOM: {str(e)}")


@app.get("/labels", tags=["Inference"])
async def get_labels():
    """
    Retorna os labels (achados radiológicos) que o modelo pode predizer.
    """
    try:
        model = get_model()
        return {"labels": model.labels, "count": len(model.labels)}
    except Exception as e:
        logger.error(f"Erro ao buscar labels: {e}")
        raise HTTPException(status_code=500, detail=str(e))
