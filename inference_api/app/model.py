"""
Módulo responsável por carregar e executar o modelo TorchXRayVision.
"""
import torch
import torchxrayvision as xrv
import numpy as np
from typing import Dict


class XRayModel:
    """
    Wrapper para o modelo TorchXRayVision pré-treinado.
    """

    def __init__(self, device: str = "cpu"):
        """
        Inicializa o modelo pré-treinado.

        Args:
            device: Device para executar o modelo ('cpu' ou 'cuda')
        """
        self.device = device
        print(f"Carregando modelo TorchXRayVision no device: {device}")

        # Carrega modelo DenseNet pré-treinado para raio-x de tórax
        self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
        self.model.to(device)
        self.model.eval()

        # Labels que o modelo prediz
        self.labels = self.model.pathologies

        print(f"Modelo carregado com sucesso. Labels disponíveis: {len(self.labels)}")

    def predict(self, tensor: torch.Tensor) -> Dict[str, float]:
        """
        Executa predição no tensor da imagem.

        Args:
            tensor: Tensor da imagem pré-processada [1, 1, H, W]

        Returns:
            Dicionário com probabilidades para cada achado radiológico
        """
        with torch.no_grad():
            tensor = tensor.to(self.device)
            outputs = self.model(tensor)

            # Converte para probabilidades com sigmoid
            probabilities = torch.sigmoid(outputs).cpu().numpy()[0]

            # Cria dicionário label: probabilidade
            results = {
                label: float(prob)
                for label, prob in zip(self.labels, probabilities)
            }

        return results


# Instância global do modelo (carregada no startup da API)
_model_instance = None


def get_model() -> XRayModel:
    """
    Retorna a instância global do modelo (singleton).
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = XRayModel(device="cpu")
    return _model_instance
