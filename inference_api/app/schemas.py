"""
Schemas Pydantic para validação e documentação da API.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional


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
