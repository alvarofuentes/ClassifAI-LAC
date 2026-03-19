import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers import HuggingFaceVectoriser

# --- Configuración ---
MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DATA_FILE = str(ROOT / "data" / "indices" / "tna_es")

# --- Muestra Sintética (TNA) ---
# [F] Fácil, [A] Coloquial/Jerga, [B] Técnico/Científico, [C] Complejo
SAMPLE = [
    # Frijol negro (01260101, 01260104)
    ("Frijol negro, crudo", ["01260101", "01260104"], "F: control fácil"),
    ("Frijolitos negros para sopa", ["01260101", "01260104"], "A: jerga/coloquial"),
    ("Phaseolus vulgaris, crudo", ["01260101", "01260104"], "B: nombre técnico"),
    
    # Leche descremada (22219101)
    ("Leche descremada con vitamina A", ["22219101"], "F: control fácil"),
    ("Leche light", ["22219101"], "A: jerga/coloquial"),
    ("Lactosuero desnatado fortificado con retinol", ["22219101"], "B: nombre técnico"),
    
    # Aceite de girasol (21549104)
    ("Aceite de girasol", ["21549104", "21549103"], "F: control fácil"),
    ("Aceitito de maravilla", ["21549104", "21549103"], "A: regionalismo (Chile)"),
    ("Lípidos de Helianthus annuus", ["21549104", "21549103"], "B: nombre técnico"),
    
    # Pechuga de pollo (21176108)
    ("Pechuga de pollo cocida sin piel", ["21176108"], "F: control fácil"),
    ("Pechuguita de ave hervida", ["21176108"], "A: jerga/coloquial"),
    ("Proteína de Gallus gallus domesticus procesada", ["21176108"], "B: nombre técnico"),
    
    # Manzana (01310003 - Nicaragua manzana...) -> wait let me check the ID again
    # Correction: I saw 01313101 for platanos.
    ("Manzana fresca", ["01310003"], "F: control fácil"),
    
    # Pie de limón (23439106)
    ("Pie de limon con merengue", ["23439106"], "F: control fácil"),
    ("Pay de limón casero", ["23439106"], "A: regionalismo"),
    
    # Plátano (01313101)
    ("platanos, crudos", ["01313101"], "F: control fácil"),
    ("Bananas maduras", ["01313101"], "A: regionalismo"),
    
    # Sopa minestrone (23992105)
    ("Sopa minestrone, enlatada", ["23992105"], "F: control fácil"),
    ("Sopita de verduras en conserva", ["23992105"], "A: jerga/coloquial"),
    
    # Almendra (21495106)
    ("Almendra seca", ["21495106"], "F: control fácil"),
]

def run_benchmark(store: VectorStore, sample: list, n_results: int = 3) -> pd.DataFrame:
    ids = [str(i) for i in range(len(sample))]
    queries = [row[0] for row in sample]
    
    search_input = VectorStoreSearchInput({"id": ids, "query": queries})
    results = store.search(search_input, n_results=n_results)
    results_df = results  # It already inherits from pd.DataFrame
    
    rows = []
    for i, (query, correct_codes, note) in enumerate(sample):
        # Filter results for this query
        res_i = results_df[results_df["query_id"] == str(i)].sort_values("rank")
        
        # Ensure we have strings for comparison
        top_codes = [str(c) for c in res_i["doc_id"].tolist()]
        top_scores = res_i["score"].tolist()
        top_labels = res_i["doc_text"].tolist()
        
        t1_code = top_codes[0] if top_codes else ""
        t1_score = top_scores[0] if top_scores else 0.0
        t1_label = top_labels[0] if top_labels else ""
        
        # Normalicemos los códigos para comparación (quitar ceros a la izquierda si es necesario)
        # En TNA los códigos son strings de longitud fija o números. 
        # Pero los IDs en el CSV original eran i64.
        # Comparación estricta de strings por ahora.
        hit_top1 = t1_code in correct_codes
        hit_top3 = any(c in correct_codes for c in top_codes[:3])
        
        rows.append({
            "query": query,
            "correct_code": "|".join(correct_codes),
            "top1_code": t1_code,
            "top1_label": t1_label,
            "top1_score": round(t1_score, 4),
            "hit_top1": hit_top1,
            "hit_top3": hit_top3,
            "difficulty": note[:1],
            "note": note
        })
    return pd.DataFrame(rows)

def main():
    print("="*60)
    print("ClassifAI-LAC — Benchmark de Accuracy TNA")
    print("="*60)
    
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    store = VectorStore.from_filespace(DATA_FILE, vectoriser=vectoriser)
    print(f"Cargado VectorStore TNA con {store.num_vectors} entradas.")
    
    df = run_benchmark(store, SAMPLE)
    
    # Métricas Globales
    t1_acc = df["hit_top1"].mean()
    t3_acc = df["hit_top3"].mean()
    
    print("\n📊 RESULTADOS:")
    print(f"   Top-1 Accuracy: {t1_acc:.1%}")
    print(f"   Top-3 Accuracy: {t3_acc:.1%}")
    
    print("\n📊 DETALLE POR DIFICULTAD:")
    diff_map = {"F": "Fácil", "A": "Coloquial", "B": "Técnico", "C": "Complejo"}
    for d, label in diff_map.items():
        sub = df[df["difficulty"] == d]
        if not sub.empty:
            acc = sub["hit_top1"].mean()
            print(f"   {label:<12}: {acc:.1%} (n={len(sub)})")

    # Guardar resultados
    out = ROOT / "poc" / "benchmark_tna_results.csv"
    df.to_csv(out, index=False)
    print(f"\n✅ Resultados guardados en: {out}")

if __name__ == "__main__":
    main()
