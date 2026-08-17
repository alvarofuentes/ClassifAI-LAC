import pandas as pd
from classifai.indexers.main import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers.huggingface import HuggingFaceVectoriser

def evaluate_model():
    print("Loading test dataset (INE Chile)...")
    test_df = pd.read_csv("data/raw/ine_chile_examples.csv", dtype=str)
    
    # We only care about predicting the first 2 digits (Division) or the first 4 digits (Class).
    # Since our expanded index was built at the 4-digit level, we will evaluate at 4 digits.
    # However, some codes in the PDF might be from non-food categories if the PDF contains the full catalog.
    # Let's filter our test dataset to only include food items (01XX) or evaluate on everything if our index covers everything.
    # coicop_es.csv covers all COICOP (up to 12 divisions).
    
    print(f"Total test examples: {len(test_df)}")
    
    # Clean up test dataset
    test_df = test_df.dropna(subset=['id', 'text'])
    
    # Initialize VectorStore
    print("Loading VectorStore with expanded index...")
    vectoriser = HuggingFaceVectoriser(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Use the expanded index we created previously
    store = VectorStore(
        file_name="data/raw/coicop_es_expanded.csv",
        data_type="csv",
        vectoriser=vectoriser,
        output_dir="data/coicop_expanded_index",
        overwrite=True
    )
    
    # Prepare queries
    queries = test_df['text'].tolist()
    query_ids = test_df['id'].tolist()
    
    search_input = VectorStoreSearchInput.from_data({
        "id": [str(i) for i in range(len(queries))],
        "query": queries
    })
    
    print("Running classification on all examples (this may take a moment)...")
    # Using n_results=3 to calculate Top-1 and Top-3 Accuracy
    results_df = store.search(search_input, n_results=3)
    
    # Evaluate
    top1_correct = 0
    top3_correct = 0
    total = len(queries)
    
    # We need to map the predicted doc_id to the true query_id
    # results_df contains: query_id, rank, doc_id, doc_text, score
    
    # Group results by query_id
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
        
        # Check Top-1
        if predicted_labels and predicted_labels[0] == true_label:
            top1_correct += 1
            top3_correct += 1
        else:
            # Check Top-3
            if true_label in predicted_labels:
                top3_correct += 1
            else:
                failures.append((query_text, true_label, predicted_labels[0] if predicted_labels else "NONE"))
                
    top1_acc = top1_correct / total * 100
    top3_acc = top3_correct / total * 100
    
    print("\n" + "="*50)
    print(" EVALUATION RESULTS (INE Chile Dataset)")
    print("="*50)
    print(f"Total Evaluated : {total}")
    print(f"Top-1 Accuracy  : {top1_acc:.2f}% ({top1_correct}/{total})")
    print(f"Top-3 Accuracy  : {top3_acc:.2f}% ({top3_correct}/{total})")
    print("="*50)
    
    # Print some failures
    print("\nSample of Failures (Text | True Label | Predicted Label):")
    for fail in failures[:15]:
        print(f"- {fail[0]} | True: {fail[1]} | Pred: {fail[2]}")

if __name__ == "__main__":
    evaluate_model()
