"""
Schemas Pydantic para validação e documentação da API.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, List


class PredictionResponse(BaseModel):
    """
    Resposta do endpoint /predict com probabilidades de achados radiológicos.
    """

    probabilities: Dict[str, float] = Field(
        ...,
        description="Dicionário com probabilidades para cada achado radiológico",
        example={
            "Atelectasis": 0.123,
            "Cardiomegaly": 0.456,
            "Consolidation": 0.078,
            "Edema": 0.234,
            "Pleural Effusion": 0.567,
        },
    )

    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Metadados opcionais do arquivo DICOM",
        example={
            "patient_id": "123456",
            "study_date": "20240101",
            "modality": "CR",
        },
    )


class HealthResponse(BaseModel):
    """
    Resposta do endpoint /health.
    """

    status: str = Field(..., description="Status da API", example="healthy")
    model_loaded: bool = Field(
        ..., description="Indica se o modelo está carregado", example=True
    )


class PreprocessingStats(BaseModel):
    """
    Estatísticas de um método de pré-processamento.
    """
    mean: float = Field(..., description="Média dos valores do tensor")
    std: float = Field(..., description="Desvio padrão dos valores do tensor")
    min: float = Field(..., description="Valor mínimo do tensor")
    max: float = Field(..., description="Valor máximo do tensor")


class ComparePreprocessingResponse(BaseModel):
    """
    Resposta do endpoint /compare_preprocessing.
    """
    current_method: Dict[str, float] = Field(
        ...,
        description="Probabilidades usando método atual (preprocess.py)"
    )
    official_method: Dict[str, float] = Field(
        ...,
        description="Probabilidades usando método oficial TorchXRayVision"
    )
    absolute_differences: Dict[str, float] = Field(
        ...,
        description="Diferenças absolutas entre os dois métodos"
    )
    statistics: Dict[str, float] = Field(
        ...,
        description="Estatísticas agregadas das diferenças",
        example={
            "mean_difference": 0.0234,
            "max_difference": 0.0891,
            "std_difference": 0.0156
        }
    )
    preprocessing_stats: Dict[str, PreprocessingStats] = Field(
        ...,
        description="Estatísticas dos tensores pré-processados"
    )


class HeatmapData(BaseModel):
    """
    Dados de um heatmap Grad-CAM.
    """
    pathology: str = Field(..., description="Nome do achado radiológico")
    probability: float = Field(..., description="Probabilidade da predição")
    heatmap_base64: str = Field(..., description="Heatmap em base64 (PNG)")
    mask_base64: Optional[str] = Field(None, description="Máscara binária da região de atenção em base64 (PNG)")


class PredictionWithHeatmapResponse(BaseModel):
    """
    Resposta do endpoint /predict_with_heatmap.
    """
    probabilities: Dict[str, float] = Field(
        ...,
        description="Probabilidades de todos os achados"
    )
    heatmaps: List[HeatmapData] = Field(
        ...,
        description="Heatmaps Grad-CAM para top N achados"
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Metadados do DICOM"
    )


class GroundTruthMask(BaseModel):
    """
    Dados de uma máscara ground truth.
    """
    pathology: str = Field(..., description="Nome da patologia")
    has_mask: bool = Field(..., description="Se existe máscara para esta patologia")
    mask_base64: Optional[str] = Field(None, description="Máscara em base64 (PNG)")
    coverage_percentage: Optional[float] = Field(None, description="% da imagem coberta pela máscara")


class ValidationResult(BaseModel):
    """
    Resultado da validação Grad-CAM vs Ground Truth.
    """
    pathology: str = Field(..., description="Nome da patologia")
    iou_score: float = Field(..., description="IoU score (Intersection over Union)")
    gradcam_bbox: Dict[str, int] = Field(..., description="Bounding box do Grad-CAM: {x, y, w, h}")
    groundtruth_stats: Dict = Field(..., description="Estatísticas da máscara ground truth")
    groundtruth_mask_base64: str = Field(..., description="Máscara ground truth em base64")
    evaluation: str = Field(..., description="Avaliação: excellent/good/fair/poor")


class MasksResponse(BaseModel):
    """
    Resposta do endpoint /masks com máscaras ground truth.
    """
    dataset_available: bool = Field(..., description="Se o dataset NIH está disponível")
    image_base64: Optional[str] = Field(None, description="Imagem do dataset em base64")
    masks: Optional[List[GroundTruthMask]] = Field(None, description="Máscaras ground truth disponíveis")
    pathologies: Optional[List[str]] = Field(None, description="Lista de patologias do dataset")
    sample_idx: Optional[int] = Field(None, description="Índice da amostra no dataset")
    message: Optional[str] = Field(None, description="Mensagem informativa")


class ValidateMasksResponse(BaseModel):
    """
    Resposta do endpoint /validate_masks.
    """
    dataset_available: bool = Field(..., description="Se o dataset NIH está disponível")
    validations: Optional[List[ValidationResult]] = Field(None, description="Resultados das validações")
    average_iou: Optional[float] = Field(None, description="IoU médio de todas as validações")
    message: Optional[str] = Field(None, description="Mensagem informativa")
