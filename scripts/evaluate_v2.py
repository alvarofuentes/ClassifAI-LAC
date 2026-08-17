import pandas as pd
from classifai.indexers.main import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers.huggingface import HuggingFaceVectoriser

def is_orphan(row):
    """
    Heuristic to determine if an example is an orphan word 
    broken off from a larger compound phrase.
    """
    ejemplo = str(row.get('ejemplo', '')).strip()
    frase = str(row.get('frase_original', '')).strip()
    
    words_ejemplo = len(ejemplo.split())
    words_frase = len(frase.split())
    
    # If the extracted example is just 1 word, but the original phrase was long (>3 words)
    # and contained conjunctions, it's highly likely to be a broken orphan.
    conjunctions = [" o ", " y ", " e ", " u "]
    has_conj = any(c in frase.lower() for c in conjunctions)
    
    if words_ejemplo == 1 and words_frase > 2 and has_conj:
        return True
        
    # Also exclude very short meaningless words
    if len(ejemplo) < 3:
        return True
        
    return False

def evaluate_model():
    print("Loading test dataset (CCIF 2018 LLM Extracted)...")
    test_df = pd.read_csv("data/raw/ccif_2018_cl_ejemplos_es.csv", dtype=str)
    
    initial_len = len(test_df)
    
    # Apply orphan filter
    test_df['is_orphan'] = test_df.apply(is_orphan, axis=1)
    orphans = test_df[test_df['is_orphan'] == True]
    test_df = test_df[test_df['is_orphan'] == False]
    
    print(f"Filtered {len(orphans)} orphan/invalid examples. Kept {len(test_df)} out of {initial_len}.")
    
    # Clean COICOP code (remove dots, truncate to 4 digits)
    test_df['id'] = test_df['codigo_ccif'].str.replace('.', '').str[:4]
    
    # We only care about predicting categories that are present in our base catalog.
    # Our base catalog coicop_es.csv covers all COICOP classes (4 digits) 0111 to 12XX
    # So we can keep all of them.
    
    # Initialize VectorStore
    print("Loading VectorStore with expanded index...")
    vectoriser = HuggingFaceVectoriser(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Use the expanded index we created previously (which has the 10 LAC countries, but NOT Chile)
    store = VectorStore(
        file_name="data/raw/coicop_es_expanded.csv",
        data_type="csv",
        vectoriser=vectoriser,
        output_dir="data/coicop_expanded_index",
        overwrite=True # ensure it loads clean or re-reads
    )
    
    queries = test_df['ejemplo'].tolist()
    query_ids = test_df['id'].tolist()
    
    search_input = VectorStoreSearchInput.from_data({
        "id": [str(i) for i in range(len(queries))],
        "query": queries
    })
    
    print("Running classification on all examples (this may take a moment)...")
    results_df = store.search(search_input, n_results=3)
    
    top1_correct = 0
    top2_correct = 0
    top3_correct = 0
    total = len(queries)
    
    grouped = results_df.groupby('query_id')
    failures = []
    
    for i in range(len(queries)):
        q_id = str(i)
        true_label = query_ids[i]
        query_text = queries[i]
        
        if q_id not in grouped.groups:
            failures.append((query_text, true_label, "NO PREDICTION"))
            continue
            
        group = grouped.get_group(q_id).sort_values('rank')
        predicted_labels = group['doc_id'].tolist()
        
        if not predicted_labels:
            failures.append((query_text, true_label, "NONE"))
            continue
            
        # Top 1
        if predicted_labels[0] == true_label:
            top1_correct += 1
            top2_correct += 1
            top3_correct += 1
        else:
            # Top 2
            if len(predicted_labels) > 1 and predicted_labels[1] == true_label:
                top2_correct += 1
                top3_correct += 1
            else:
                # Top 3
                if len(predicted_labels) > 2 and predicted_labels[2] == true_label:
                    top3_correct += 1
                else:
                    failures.append((query_text, true_label, predicted_labels[0]))
                    
    top1_acc = top1_correct / total * 100
    top2_acc = top2_correct / total * 100
    top3_acc = top3_correct / total * 100
    
    print("\n" + "="*50)
    print(" EVALUATION RESULTS (CCIF 2018 LLM Dataset)")
    print("="*50)
    print(f"Total Evaluated : {total}")
    print(f"Top-1 Accuracy  : {top1_acc:.2f}% ({top1_correct}/{total})")
    print(f"Top-2 Accuracy  : {top2_acc:.2f}% ({top2_correct}/{total})")
    print(f"Top-3 Accuracy  : {top3_acc:.2f}% ({top3_correct}/{total})")
    print("="*50)
    
    print("\nSample of Failures (Text | True Label | Predicted Label):")
    for fail in failures[:15]:
        print(f"- {fail[0]} | True: {fail[1]} | Pred: {fail[2]}")

if __name__ == "__main__":
    evaluate_model()
