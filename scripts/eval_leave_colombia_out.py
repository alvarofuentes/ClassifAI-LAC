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
    print("Loading test dataset (Colombia Test)...")
    test_df = pd.read_csv("data/raw/colombia_test.csv", dtype=str)
    
    # Clean COICOP code (remove dots, truncate to 4 digits)
    test_df['id'] = test_df['id'].str.replace('.', '').str[:4]
    
    # Drop rows without query text or valid ID
    test_df = test_df.dropna(subset=['text', 'id'])
    
    # We only care about predicting categories that are present in our base catalog.
    # Our base catalog coicop_es.csv covers all COICOP classes (4 digits) 0111 to 12XX
    # So we can keep all of them.
    
    # Initialize VectorStore
    print("Loading VectorStore with expanded index...")
    vectoriser = HuggingFaceVectoriser(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Usamos el Índice Maestro SIN Colombia
    store = VectorStore(
        file_name="data/raw/coicop_master_no_col.csv",
        data_type="csv",
        vectoriser=vectoriser,
        output_dir="data/coicop_master_no_col",
        overwrite=True
    )
    
    # Usamos la columna text
    queries = test_df['text'].tolist()
    query_ids = test_df['id'].tolist()
    
    search_input = VectorStoreSearchInput.from_data({
        "id": [str(i) for i in range(len(queries))],
        "query": queries
    })
    
    print("Running classification on all examples (this may take a moment)...")
    results_df = store.search(search_input, n_results=3)
    
    def calculate_metrics(subset_indices, name):
        top1_correct = 0
        top2_correct = 0
        top3_correct = 0
        total = len(subset_indices)
        if total == 0:
            return
            
        grouped = results_df.groupby('query_id')
        failures = []
        
        for i in subset_indices:
            q_id = str(i)
            true_label = str(query_ids[i])
            query_text = queries[i]
            
            if q_id not in grouped.groups:
                failures.append((query_text, true_label, "NO PREDICTION"))
                continue
                
            group = grouped.get_group(q_id).sort_values('rank')
            predicted_labels = [str(x) for x in group['doc_id'].tolist()]
            
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
        print(f" EVALUATION RESULTS: {name}")
        print("="*50)
        print(f"Total Evaluated : {total}")
        print(f"Top-1 Accuracy  : {top1_acc:.2f}% ({top1_correct}/{total})")
        print(f"Top-2 Accuracy  : {top2_acc:.2f}% ({top2_correct}/{total})")
        print(f"Top-3 Accuracy  : {top3_acc:.2f}% ({top3_correct}/{total})")
        print("="*50)
        
        if name == "TOTALES (Todas las divisiones)":
            print("\nSample of Failures (Text | True Label | Predicted Label):")
            for fail in failures[:15]:
                print(f"- {fail[0]} | True: {fail[1]} | Pred: {fail[2]}")
                
        return top1_acc, top2_acc, top3_acc

    # All indices
    all_indices = list(range(len(queries)))
    
    # Calculate for Totals
    calculate_metrics(all_indices, "TOTALES (Todas las divisiones)")
    
    # Loop through all divisions 01 to 12
    for d in range(1, 13):
        div_str = f"{d:02d}"
        div_indices = [i for i, true_label in enumerate(query_ids) if str(true_label).startswith(div_str)]
        calculate_metrics(div_indices, f"División {div_str}")


if __name__ == "__main__":
    evaluate_model()
