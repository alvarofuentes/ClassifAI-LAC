import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.getcwd(), "src"))
os.chdir("data")

try:
    from classifai.indexers import VectorStore
    from classifai.vectorisers import HuggingFaceVectoriser

    print("Loading vectoriser...")
    v = HuggingFaceVectoriser("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    print("Loading store...")
    store = VectorStore("raw/tna_es.csv", data_type="csv", vectoriser=v, output_dir="indices/tna_es", overwrite=True)
    print("Success:", store.num_vectors)
except Exception:
    print("Caught an exception! Writing to exception.txt")
    with open("exception.txt", "w") as f:
        traceback.print_exc(file=f)
