import os
import shutil
from classifai.indexers.main import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers.huggingface import HuggingFaceVectoriser

def test_expanded_index():
    print("Testing Expanded COICOP Index...")
    
    # 1. Initialize Vectoriser (using BM25 internally via VectorStore)
    vectoriser = HuggingFaceVectoriser(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # 2. Build Index with the expanded catalog
    index_path = "data/coicop_expanded_index"
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
        
    print("\nBuilding VectorStore...")
    store = VectorStore(
        file_name="data/raw/coicop_es_expanded.csv",
        data_type="csv",
        vectoriser=vectoriser,
        output_dir=index_path,
        overwrite=True
    )
    
    # 3. Test Regional Terms
    print("\nExecuting search for regional terms...")
    query = VectorStoreSearchInput.from_data({
        "id": ["q1", "q2"],
        "query": ["Tortilla de maíz", "Pan sobado"]
    })
    
    results = store.search(query, n_results=3)
    
    print("\nResults:")
    for _, row in results.iterrows():
        print(f"Query ID: {row['query_id']}")
        print(f"Rank {row['rank']} (Score: {row['score']:.4f}) -> COICOP: {row['doc_id']}")
        print(f"Matched Text: {row['doc_text']}")
        print("-" * 50)

if __name__ == "__main__":
    test_expanded_index()
