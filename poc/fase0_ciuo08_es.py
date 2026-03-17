"""Script de prueba de concepto — Fase 0 ClassifAI-LAC.

Valida el pipeline completo de ClassifAI con un modelo multilingüe
usando el catálogo CIUO-08 en español como base de conocimiento.
"""

import sys
from pathlib import Path

# Asegurar que el paquete se encuentra en el path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers import HuggingFaceVectoriser

# ─── Configuración ────────────────────────────────────────────────────────────
# Modelo multilingüe liviano (~118 MB, 50+ idiomas, incluye ES y PT)
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DATA_FILE = str(ROOT / "data" / "ciuo08_es.csv")
VECTORSTORE_PATH = str(ROOT / "data" / "vectorstore_ciuo08_es")

# ─── Consultas de prueba ──────────────────────────────────────────────────────
TEST_QUERIES = [
    "conductor de camión de carga pesada",
    "enfermera que trabaja en urgencias del hospital",
    "maestro que enseña matemáticas en colegio",
    "programador que hace apps para el celular",
    "vendedor que vende frutas en la calle",
    "cocinero en restaurante de comida rápida",
    "abogada que defiende casos en tribunales",
    "agricultor que siembra maíz y papa",
    "albañil que construye casas",
    "médico que atiende consultas generales",
]


def main():
    print("=" * 60)
    print("ClassifAI-LAC — Fase 0: Prueba de Concepto")
    print(f"Modelo: {MODEL}")
    print("=" * 60)

    # 1. Inicializar vectorizador multilingüe
    print("\n[1/3] Cargando modelo de embeddings multilingüe...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    print("      ✓ Modelo cargado")

    # 2. Construir VectorStore desde el catálogo CIUO-08
    print(f"\n[2/3] Construyendo VectorStore desde {DATA_FILE}...")
    store = VectorStore(
        file_name=DATA_FILE,
        data_type="csv",
        vectoriser=vectoriser,
        overwrite=True,
    )
    print("      ✓ VectorStore creado")

    # 3. Evaluar consultas en español
    print("\n[3/3] Evaluando consultas en español...\n")
    print(f"{'Consulta':<45} {'Top-1 código':<10} {'Descripción CIUO-08':<40} {'Score'}")
    print("-" * 120)

    search_input = VectorStoreSearchInput(
        {"id": list(range(len(TEST_QUERIES))), "query": TEST_QUERIES}
    )
    results = store.search(search_input, n_results=3)

    # La API retorna un pandas DataFrame con columnas: query_id, query_text, doc_id, doc_text, rank, score
    results_df = results.to_pandas() if hasattr(results, 'to_pandas') else results

    for i, query in enumerate(TEST_QUERIES):
        row = results_df[(results_df["query_id"] == str(i)) & (results_df["rank"] == 1)]
        if not row.empty:
            code = row["doc_id"].values[0]
            label = row["doc_text"].values[0]
            score = row["score"].values[0]
            print(f"{query:<45} {str(code):<10} {label:<40} {score:.4f}")

    print("\n✓ Pipeline completo ejecutado correctamente.")
    print("  → Para ver el benchmark de accuracy con muestra sintética, ejecute:")
    print("    python poc/benchmark_ciuo08.py")


if __name__ == "__main__":
    main()
