"""
Módulo para geração de visualizações Grad-CAM (Class Activation Mapping).

Grad-CAM gera heatmaps de atenção mostrando quais regiões da imagem
foram mais importantes para a predição de cada achado radiológico.

Usado por visualizadores profissionais como Sante DICOM Viewer, Horos.

Referências:
- Paper: https://arxiv.org/abs/1610.02391
- pytorch-grad-cam: https://github.com/jacobgil/pytorch-grad-cam
"""
import numpy as np
import torch
import cv2
from pytorch_grad_cam import GradCAM
from typing import Optional


class TorchXRayVisionCAM:
    """
    Wrapper para gerar Grad-CAM em modelos TorchXRayVision.

    O modelo DenseNet121 do TorchXRayVision tem arquitetura específica
    onde a última camada convolucional está em model.model.features[-1].
    """

    def __init__(self, model):
        """
        Inicializa o gerador de CAM.

        Args:
            model: Modelo TorchXRayVision carregado
        """
        self.model = model
        self.model.eval()

        # Target layer: última convolucional do DenseNet121
        # Estrutura: model.model.features[-1] (DenseBlock final)
        try:
            self.target_layers = [model.model.features[-1]]
        except AttributeError:
            # Fallback se estrutura for diferente
            self.target_layers = [model.features[-1]]

        # Inicializa Grad-CAM
        self.cam = GradCAM(
            model=model,
            target_layers=self.target_layers
        )

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: Optional[int] = None
    ) -> np.ndarray:
        """
        Gera heatmap Grad-CAM para uma classe específica.

        Args:
            input_tensor: Tensor de entrada [1, 1, 224, 224]
            target_class_idx: Índice da classe alvo (None = maior probabilidade)

        Returns:
            np.ndarray: Heatmap [224, 224] com valores [0, 1]
        """
        # Se não especificar classe, usa a de maior probabilidade
        targets = None
        if target_class_idx is not None:
            from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
            targets = [ClassifierOutputTarget(target_class_idx)]

        # Gera CAM
        # grayscale_cam shape: [batch_size, height, width]
        grayscale_cam = self.cam(
            input_tensor=input_tensor,
            targets=targets
        )

        # Retorna primeiro item do batch
        return grayscale_cam[0, :]

    def overlay_heatmap_on_image(
        self,
        image: np.ndarray,
        heatmap: np.ndarray,
        colormap: int = cv2.COLORMAP_JET,
        alpha: float = 0.4
    ) -> np.ndarray:
        """
        Sobrepõe heatmap sobre imagem original.

        Args:
            image: Imagem original [H, W] ou [H, W, C]
            heatmap: Heatmap [H, W] com valores [0, 1]
            colormap: Colormap OpenCV (COLORMAP_JET, COLORMAP_HOT, etc.)
            alpha: Transparência do heatmap (0=transparente, 1=opaco)

        Returns:
            np.ndarray: Imagem RGB [H, W, 3] com heatmap sobreposto
        """
        # Normaliza imagem para [0, 1] se necessário
        if image.max() > 1.0:
            image = image / image.max()

        # Converte para RGB se grayscale
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)

        # Garante float32
        image = image.astype(np.float32)

        # Aplica colormap ao heatmap
        heatmap_colored = cv2.applyColorMap(
            np.uint8(255 * heatmap),
            colormap
        )
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        heatmap_colored = heatmap_colored.astype(np.float32) / 255.0

        # Sobrepõe
        overlay = (1 - alpha) * image + alpha * heatmap_colored

        # Clipa para [0, 1]
        overlay = np.clip(overlay, 0, 1)

        return overlay

    def generate_all_heatmaps(
        self,
        input_tensor: torch.Tensor,
        top_n: int = 5
    ) -> dict:
        """
        Gera heatmaps para as top N classes com maior probabilidade.

        Args:
            input_tensor: Tensor de entrada [1, 1, 224, 224]
            top_n: Número de top classes para gerar heatmaps

        Returns:
            dict: {
                "class_indices": [idx1, idx2, ...],
                "class_names": ["Cardiomegaly", ...],
                "probabilities": [0.8, 0.7, ...],
                "heatmaps": [heatmap1, heatmap2, ...]  # Each [224, 224]
            }
        """
        # Obter predições
        with torch.no_grad():
            outputs = self.model(input_tensor)

        # Top N classes
        probs = torch.sigmoid(outputs)[0]  # TorchXRayVision usa sigmoid
        top_probs, top_indices = torch.topk(probs, top_n)

        # Gera heatmap para cada
        heatmaps = []
        class_names = []

        for idx in top_indices:
            idx_int = int(idx)
            heatmap = self.generate_heatmap(input_tensor, idx_int)
            heatmaps.append(heatmap)
            class_names.append(self.model.pathologies[idx_int])

        return {
            "class_indices": top_indices.cpu().numpy().tolist(),
            "class_names": class_names,
            "probabilities": top_probs.cpu().numpy().tolist(),
            "heatmaps": heatmaps
        }


def convert_heatmap_to_base64(heatmap: np.ndarray, colormap: int = cv2.COLORMAP_JET) -> str:
    """
    Converte heatmap para string base64 para transmissão via JSON.

    Args:
        heatmap: Heatmap [H, W] com valores [0, 1]
        colormap: Colormap OpenCV

    Returns:
        str: Imagem PNG em base64
    """
    import base64
    from io import BytesIO
    from PIL import Image

    # Aplica colormap
    heatmap_colored = cv2.applyColorMap(
        np.uint8(255 * heatmap),
        colormap
    )
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

    # Converte para PIL Image
    img = Image.fromarray(heatmap_colored)

    # Salva em buffer como PNG
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode base64
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{img_base64}"


def generate_binary_mask_from_heatmap(
    heatmap: np.ndarray,
    threshold: float = 0.5,
    colormap: int = cv2.COLORMAP_HOT
) -> str:
    """
    Gera máscara binária a partir de heatmap Grad-CAM.

    Args:
        heatmap: Heatmap [H, W] com valores [0, 1]
        threshold: Threshold para binarização (valores > threshold = região de atenção)
        colormap: Colormap para visualização da máscara

    Returns:
        str: Máscara colorida em base64 (PNG)
    """
    import base64
    from io import BytesIO
    from PIL import Image

    # Binariza heatmap
    binary_mask = (heatmap > threshold).astype(np.uint8)

    # Aplica colormap (0 = preto, 1 = cor quente)
    mask_colored = cv2.applyColorMap(
        np.uint8(255 * binary_mask),
        colormap
    )
    mask_colored = cv2.cvtColor(mask_colored, cv2.COLOR_BGR2RGB)

    # Converte para PIL Image
    img = Image.fromarray(mask_colored)

    # Salva em buffer como PNG
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode base64
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{img_base64}"


def draw_roi_on_image(
    image: np.ndarray,
    heatmap: np.ndarray,
    pathology: str,
    probability: float,
    threshold: float = 0.6
) -> np.ndarray:
    """
    Desenha ROI (Region of Interest) estilo DICOM profissional sobre a imagem.

    Detecta região de maior atenção no heatmap e desenha elipse/círculo
    com label mostrando patologia e probabilidade.

    Args:
        image: Imagem original [H, W] ou [H, W, C]
        heatmap: Heatmap [H, W] com valores [0, 1]
        pathology: Nome da patologia
        probability: Probabilidade da predição
        threshold: Threshold para considerar região de interesse

    Returns:
        np.ndarray: Imagem RGB [H, W, 3] com ROI desenhado
    """
    # Normaliza imagem para [0, 1]
    if image.max() > 1.0:
        image = image / image.max()

    # Converte para RGB se grayscale
    if len(image.shape) == 2:
        image = np.stack([image] * 3, axis=-1)

    # Converte para uint8 para desenhar
    img_display = (image * 255).astype(np.uint8).copy()

    # Detecta região de maior atenção (threshold nos valores altos)
    mask = (heatmap > threshold).astype(np.uint8)

    # Se não houver região acima do threshold, usa threshold mais baixo
    if mask.sum() == 0:
        threshold = heatmap.max() * 0.5
        mask = (heatmap > threshold).astype(np.uint8)

    # Encontra contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # Pega maior contorno (região de maior atenção)
        largest_contour = max(contours, key=cv2.contourArea)

        # Fit elipse no contorno
        if len(largest_contour) >= 5:  # Precisa de pelo menos 5 pontos para fitEllipse
            ellipse = cv2.fitEllipse(largest_contour)
            center, axes, angle = ellipse

            # Desenha elipse (amarelo como nos viewers profissionais)
            cv2.ellipse(img_display, ellipse, color=(255, 255, 0), thickness=2)

            # Adiciona texto com pathology e probabilidade
            text = f"{pathology}: {probability:.2f}"

            # Posição do texto (acima da elipse)
            text_x = int(center[0] - 50)
            text_y = int(center[1] - axes[1]/2 - 15)

            # Garante que texto não saia da imagem
            text_y = max(20, text_y)
            text_x = max(5, min(text_x, img_display.shape[1] - 150))

            # Background semi-transparente para o texto
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(
                img_display,
                (text_x - 5, text_y - text_size[1] - 5),
                (text_x + text_size[0] + 5, text_y + 5),
                (0, 0, 0),
                -1
            )

            # Texto
            cv2.putText(
                img_display,
                text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

    return img_display


def create_professional_visualization(
    image: np.ndarray,
    heatmaps_data: list,
    top_n: int = 3
) -> np.ndarray:
    """
    Cria visualização profissional estilo DICOM com múltiplos ROIs.

    Desenha ROIs para as top N patologias com maior probabilidade,
    cada uma com cor diferente.

    Args:
        image: Imagem original [H, W] ou [H, W, C]
        heatmaps_data: Lista de dicts com keys: 'pathology', 'probability', 'heatmap'
        top_n: Número máximo de ROIs a desenhar

    Returns:
        np.ndarray: Imagem RGB [H, W, 3] com ROIs desenhados
    """
    # Normaliza imagem
    if image.max() > 1.0:
        image = image / image.max()

    # Converte para RGB se grayscale
    if len(image.shape) == 2:
        image = np.stack([image] * 3, axis=-1)

    # Converte para uint8
    img_display = (image * 255).astype(np.uint8).copy()

    # Cores diferentes para cada patologia (BGR format)
    colors = [
        (255, 255, 0),   # Amarelo (Cyan em BGR)
        (0, 255, 255),   # Amarelo claro (Yellow em BGR)
        (255, 0, 255),   # Magenta
        (0, 255, 0),     # Verde
        (255, 128, 0),   # Laranja
    ]

    # Processa top N heatmaps
    for idx, data in enumerate(heatmaps_data[:top_n]):
        heatmap = data['heatmap']
        pathology = data['pathology']
        probability = data['probability']
        color = colors[idx % len(colors)]

        # Detecta região de maior atenção
        threshold = 0.6
        mask = (heatmap > threshold).astype(np.uint8)

        if mask.sum() == 0:
            threshold = heatmap.max() * 0.5
            mask = (heatmap > threshold).astype(np.uint8)

        # Encontra contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            largest_contour = max(contours, key=cv2.contourArea)

            if len(largest_contour) >= 5:
                ellipse = cv2.fitEllipse(largest_contour)
                center, axes, angle = ellipse

                # Desenha elipse
                cv2.ellipse(img_display, ellipse, color=color, thickness=2)

                # Texto
                text = f"{pathology}: {probability:.2f}"

                # Posição do texto
                text_x = int(center[0] - 50)
                text_y = int(center[1] - axes[1]/2 - 15)
                text_y = max(20 + idx * 25, text_y)
                text_x = max(5, min(text_x, img_display.shape[1] - 150))

                # Background do texto
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(
                    img_display,
                    (text_x - 3, text_y - text_size[1] - 3),
                    (text_x + text_size[0] + 3, text_y + 3),
                    (0, 0, 0),
                    -1
                )

                # Texto
                cv2.putText(
                    img_display,
                    text,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

    return img_display
