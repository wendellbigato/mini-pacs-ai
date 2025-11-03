"""
Módulo responsável pelo pré-processamento de arquivos DICOM.
"""
import io
import numpy as np
import pydicom
import torch
from PIL import Image
from skimage import transform


def preprocess_dicom(dicom_bytes: bytes, target_size: int = 224) -> torch.Tensor:
    """
    Processa arquivo DICOM e retorna tensor normalizado para o modelo.

    Args:
        dicom_bytes: Bytes do arquivo DICOM
        target_size: Tamanho alvo da imagem (padrão: 224x224)

    Returns:
        Tensor PyTorch [1, 1, target_size, target_size]
    """
    # Lê o arquivo DICOM
    dicom_file = io.BytesIO(dicom_bytes)
    dcm = pydicom.dcmread(dicom_file)

    # Extrai pixel array
    pixel_array = dcm.pixel_array.astype(np.float32)

    # Normaliza para [0, 1]
    pixel_array = (pixel_array - pixel_array.min()) / (
        pixel_array.max() - pixel_array.min() + 1e-8
    )

    # Redimensiona para target_size x target_size
    if pixel_array.shape != (target_size, target_size):
        pixel_array = transform.resize(
            pixel_array, (target_size, target_size), mode="constant", preserve_range=True
        )

    # Converte para tensor [1, 1, H, W]
    # TorchXRayVision espera canal único (grayscale)
    tensor = torch.from_numpy(pixel_array).unsqueeze(0).unsqueeze(0).float()

    # Normaliza para média 0 e desvio padrão 1 (padrão ImageNet)
    # TorchXRayVision usa normalização específica, mas esta é adequada
    mean = tensor.mean()
    std = tensor.std()
    tensor = (tensor - mean) / (std + 1e-8)

    return tensor


def get_dicom_metadata(dicom_bytes: bytes) -> dict:
    """
    Extrai metadados úteis do arquivo DICOM.

    Args:
        dicom_bytes: Bytes do arquivo DICOM

    Returns:
        Dicionário com metadados
    """
    dicom_file = io.BytesIO(dicom_bytes)
    dcm = pydicom.dcmread(dicom_file)

    metadata = {
        "patient_id": str(dcm.get("PatientID", "N/A")),
        "study_date": str(dcm.get("StudyDate", "N/A")),
        "modality": str(dcm.get("Modality", "N/A")),
        "image_shape": str(dcm.pixel_array.shape) if hasattr(dcm, "pixel_array") else "N/A",
    }

    return metadata
