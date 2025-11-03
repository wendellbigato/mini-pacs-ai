"""
Pré-processamento oficial usando pipeline TorchXRayVision.

Este módulo implementa o pipeline de pré-processamento recomendado
pela biblioteca TorchXRayVision, garantindo melhor acurácia pois
o modelo foi treinado com essas transformações específicas.

Referências:
- https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py
- https://github.com/mlmed/torchxrayvision/issues/9
"""
import io
import numpy as np
import pydicom
import torch
import torchvision.transforms as transforms
import torchxrayvision as xrv


def preprocess_dicom_official(dicom_bytes: bytes) -> torch.Tensor:
    """
    Pré-processa DICOM usando pipeline oficial TorchXRayVision.

    Diferenças vs. preprocess.py (pipeline simplificado):
    1. Normalização [-1024, 1024] (escala HU) ao invés de [0, 1]
    2. XRayCenterCrop() para focar região torácica
    3. XRayResizer(224) com interpolação específica para raio-X

    Args:
        dicom_bytes: Bytes do arquivo DICOM

    Returns:
        torch.Tensor: Tensor [1, 1, 224, 224] pronto para inferência
    """
    # Lê o arquivo DICOM
    dicom_file = io.BytesIO(dicom_bytes)
    dcm = pydicom.dcmread(dicom_file)

    # Extrai pixel array
    img = dcm.pixel_array.astype(np.float32)

    # Normalização oficial TorchXRayVision
    # Detecta max value automaticamente (8-bit=255, 12-bit=4095, 16-bit=65535)
    # Converte para escala HU [-1024, 1024] que é a escala de treinamento do modelo
    maxval = img.max()
    img = xrv.datasets.normalize(img, maxval)

    # Garante formato correto para as transformações
    # XRV espera [H, W] ou [C, H, W]
    if len(img.shape) == 2:
        img = img[None, ...]  # [1, H, W]

    # Pipeline de transformações oficial
    transform = transforms.Compose([
        xrv.datasets.XRayCenterCrop(),  # Crop central focando região torácica
        xrv.datasets.XRayResizer(224),  # Resize para 224x224
    ])

    img = transform(img)

    # Converte para tensor PyTorch
    if not isinstance(img, torch.Tensor):
        img = torch.from_numpy(img)

    # Garante formato [1, 1, 224, 224]
    if len(img.shape) == 2:
        img = img.unsqueeze(0).unsqueeze(0)
    elif len(img.shape) == 3:
        img = img.unsqueeze(0)

    return img.float()


def preprocess_dicom_official_from_path(dicom_path: str) -> torch.Tensor:
    """
    Versão que recebe caminho do arquivo ao invés de bytes.

    Args:
        dicom_path: Caminho para arquivo DICOM

    Returns:
        torch.Tensor: Tensor [1, 1, 224, 224] pronto para inferência
    """
    with open(dicom_path, "rb") as f:
        dicom_bytes = f.read()
    return preprocess_dicom_official(dicom_bytes)


def compare_preprocessing_outputs(dicom_bytes: bytes) -> dict:
    """
    Compara outputs dos dois métodos de pré-processamento.

    Útil para debug e validação.

    Args:
        dicom_bytes: Bytes do arquivo DICOM

    Returns:
        dict com estatísticas de comparação
    """
    from app.preprocess import preprocess_dicom  # Import local para evitar circular

    # Processa com ambos métodos
    tensor_current = preprocess_dicom(dicom_bytes)
    tensor_official = preprocess_dicom_official(dicom_bytes)

    # Calcula estatísticas
    diff = torch.abs(tensor_current - tensor_official)

    return {
        "current_stats": {
            "mean": float(tensor_current.mean()),
            "std": float(tensor_current.std()),
            "min": float(tensor_current.min()),
            "max": float(tensor_current.max()),
        },
        "official_stats": {
            "mean": float(tensor_official.mean()),
            "std": float(tensor_official.std()),
            "min": float(tensor_official.min()),
            "max": float(tensor_official.max()),
        },
        "differences": {
            "mean_absolute_diff": float(diff.mean()),
            "max_absolute_diff": float(diff.max()),
            "std_diff": float(diff.std()),
        }
    }
