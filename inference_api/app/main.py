"""
API REST para inferência de achados radiológicos em imagens DICOM.
Utiliza modelo TorchXRayVision pré-treinado.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import logging

from .model import get_model
from .preprocess import preprocess_dicom, get_dicom_metadata
from .preprocess_official import preprocess_dicom_official, compare_preprocessing_outputs
from .gradcam import TorchXRayVisionCAM, convert_heatmap_to_base64, generate_binary_mask_from_heatmap
from .nih_dataset import NIHDatasetManager, mask_to_base64, compare_gradcam_with_groundtruth
from .schemas import (
    PredictionResponse,
    HealthResponse,
    ComparePreprocessingResponse,
    PredictionWithHeatmapResponse,
    HeatmapData,
    PreprocessingStats,
    MasksResponse,
    ValidateMasksResponse,
    GroundTruthMask,
    ValidationResult
)
import torch
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import os

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
    version="1.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Gerenciador do NIH Dataset (opcional - usado para validação)
nih_manager = None


@app.on_event("startup")
async def startup_event():
    """
    Carrega o modelo na inicialização da aplicação.
    """
    global nih_manager

    logger.info("Iniciando API de inferência...")
    try:
        model = get_model()
        logger.info(f"Modelo carregado com sucesso: {len(model.labels)} labels")
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        raise

    # Tenta carregar NIH dataset (opcional - usado para validação)
    nih_dataset_path = os.getenv("NIH_DATASET_PATH")
    if nih_dataset_path:
        logger.info(f"Tentando carregar NIH dataset de: {nih_dataset_path}")
        nih_manager = NIHDatasetManager(nih_dataset_path)
        if nih_manager.is_available():
            logger.info("✓ NIH Dataset carregado para validação")
        else:
            logger.warning("✗ NIH Dataset não disponível (endpoints /masks não funcionarão)")
            nih_manager = None
    else:
        logger.info("NIH_DATASET_PATH não configurado (endpoints /masks não disponíveis)")


@app.get("/", tags=["Health"])
async def root():
    """
    Endpoint raiz - informações básicas da API.
    """
    features = [
        "/predict - Predição de achados radiológicos",
        "/generate_masks - Gera máscaras de segmentação Grad-CAM (recomendado)",
        "/predict_with_heatmap - Predição com heatmaps Grad-CAM (legacy)",
        "/compare_preprocessing - Compara métodos de pré-processamento",
        "/masks - Máscaras ground truth do NIH dataset (validação)",
        "/validate_masks - Valida Grad-CAM vs ground truth (validação)"
    ]

    return {
        "message": "Mini PACS AI - Inference API",
        "version": "1.3.0",
        "docs": "/docs",
        "features": features,
        "nih_dataset_available": nih_manager is not None and nih_manager.is_available()
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
async def predict(
    dicom_file: UploadFile = File(..., description="Arquivo DICOM para inferência", media_type="application/dicom"),
    use_official_preprocessing: bool = True
):
    """
    Realiza predição de achados radiológicos em uma imagem DICOM.

    Args:
        dicom_file: Arquivo DICOM enviado via multipart/form-data
        use_official_preprocessing: Se True, usa pipeline oficial TorchXRayVision
                                    (normalização HU [-1024, 1024]). Padrão: True
                                    Este método foi escolhido após análise comparativa
                                    que demonstrou melhor aderência ao modelo.

    Returns:
        PredictionResponse com probabilidades para cada achado radiológico

    Raises:
        HTTPException: Em caso de erro no processamento

    Note:
        O método oficial de pré-processamento foi escolhido como padrão após
        pesquisa que identificou diferença média de ~11% nas probabilidades
        comparado ao método anterior. O método oficial é mais consistente
        com o treinamento original do modelo DenseNet121.
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
        if use_official_preprocessing:
            logger.info("Pré-processando imagem DICOM (método oficial TorchXRayVision)...")
            tensor = preprocess_dicom_official(dicom_bytes)
        else:
            logger.info("Pré-processando imagem DICOM (método legado)...")
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


@app.post("/compare_preprocessing", response_model=ComparePreprocessingResponse, tags=["Analysis"])
async def compare_preprocessing(
    dicom_file: UploadFile = File(..., description="Arquivo DICOM para comparação", media_type="application/dicom")
):
    """
    Compara predições usando dois métodos de pré-processamento:
    1. Método atual (preprocess.py) - Normalização [0,1] + z-score
    2. Método oficial TorchXRayVision - Normalização [-1024,1024] HU scale

    Útil para validar qual método produz melhores resultados.

    Args:
        dicom_file: Arquivo DICOM para análise

    Returns:
        ComparePreprocessingResponse com predições de ambos métodos e diferenças
    """
    try:
        logger.info(f"Comparando pré-processamentos: {dicom_file.filename}")
        dicom_bytes = await dicom_file.read()

        if not dicom_bytes:
            raise HTTPException(status_code=400, detail="Arquivo DICOM vazio")

        # Obter estatísticas de comparação dos tensores
        preprocessing_comparison = compare_preprocessing_outputs(dicom_bytes)

        # Processar com método atual
        logger.info("Processando com método atual...")
        tensor_current = preprocess_dicom(dicom_bytes)

        # Processar com método oficial
        logger.info("Processando com método oficial...")
        tensor_official = preprocess_dicom_official(dicom_bytes)

        # Executar inferência com ambos
        model = get_model()

        probs_current = model.predict(tensor_current)
        probs_official = model.predict(tensor_official)

        # Calcular diferenças absolutas
        diff = {}
        for label in probs_current.keys():
            diff[label] = abs(probs_current[label] - probs_official[label])

        # Estatísticas agregadas
        diff_values = list(diff.values())
        statistics = {
            "mean_difference": sum(diff_values) / len(diff_values),
            "max_difference": max(diff_values),
            "std_difference": (
                sum((x - (sum(diff_values) / len(diff_values))) ** 2 for x in diff_values)
                / len(diff_values)
            ) ** 0.5,
        }

        # Ordenar por probabilidade (método oficial)
        probs_current_sorted = dict(sorted(probs_current.items(), key=lambda x: x[1], reverse=True))
        probs_official_sorted = dict(sorted(probs_official.items(), key=lambda x: x[1], reverse=True))
        diff_sorted = dict(sorted(diff.items(), key=lambda x: x[1], reverse=True))

        logger.info(
            f"Comparação concluída. Mean diff: {statistics['mean_difference']:.4f}, "
            f"Max diff: {statistics['max_difference']:.4f}"
        )

        return ComparePreprocessingResponse(
            current_method=probs_current_sorted,
            official_method=probs_official_sorted,
            absolute_differences=diff_sorted,
            statistics=statistics,
            preprocessing_stats={
                "current": PreprocessingStats(**preprocessing_comparison["current_stats"]),
                "official": PreprocessingStats(**preprocessing_comparison["official_stats"])
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /compare_preprocessing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao comparar pré-processamentos: {str(e)}")


@app.post("/predict_with_heatmap", response_model=PredictionWithHeatmapResponse, tags=["Visualization"])
async def predict_with_heatmap(
    dicom_file: UploadFile = File(..., description="Arquivo DICOM para inferência", media_type="application/dicom"),
    top_n: int = 5,
    use_official_preprocessing: bool = True
):
    """
    Realiza predição E gera heatmaps Grad-CAM para interpretação visual.

    Grad-CAM (Gradient-weighted Class Activation Mapping) destaca as regiões
    da imagem que mais influenciaram cada predição. Usado por visualizadores
    profissionais como Sante DICOM Viewer e Horos.

    Args:
        dicom_file: Arquivo DICOM
        top_n: Número de top achados para gerar heatmaps (padrão: 5)
        use_official_preprocessing: Se True, usa pipeline oficial TorchXRayVision (padrão: True)

    Returns:
        PredictionWithHeatmapResponse com probabilidades e heatmaps em base64

    Note:
        Heatmaps podem adicionar ~1-2s ao tempo de processamento.
    """
    try:
        logger.info(f"Gerando predição com heatmaps: {dicom_file.filename}")
        dicom_bytes = await dicom_file.read()

        if not dicom_bytes:
            raise HTTPException(status_code=400, detail="Arquivo DICOM vazio")

        # Extrair metadados
        try:
            metadata = get_dicom_metadata(dicom_bytes)
        except Exception as e:
            logger.warning(f"Erro ao extrair metadados: {e}")
            metadata = None

        # Pré-processar
        if use_official_preprocessing:
            logger.info("Usando pré-processamento oficial TorchXRayVision")
            tensor = preprocess_dicom_official(dicom_bytes)
        else:
            logger.info("Usando pré-processamento atual")
            tensor = preprocess_dicom(dicom_bytes)

        # Executar inferência
        model = get_model()
        probabilities = model.predict(tensor)

        # Inicializar Grad-CAM
        logger.info(f"Gerando heatmaps Grad-CAM para top {top_n} achados...")
        cam_generator = TorchXRayVisionCAM(model.model)

        # Gerar heatmaps para top N
        cam_results = cam_generator.generate_all_heatmaps(tensor, top_n=top_n)

        # Converter heatmaps e gerar máscaras binárias
        heatmaps_data = []
        for i, (pathology, prob, heatmap) in enumerate(
            zip(
                cam_results["class_names"],
                cam_results["probabilities"],
                cam_results["heatmaps"]
            )
        ):
            heatmap_base64 = convert_heatmap_to_base64(heatmap)

            # Gerar máscara binária (threshold adaptativo baseado na probabilidade)
            if prob > 0.7:
                threshold = 0.6
            elif prob > 0.5:
                threshold = 0.5
            else:
                threshold = 0.4

            mask_base64 = generate_binary_mask_from_heatmap(heatmap, threshold=threshold)

            heatmaps_data.append(
                HeatmapData(
                    pathology=pathology,
                    probability=prob,
                    heatmap_base64=heatmap_base64,
                    mask_base64=mask_base64
                )
            )

        # Ordenar probabilidades
        probabilities_sorted = dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True))

        logger.info(f"Heatmaps gerados com sucesso para {len(heatmaps_data)} achados")

        return PredictionWithHeatmapResponse(
            probabilities=probabilities_sorted,
            heatmaps=heatmaps_data,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /predict_with_heatmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar heatmaps: {str(e)}")


@app.post("/generate_masks", response_model=PredictionWithHeatmapResponse, tags=["Visualization"])
async def generate_masks(
    dicom_file: UploadFile = File(..., description="Arquivo DICOM para inferência", media_type="application/dicom"),
    top_n: int = 3,
    use_official_preprocessing: bool = True
):
    """
    Gera máscaras de segmentação Grad-CAM para achados radiológicos.

    Endpoint focado em máscaras de segmentação automática. Retorna as mesmas
    informações que /predict_with_heatmap, mas com semântica mais clara para
    geração de máscaras.

    Args:
        dicom_file: Arquivo DICOM
        top_n: Número de top achados para gerar máscaras (padrão: 3)
        use_official_preprocessing: Se True, usa pipeline oficial TorchXRayVision (padrão: True)

    Returns:
        PredictionWithHeatmapResponse com probabilidades, heatmaps e máscaras

    Note:
        - Máscaras são geradas automaticamente via Grad-CAM
        - NÃO são máscaras ground truth (anotações manuais)
        - Útil para visualização e localização automática de achados
        - Usado no notebook orthanc_analysis.ipynb
    """
    # Reutiliza a mesma lógica de /predict_with_heatmap
    return await predict_with_heatmap(dicom_file, top_n, use_official_preprocessing)


@app.get("/masks", response_model=MasksResponse, tags=["Validation"])
async def get_masks(
    sample_idx: int = 0,
    pathology: str = None
):
    """
    Retorna máscaras ground truth de uma amostra do NIH Dataset.

    Este endpoint é usado para VALIDAÇÃO científica, comparando predições Grad-CAM
    com máscaras anotadas manualmente. Requer NIH_DATASET_PATH configurado.

    Args:
        sample_idx: Índice da amostra no dataset (padrão: 0)
        pathology: Se especificado, busca amostra com esta patologia

    Returns:
        MasksResponse com imagem e máscaras ground truth em base64

    Note:
        - Dataset NIH: 112,120 imagens com máscaras de patologias
        - Este endpoint NÃO é necessário para inferência em produção
        - Usado apenas para validação e pesquisa
    """
    try:
        # Verifica se dataset está disponível
        if nih_manager is None or not nih_manager.is_available():
            return MasksResponse(
                dataset_available=False,
                message="NIH Dataset não configurado. Configure NIH_DATASET_PATH para usar este endpoint."
            )

        # Se pathology especificada, busca amostra
        if pathology:
            logger.info(f"Buscando amostra com patologia: {pathology}")
            found_idx = nih_manager.find_sample_with_pathology(pathology)
            if found_idx is None:
                return MasksResponse(
                    dataset_available=True,
                    message=f"Nenhuma amostra encontrada com patologia '{pathology}' nos primeiros 100 exemplos"
                )
            sample_idx = found_idx

        # Obtém amostra
        logger.info(f"Obtendo amostra {sample_idx}")
        sample = nih_manager.get_sample_with_masks(sample_idx)

        if sample is None:
            return MasksResponse(
                dataset_available=True,
                message=f"Erro ao obter amostra {sample_idx}"
            )

        # Converter imagem para base64
        image_np = sample['image'].squeeze().cpu().numpy()  # [H, W]
        image_normalized = (image_np - image_np.min()) / (image_np.max() - image_np.min())
        image_uint8 = (image_normalized * 255).astype(np.uint8)
        pil_img = Image.fromarray(image_uint8, mode='L')

        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"

        # Processar máscaras
        masks_data = []
        pathology_masks = sample.get('masks', {})

        for idx, pathology_name in enumerate(sample['pathologies']):
            has_label = sample['labels'][idx] == 1

            if has_label and pathology_masks and pathology_name in pathology_masks:
                mask = pathology_masks[pathology_name]

                # Estatísticas da máscara
                mask_area = mask.sum()
                total_pixels = mask.size
                coverage = float(mask_area / total_pixels * 100)

                # Converter máscara para base64
                mask_b64 = mask_to_base64(mask)

                masks_data.append(GroundTruthMask(
                    pathology=pathology_name,
                    has_mask=True,
                    mask_base64=mask_b64,
                    coverage_percentage=coverage
                ))
            elif has_label:
                # Tem label mas não tem máscara
                masks_data.append(GroundTruthMask(
                    pathology=pathology_name,
                    has_mask=False
                ))

        logger.info(f"Retornando {len(masks_data)} máscaras para amostra {sample_idx}")

        return MasksResponse(
            dataset_available=True,
            image_base64=image_base64,
            masks=masks_data,
            pathologies=sample['pathologies'],
            sample_idx=sample_idx,
            message=f"Amostra {sample_idx} do NIH dataset"
        )

    except Exception as e:
        logger.error(f"Erro no endpoint /masks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao obter máscaras: {str(e)}")


@app.post("/validate_masks", response_model=ValidateMasksResponse, tags=["Validation"])
async def validate_masks(
    dicom_file: UploadFile = File(..., description="Arquivo DICOM para validação", media_type="application/dicom"),
    nih_sample_idx: int = 0
):
    """
    Valida predições Grad-CAM comparando com máscaras ground truth do NIH Dataset.

    Este endpoint:
    1. Faz predição Grad-CAM na imagem DICOM enviada
    2. Obtém máscaras ground truth da amostra NIH especificada
    3. Calcula IoU (Intersection over Union) entre predições e ground truth
    4. Retorna métricas de validação

    Args:
        dicom_file: Arquivo DICOM para inferência
        nih_sample_idx: Índice da amostra NIH para comparação

    Returns:
        ValidateMasksResponse com IoU scores e avaliações

    Note:
        - IoU > 0.5: Excellent
        - IoU > 0.3: Good
        - IoU > 0.1: Fair
        - IoU <= 0.1: Poor
    """
    try:
        # Verifica se dataset está disponível
        if nih_manager is None or not nih_manager.is_available():
            return ValidateMasksResponse(
                dataset_available=False,
                message="NIH Dataset não configurado. Configure NIH_DATASET_PATH para usar este endpoint."
            )

        logger.info(f"Validando predições Grad-CAM com amostra NIH {nih_sample_idx}")

        # 1. Processar DICOM e gerar predições Grad-CAM
        dicom_bytes = await dicom_file.read()

        if not dicom_bytes:
            raise HTTPException(status_code=400, detail="Arquivo DICOM vazio")

        # Pré-processar
        tensor = preprocess_dicom_official(dicom_bytes)

        # Inferência + Grad-CAM
        model = get_model()
        probabilities = model.predict(tensor)

        cam_generator = TorchXRayVisionCAM(model.model)
        cam_results = cam_generator.generate_all_heatmaps(tensor, top_n=18)

        # Carregar imagem original DICOM
        import pydicom
        dcm = pydicom.dcmread(BytesIO(dicom_bytes))
        original_img = dcm.pixel_array

        # 2. Obter máscaras ground truth do NIH
        sample = nih_manager.get_sample_with_masks(nih_sample_idx)

        if sample is None:
            raise HTTPException(status_code=400, detail=f"Erro ao obter amostra NIH {nih_sample_idx}")

        pathology_masks = sample.get('masks', {})

        # 3. Comparar predições com ground truth
        validations = []
        from scipy.ndimage import label as scipy_label
        from skimage.transform import resize
        import cv2

        for idx, (pathology, prob, heatmap) in enumerate(
            zip(cam_results["class_names"], cam_results["probabilities"], cam_results["heatmaps"])
        ):
            # Só valida se probabilidade > 30% E existe máscara ground truth
            if prob < 0.30 or pathology not in pathology_masks:
                continue

            # Resize heatmap para tamanho original
            heatmap_resized = resize(heatmap, original_img.shape, order=1, mode='reflect', anti_aliasing=True)

            # Extrair bounding box do Grad-CAM
            threshold = heatmap_resized.max() * 0.6
            mask = (heatmap_resized > threshold).astype(np.uint8)

            if mask.sum() < 50:
                continue

            labeled_mask, num_features = scipy_label(mask)

            if num_features == 0:
                continue

            # Maior componente
            component_sizes = [(labeled_mask == i).sum() for i in range(1, num_features + 1)]
            largest_label = component_sizes.index(max(component_sizes)) + 1
            largest_component = (labeled_mask == largest_label).astype(np.uint8)

            contours, _ = cv2.findContours(largest_component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                continue

            x, y, w, h = cv2.boundingRect(contours[0])

            # Comparar com ground truth
            gt_mask = pathology_masks[pathology]

            # Resize ground truth para tamanho do DICOM
            gt_mask_resized = resize(gt_mask, original_img.shape, order=0, mode='constant', anti_aliasing=False)
            gt_mask_resized = (gt_mask_resized > 0.5).astype(np.uint8)

            # Calcular validação
            validation = compare_gradcam_with_groundtruth(
                (x, y, w, h),
                gt_mask_resized,
                original_img,
                pathology
            )

            validations.append(ValidationResult(**validation))

        # Calcular IoU médio
        average_iou = 0.0
        if validations:
            average_iou = sum(v.iou_score for v in validations) / len(validations)

        logger.info(f"Validação concluída: {len(validations)} comparações, IoU médio: {average_iou:.3f}")

        return ValidateMasksResponse(
            dataset_available=True,
            validations=validations,
            average_iou=average_iou,
            message=f"{len(validations)} patologias validadas com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /validate_masks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao validar máscaras: {str(e)}")
