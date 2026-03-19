import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers import HuggingFaceVectoriser

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DATA_DIR = ROOT / "data" / "indices" / "tna_es"


def main():
    v = HuggingFaceVectoriser(MODEL)
    store = VectorStore.from_filespace(str(DATA_DIR), v)

    # Test 1: EXACT match from the start of the file
    query_text = "Avena, cruda"
    print(f"\nSearching for exact string: '{query_text}'")
    si = VectorStoreSearchInput({"id": ["1"], "query": [query_text]})
    res = store.search(si, n_results=3)
    print("Results (Top 3):")
    for i, row in res.iterrows():
        print(f"Rank {row['rank']}: {row['doc_id']} - {row['doc_text']} (Score: {row['score']:.4f})")

    # Test 2: Semantic match
    query_text = "leche con poca grasa"
    print(f"\nSearching for semantic string: '{query_text}'")
    si = VectorStoreSearchInput({"id": ["2"], "query": [query_text]})
    res = store.search(si, n_results=3)
    print("Results (Top 3):")
    for i, row in res.iterrows():
        print(f"Rank {row['rank']}: {row['doc_id']} - {row['doc_text']} (Score: {row['score']:.4f})")


if __name__ == "__main__":
    main()
