#!/usr/bin/env python3
"""
Script de teste para o endpoint /predict da API de inferência.
Uso: python test_predict.py <caminho-para-arquivo.dcm>
"""
import sys
import requests
from pathlib import Path


def test_predict(dicom_path: str):
    """Testa o endpoint /predict com um arquivo DICOM."""

    # Valida arquivo
    file_path = Path(dicom_path)
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {dicom_path}")
        sys.exit(1)

    if not file_path.suffix.lower() in ['.dcm', '.dicom']:
        print(f"⚠️  Aviso: Arquivo não parece ser DICOM (extensão: {file_path.suffix})")

    # Configuração
    api_url = "http://localhost:8000/predict"

    print("🧪 Testando API de Inferência...")
    print(f"📁 Arquivo: {file_path.name}")
    print(f"📊 Tamanho: {file_path.stat().st_size / 1024:.2f} KB")
    print("-" * 60)

    # Faz a requisição
    try:
        with open(file_path, "rb") as f:
            files = {"dicom_file": (file_path.name, f, "application/dicom")}
            response = requests.post(api_url, files=files, timeout=30)

        # Processa resposta
        if response.status_code == 200:
            data = response.json()

            print("✅ Predição bem-sucedida!\n")
            print("📊 Top 10 Achados Radiológicos:")
            print("-" * 60)

            for i, (finding, prob) in enumerate(list(data["probabilities"].items())[:10], 1):
                bar = "█" * int(prob * 50)
                print(f"{i:2}. {finding:25} {prob:6.1%} {bar}")

            if data.get("metadata"):
                print("\n📋 Metadados DICOM:")
                print("-" * 60)
                for key, value in data["metadata"].items():
                    print(f"  {key:15}: {value}")

            print("\n" + "=" * 60)
            print("✅ Teste concluído com sucesso!")

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
        print("❌ Erro: Timeout na requisição (>30s)")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_predict.py <caminho-para-arquivo.dcm>")
        print("\nExemplo:")
        print("  python test_predict.py ~/Downloads/chest_xray.dcm")
        sys.exit(1)

    test_predict(sys.argv[1])
