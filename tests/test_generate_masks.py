#!/usr/bin/env python3
"""
Teste para o endpoint /generate_masks (recomendado v1.3.0+).
Uso: python tests/test_generate_masks.py <caminho-para-arquivo.dcm>
"""
import sys
import requests
from pathlib import Path


def test_generate_masks(dicom_path: str, top_n: int = 3):
    """Testa o endpoint /generate_masks com um arquivo DICOM."""

    # Valida arquivo
    file_path = Path(dicom_path)
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {dicom_path}")
        sys.exit(1)

    if not file_path.suffix.lower() in ['.dcm', '.dicom']:
        print(f"⚠️  Aviso: Arquivo não parece ser DICOM (extensão: {file_path.suffix})")

    # Configuração
    api_url = "http://localhost:8000/generate_masks"

    print("🧪 Testando endpoint /generate_masks...")
    print(f"📁 Arquivo: {file_path.name}")
    print(f"📊 Tamanho: {file_path.stat().st_size / 1024:.2f} KB")
    print(f"🎯 Top N: {top_n}")
    print("-" * 60)

    # Faz a requisição
    try:
        with open(file_path, "rb") as f:
            files = {"dicom_file": (file_path.name, f, "application/dicom")}
            params = {"top_n": top_n, "use_official_preprocessing": True}
            response = requests.post(api_url, files=files, params=params, timeout=60)

        # Processa resposta
        if response.status_code == 200:
            data = response.json()

            print("✅ Geração de máscaras bem-sucedida!\n")

            # Probabilidades
            print("📊 Probabilidades:")
            print("-" * 60)
            for i, (finding, prob) in enumerate(sorted(
                data["probabilities"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10], 1):
                bar = "█" * int(prob * 50)
                print(f"{i:2}. {finding:30} {prob:6.1%} {bar}")

            # Máscaras geradas
            print(f"\n🎭 Máscaras Grad-CAM Geradas: {len(data['heatmaps'])}")
            print("-" * 60)
            for i, heatmap_data in enumerate(data['heatmaps'], 1):
                pathology = heatmap_data['pathology']
                prob = heatmap_data['probability']
                has_heatmap = bool(heatmap_data.get('heatmap_base64'))
                has_mask = bool(heatmap_data.get('mask_base64'))

                print(f"{i}. {pathology:30} {prob:6.1%}")
                print(f"   ✓ Heatmap: {'Sim' if has_heatmap else 'Não'}")
                print(f"   ✓ Máscara: {'Sim' if has_mask else 'Não'}")

            # Metadados
            if data.get("metadata"):
                print("\n📋 Metadados DICOM:")
                print("-" * 60)
                for key, value in data["metadata"].items():
                    print(f"  {key:20}: {value}")

            print("\n" + "=" * 60)
            print("✅ Teste concluído com sucesso!")
            print("\n💡 Dica: Use orthanc_analysis.ipynb para visualizar as máscaras")

        else:
            print(f"❌ Erro {response.status_code}: {response.reason}\n")
            print("📝 Detalhes:")
            try:
                error_data = response.json()
                import json
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Verifique se o serviço está rodando: docker compose ps")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout na requisição (>60s)")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tests/test_generate_masks.py <caminho-para-arquivo.dcm> [top_n]")
        print("\nExemplo:")
        print("  python tests/test_generate_masks.py ~/Downloads/chest_xray.dcm")
        print("  python tests/test_generate_masks.py ~/Downloads/chest_xray.dcm 5")
        sys.exit(1)

    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    test_generate_masks(sys.argv[1], top_n)
