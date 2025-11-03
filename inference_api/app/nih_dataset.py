"""
Módulo para carregar e processar máscaras ground truth do NIH Dataset.

O NIH Chest X-ray Dataset contém 112,120 imagens com máscaras de patologias
anotadas manualmente. Este módulo permite comparar predições Grad-CAM com
ground truth para validação científica.

Referências:
- Dataset: https://nihcc.app.box.com/v/ChestXray-NIHCC
- Paper: https://arxiv.org/abs/1705.02315
- TorchXRayVision: https://github.com/mlmed/torchxrayvision
"""
import io
import numpy as np
import torch
import torchxrayvision as xrv
from typing import Dict, List, Optional, Tuple
import base64
from PIL import Image


class NIHDatasetManager:
    """
    Gerenciador do NIH Dataset para validação de modelos.

    IMPORTANTE: Este dataset é usado apenas para VALIDAÇÃO, não para inferência.
    Para inferência em imagens novas, use o endpoint /predict_with_heatmap.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        """
        Inicializa o gerenciador do NIH dataset.

        Args:
            dataset_path: Caminho para o dataset NIH (se None, não carrega)
        """
        self.dataset_path = dataset_path
        self.dataset = None

        if dataset_path:
            self._load_dataset()

    def _load_dataset(self):
        """Carrega o NIH dataset com máscaras de patologias."""
        try:
            self.dataset = xrv.datasets.NIH_Dataset(
                imgpath=self.dataset_path,
                views=["PA", "AP"],
                unique_patients=False,
                pathology_masks=True  # ← Carrega máscaras ground truth
            )
            print(f"✓ NIH Dataset carregado: {len(self.dataset)} imagens")
        except Exception as e:
            print(f"✗ Erro ao carregar NIH dataset: {e}")
            print("  Nota: Dataset NIH não é necessário para inferência em produção")
            self.dataset = None

    def is_available(self) -> bool:
        """Verifica se o dataset está disponível."""
        return self.dataset is not None

    def get_sample_with_masks(self, idx: int = 0) -> Optional[Dict]:
        """
        Obtém uma amostra do dataset com suas máscaras.

        Args:
            idx: Índice da amostra

        Returns:
            Dict com keys: 'image', 'masks', 'labels', 'pathologies'
        """
        if not self.is_available():
            return None

        try:
            sample = self.dataset[idx]

            return {
                'image': sample['img'],  # [1, H, W]
                'masks': sample.get('pathology_masks', None),  # Dict de máscaras
                'labels': sample['lab'],  # Labels das patologias
                'pathologies': self.dataset.pathologies,
                'idx': idx
            }
        except Exception as e:
            print(f"Erro ao obter amostra {idx}: {e}")
            return None

    def find_sample_with_pathology(self, pathology: str, max_search: int = 100) -> Optional[int]:
        """
        Encontra uma amostra que contenha a patologia especificada.

        Args:
            pathology: Nome da patologia (ex: "Cardiomegaly")
            max_search: Número máximo de amostras a pesquisar

        Returns:
            Índice da amostra ou None se não encontrar
        """
        if not self.is_available():
            return None

        try:
            pathology_idx = self.dataset.pathologies.index(pathology)
        except ValueError:
            print(f"Patologia '{pathology}' não encontrada no dataset")
            return None

        for idx in range(min(max_search, len(self.dataset))):
            try:
                sample = self.dataset[idx]
                if sample['lab'][pathology_idx] == 1:  # Patologia presente
                    return idx
            except:
                continue

        return None


def calculate_iou(bbox: Tuple[int, int, int, int], mask: np.ndarray) -> float:
    """
    Calcula IoU (Intersection over Union) entre bounding box e máscara.

    Args:
        bbox: (x, y, w, h) do bounding box
        mask: Máscara binária [H, W]

    Returns:
        float: IoU score [0, 1]
    """
    x, y, w, h = bbox

    # Criar máscara do bbox
    bbox_mask = np.zeros_like(mask)
    bbox_mask[y:y+h, x:x+w] = 1

    # Calcular intersecção e união
    intersection = np.logical_and(bbox_mask, mask).sum()
    union = np.logical_or(bbox_mask, mask).sum()

    if union == 0:
        return 0.0

    return float(intersection / union)


def mask_to_base64(mask: np.ndarray, colormap: str = 'hot') -> str:
    """
    Converte máscara binária para imagem base64.

    Args:
        mask: Máscara binária [H, W]
        colormap: Colormap matplotlib ('hot', 'jet', 'viridis')

    Returns:
        str: Imagem PNG em base64
    """
    import matplotlib.pyplot as plt
    from io import BytesIO

    # Normaliza máscara
    mask_normalized = (mask - mask.min()) / (mask.max() - mask.min() + 1e-7)

    # Aplica colormap
    cmap = plt.get_cmap(colormap)
    colored = cmap(mask_normalized)
    colored = (colored[:, :, :3] * 255).astype(np.uint8)

    # Converte para PIL
    img = Image.fromarray(colored)

    # Salva em buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode base64
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{img_base64}"


def compare_gradcam_with_groundtruth(
    gradcam_bbox: Tuple[int, int, int, int],
    groundtruth_mask: np.ndarray,
    image: np.ndarray,
    pathology: str
) -> Dict:
    """
    Compara predição Grad-CAM com ground truth mask.

    Args:
        gradcam_bbox: (x, y, w, h) do Grad-CAM
        groundtruth_mask: Máscara ground truth [H, W]
        image: Imagem original [H, W]
        pathology: Nome da patologia

    Returns:
        Dict com métricas e visualizações
    """
    # Calcula IoU
    iou = calculate_iou(gradcam_bbox, groundtruth_mask)

    # Estatísticas da máscara
    mask_area = groundtruth_mask.sum()
    total_pixels = groundtruth_mask.size
    mask_coverage = mask_area / total_pixels

    # Converte máscara para base64
    mask_base64 = mask_to_base64(groundtruth_mask)

    return {
        'pathology': pathology,
        'iou_score': float(iou),
        'gradcam_bbox': {
            'x': int(gradcam_bbox[0]),
            'y': int(gradcam_bbox[1]),
            'w': int(gradcam_bbox[2]),
            'h': int(gradcam_bbox[3])
        },
        'groundtruth_stats': {
            'mask_area_pixels': int(mask_area),
            'total_pixels': int(total_pixels),
            'coverage_percentage': float(mask_coverage * 100)
        },
        'groundtruth_mask_base64': mask_base64,
        'evaluation': 'excellent' if iou > 0.5 else 'good' if iou > 0.3 else 'fair' if iou > 0.1 else 'poor'
    }
