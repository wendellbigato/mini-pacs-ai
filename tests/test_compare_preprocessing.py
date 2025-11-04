#!/usr/bin/env python3
"""
Teste para o endpoint /compare_preprocessing.
Compara método anterior vs oficial TorchXRayVision.
Uso: python tests/test_compare_preprocessing.py <caminho-para-arquivo.dcm>
"""
import sys
import requests
from pathlib import Path


def test_compare_preprocessing(dicom_path: str):
    """Testa o endpoint /compare_preprocessing com um arquivo DICOM."""

    # Valida arquivo
    file_path = Path(dicom_path)
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {dicom_path}")
        sys.exit(1)

    if not file_path.suffix.lower() in ['.dcm', '.dicom']:
        print(f"⚠️  Aviso: Arquivo não parece ser DICOM (extensão: {file_path.suffix})")

    # Configuração
    api_url = "http://localhost:8000/compare_preprocessing"

    print("🧪 Testando endpoint /compare_preprocessing...")
    print(f"📁 Arquivo: {file_path.name}")
    print(f"📊 Tamanho: {file_path.stat().st_size / 1024:.2f} KB")
    print("-" * 60)

    # Faz a requisição
    try:
        with open(file_path, "rb") as f:
            files = {"dicom_file": (file_path.name, f, "application/dicom")}
            response = requests.post(api_url, files=files, timeout=60)

        # Processa resposta
        if response.status_code == 200:
            data = response.json()

            print("✅ Comparação bem-sucedida!\n")

            # Estatísticas
            stats = data["statistics"]
            print("📊 Estatísticas da Comparação:")
            print("-" * 60)
            print(f"  Diferença Média:  {stats['mean_difference']:.4f} ({stats['mean_difference']*100:.2f}%)")
            print(f"  Diferença Máxima: {stats['max_difference']:.4f} ({stats['max_difference']*100:.2f}%)")
            print(f"  Desvio Padrão:    {stats['std_difference']:.4f}")

            # Análise
            if stats['mean_difference'] > 0.10:
                print("\n⚠️  ALERTA: Diferença > 10% - Métodos muito diferentes!")
            elif stats['mean_difference'] > 0.05:
                print("\n⚠️  ATENÇÃO: Diferença > 5% - Considere usar método oficial")
            else:
                print("\n✅ Diferença aceitável (< 5%)")

            # Top 5 maiores diferenças
            print("\n🔍 Top 5 Maiores Diferenças:")
            print("-" * 60)
            diffs = sorted(
                data["absolute_differences"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            for i, (finding, diff) in enumerate(diffs, 1):
                curr = data["current_method"][finding]
                offi = data["official_method"][finding]
                print(f"{i}. {finding:30} Δ={diff:.4f} ({diff*100:.2f}%)")
                print(f"   Anterior: {curr:.4f} | Oficial: {offi:.4f}")

            # Comparação lado a lado (top 10)
            print("\n📊 Comparação Detalhada (Top 10 probabilidades):")
            print("-" * 60)
            print(f"{'Achado':<30} {'Anterior':>10} {'Oficial':>10} {'Δ':>8}")
            print("-" * 60)

            # Pegar top 10 do método oficial
            top_findings = sorted(
                data["official_method"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            for finding, prob_official in top_findings:
                prob_current = data["current_method"][finding]
                diff = abs(prob_official - prob_current)
                print(f"{finding:<30} {prob_current:>9.1%} {prob_official:>9.1%} {diff:>7.1%}")

            # Decisão
            print("\n" + "=" * 60)
            print("🎯 DECISÃO TÉCNICA:")
            if stats['mean_difference'] > 0.05:
                print("   → Use método oficial (use_official_preprocessing=True)")
                print("   → Diferença justifica mudança de padrão")
            else:
                print("   → Ambos métodos equivalentes")
                print("   → Use método oficial por consistência")

            print("\n💡 Referência: orthanc_analysis.ipynb Seção 2")

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
        print("Uso: python tests/test_compare_preprocessing.py <caminho-para-arquivo.dcm>")
        print("\nExemplo:")
        print("  python tests/test_compare_preprocessing.py ~/Downloads/chest_xray.dcm")
        sys.exit(1)

    test_compare_preprocessing(sys.argv[1])
