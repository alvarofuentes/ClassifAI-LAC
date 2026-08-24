"""Multi-Country Benchmark Evaluation Script for ClassifAI-LAC.

Evaluates COICOP 4-digit classification across Latin American and Caribbean datasets.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.indexers.main import VectorStore

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BENCHMARK_FILE = ROOT_DIR / "data" / "benchmarks" / "lac_multicountry_benchmark.parquet"
FALLBACK_CSV = ROOT_DIR / "data" / "benchmarks" / "lac_multicountry_benchmark.csv"
DEFAULT_OUTPUT_REPORT_PATH = ROOT_DIR / "docs" / "benchmarks" / "reporte_multipais_v2.md"
INDICES_DIR = ROOT_DIR / "data" / "indices"


def load_benchmark(
    benchmark_file: Path | None = None, sample_size: int = 0, countries: list[str] | None = None
) -> pd.DataFrame:
    """Loads benchmark dataset with optional filtering and sampling per country."""
    file_to_load = benchmark_file if benchmark_file and benchmark_file.exists() else DEFAULT_BENCHMARK_FILE
    if file_to_load.exists():
        df = pd.read_parquet(file_to_load)
    elif FALLBACK_CSV.exists():
        df = pd.read_csv(FALLBACK_CSV, dtype=str)
    else:
        raise FileNotFoundError(f"Benchmark file not found at {file_to_load} or {FALLBACK_CSV}")

    # Clean types
    df["target_code_4d"] = df["target_code_4d"].astype(str).str.strip()
    df["target_division_2d"] = df["target_code_4d"].str[:2]
    df["query_text"] = df["query_text"].astype(str).str.strip()

    if countries and countries != ["all"]:
        df = df[df["sheet_name"].isin(countries)]

    if sample_size > 0:
        print(f"Sampling up to {sample_size} examples per country dataset...")
        sampled_groups = [
            group.sample(min(len(group), sample_size), random_state=42)
            for _, group in df.groupby("sheet_name")
        ]
        df = pd.concat(sampled_groups, ignore_index=True)

    print(f"Loaded benchmark with {len(df)} records across {df['sheet_name'].nunique()} sheets.")
    return df


def translate_brazil_pt_to_es(df_brazil: pd.DataFrame) -> pd.DataFrame:
    """Translates Brazil query texts from Portuguese to Spanish using deep-translator."""
    try:
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source="pt", target="es")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize deep-translator: {e}. Skipping translation.")
        return df_brazil

    print(f"Translating {len(df_brazil)} Brazilian Portuguese queries to Spanish...")
    unique_texts = [str(t).strip() for t in df_brazil["query_text"].unique() if str(t).strip()]
    cache = {}

    batch_size = 30
    for i in range(0, len(unique_texts), batch_size):
        chunk = unique_texts[i : i + batch_size]
        try:
            translated_chunk = translator.translate_batch(chunk)
            for orig, trans in zip(chunk, translated_chunk, strict=False):
                cache[orig] = trans
        except Exception:
            for item in chunk:
                try:
                    cache[item] = translator.translate(item)
                except Exception:
                    cache[item] = item
        print(f"  Translated {min(i + batch_size, len(unique_texts))}/{len(unique_texts)} terms...", flush=True)
        time.sleep(0.1)

    df_trans = df_brazil.copy()
    df_trans["query_text"] = df_trans["query_text"].map(cache).fillna(df_trans["query_text"])
    df_trans["sheet_name"] = "bra17_es"
    df_trans["country"] = "Brasil (Traducido ES)"
    return df_trans


def evaluate_store(store: VectorStore, benchmark_df: pd.DataFrame, top_k: int = 5) -> tuple[dict, pd.DataFrame]:
    """Runs batch vector search and calculates accuracy & F1 metrics."""
    queries = benchmark_df["query_text"].tolist()
    targets_4d = benchmark_df["target_code_4d"].tolist()
    targets_2d = benchmark_df["target_division_2d"].tolist()
    sheet_names = benchmark_df["sheet_name"].tolist()

    search_input = VectorStoreSearchInput.from_data({
        "id": [str(i) for i in range(len(queries))],
        "query": queries,
    })

    t0 = time.time()
    results_df = store.search(search_input, n_results=top_k)
    elapsed = time.time() - t0
    latency_ms = (elapsed / max(len(queries), 1)) * 1000

    grouped = results_df.groupby("query_id")
    rows_eval = []

    for i in range(len(queries)):
        q_id = str(i)
        true_4d = str(targets_4d[i]).strip().zfill(4)
        true_2d = str(targets_2d[i]).strip().zfill(2)
        sheet = sheet_names[i]
        q_text = queries[i]

        if q_id not in grouped.groups:
            top_preds = []
        else:
            group = grouped.get_group(q_id).sort_values("rank")
            top_preds = [str(doc_id).strip().zfill(4) for doc_id in group["doc_id"].tolist()]

        pred_1 = top_preds[0] if len(top_preds) > 0 else ""
        pred_top3 = top_preds[:3]
        pred_top5 = top_preds[:5]

        top1_match = bool(pred_1 == true_4d)
        top3_match = bool(true_4d in pred_top3)
        top5_match = bool(true_4d in pred_top5)
        div2_match = bool(pred_1[:2] == true_2d) if pred_1 else False

        rows_eval.append({
            "sheet_name": sheet,
            "query_text": q_text,
            "true_code_4d": true_4d,
            "pred_code_4d": pred_1,
            "top_predictions": top_preds,
            "top1_match": top1_match,
            "top3_match": top3_match,
            "top5_match": top5_match,
            "div2_match": div2_match,
        })

    eval_df = pd.DataFrame(rows_eval)

    # Calculate metrics by sheet
    sheet_summaries = []
    for sheet, s_df in eval_df.groupby("sheet_name"):
        n = len(s_df)
        t1 = s_df["top1_match"].mean() * 100
        t3 = s_df["top3_match"].mean() * 100
        t5 = s_df["top5_match"].mean() * 100
        d2 = s_df["div2_match"].mean() * 100

        # F1 Scores
        y_true = s_df["true_code_4d"]
        y_pred = s_df["pred_code_4d"]
        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) * 100
        weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0) * 100

        sheet_summaries.append({
            "Dataset": sheet,
            "N": n,
            "Top-1 Acc (%)": round(t1, 2),
            "Top-3 Hit (%)": round(t3, 2),
            "Top-5 Hit (%)": round(t5, 2),
            "División 2D (%)": round(d2, 2),
            "Macro F1 (%)": round(macro_f1, 2),
            "Weighted F1 (%)": round(weighted_f1, 2),
        })

    overall_t1 = eval_df["top1_match"].mean() * 100
    overall_t3 = eval_df["top3_match"].mean() * 100
    overall_t5 = eval_df["top5_match"].mean() * 100
    overall_d2 = eval_df["div2_match"].mean() * 100
    overall_macro_f1 = f1_score(eval_df["true_code_4d"], eval_df["pred_code_4d"], average="macro", zero_division=0) * 100
    overall_weighted_f1 = (
        f1_score(eval_df["true_code_4d"], eval_df["pred_code_4d"], average="weighted", zero_division=0) * 100
    )

    metrics = {
        "total_queries": len(queries),
        "latency_ms_per_query": round(latency_ms, 2),
        "overall_top1": round(overall_t1, 2),
        "overall_top3": round(overall_t3, 2),
        "overall_top5": round(overall_t5, 2),
        "overall_div2": round(overall_d2, 2),
        "overall_macro_f1": round(overall_macro_f1, 2),
        "overall_weighted_f1": round(overall_weighted_f1, 2),
        "sheet_summaries": pd.DataFrame(sheet_summaries),
    }

    return metrics, eval_df


def generate_markdown_report(results: dict[str, dict], output_file: Path, benchmark_name: str = "Benchmark"):
    """Generates a comprehensive Markdown report summarizing multi-country results."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# 📊 Reporte de Benchmark Multipaís LAC - Clasificación COICOP 2018 (4 Dígitos) — {benchmark_name}",
        "",
        f"**Fecha de ejecución:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 1. Resumen Global Comparativo de Modelos",
        "",
        "| Modelo / Estrategia | Total Items | Top-1 Acc (4D) | Top-3 Hit (4D) | Top-5 Hit (4D) | División 2D Acc | Macro F1 | Latencia (ms/q) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for model_name, res in results.items():
        lines.append(
            f"| **{model_name}** | {res['total_queries']} | **{res['overall_top1']}%** | {res['overall_top3']}% | {res['overall_top5']}% | {res['overall_div2']}% | {res['overall_macro_f1']}% | {res['latency_ms_per_query']} ms |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Desglose Detallado por País y Dataset",
        "",
    ])

    for model_name, res in results.items():
        lines.extend([
            f"### 📍 Resultados para: `{model_name}`",
            "",
            res["sheet_summaries"].to_markdown(index=False),
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 3. Conclusiones Metodológicas y Siguientes Pasos",
        "",
        "- **Rendimiento Multipaís:** Evaluación del balance entre países tras estratificación anti-sobreajuste.",
        "- **Impacto de Fine-Tuning v2:** Comparativa directa frente a v1 y Baseline.",
        "",
    ])

    report_content = "\n".join(lines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n📑 Markdown report generated at: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Multi-country COICOP benchmark evaluator")
    parser.add_argument(
        "--benchmark-path",
        type=str,
        default=str(DEFAULT_BENCHMARK_FILE),
        help="Path to the benchmark parquet or csv file",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=str(DEFAULT_OUTPUT_REPORT_PATH),
        help="Output markdown report file path",
    )
    parser.add_argument("--sample-size", type=int, default=0, help="Number of samples per country (0 for all)")
    parser.add_argument("--countries", type=str, default="all", help="Comma-separated country sheets or 'all'")
    parser.add_argument("--test-brazil-translation", action="store_true", help="Compare Brazil PT vs translated ES")
    parser.add_argument("--top-k", type=int, default=5, help="Number of nearest neighbors to retrieve")
    parser.add_argument("--include-reranker", action="store_true", default=False, help="Include Cross-Encoder ReRanker")
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark_path)
    output_report_path = Path(args.output_report)

    country_list = [c.strip() for c in args.countries.split(",")] if args.countries != "all" else ["all"]
    benchmark_df = load_benchmark(benchmark_file=benchmark_path, sample_size=args.sample_size, countries=country_list)

    if args.test_brazil_translation and "bra17" in benchmark_df["sheet_name"].values:
        df_brazil = benchmark_df[benchmark_df["sheet_name"] == "bra17"]
        df_brazil_es = translate_brazil_pt_to_es(df_brazil)
        benchmark_df = pd.concat([benchmark_df, df_brazil_es], ignore_index=True)

    from classifai.rerankers.cross_encoder import HuggingFaceCrossEncoder
    from classifai.vectorisers.huggingface import HuggingFaceVectoriser

    # Check available indices
    indices_to_evaluate = {}

    # 1. Fine-Tuned v2
    ft2_index_dir = INDICES_DIR / "coicop_master_finetuned_v2"
    ft2_model_path = ROOT_DIR / "models" / "coicop-finetuned-v2"
    if ft2_index_dir.exists() and ft2_model_path.exists():
        print(f"Loading Fine-Tuned v2 VectorStore from {ft2_index_dir}...")
        ft2_vectoriser = HuggingFaceVectoriser(model_name=str(ft2_model_path))
        indices_to_evaluate["Fine-Tuned v2 (Balanced LAC Embeddings)"] = VectorStore.from_filespace(
            str(ft2_index_dir), vectoriser=ft2_vectoriser
        )

    # 2. Fine-Tuned v1
    ft1_index_dir = INDICES_DIR / "coicop_master_finetuned_v1"
    ft1_model_path = ROOT_DIR / "models" / "coicop-finetuned-v1"
    if ft1_index_dir.exists() and ft1_model_path.exists():
        print(f"Loading Fine-Tuned v1 VectorStore from {ft1_index_dir}...")
        ft1_vectoriser = HuggingFaceVectoriser(model_name=str(ft1_model_path))
        indices_to_evaluate["Fine-Tuned v1 (SetFit Embeddings)"] = VectorStore.from_filespace(
            str(ft1_index_dir), vectoriser=ft1_vectoriser
        )

        if args.include_reranker:
            print("Loading Multilingual Cross-Encoder ReRanker...")
            reranker = HuggingFaceCrossEncoder(model_name="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
            indices_to_evaluate["Fine-Tuned v1 + Cross-Encoder ReRanker"] = VectorStore.from_filespace(
                str(ft1_index_dir), vectoriser=ft1_vectoriser, reranker=reranker
            )

    # 3. Baseline
    baseline_index_dir = INDICES_DIR / "coicop_master_baseline_mpnet"
    baseline_model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    if baseline_index_dir.exists():
        print(f"Loading Baseline VectorStore from {baseline_index_dir}...")
        baseline_vectoriser = HuggingFaceVectoriser(model_name=baseline_model_name)
        indices_to_evaluate["Baseline (mpnet-base-v2)"] = VectorStore.from_filespace(
            str(baseline_index_dir), vectoriser=baseline_vectoriser
        )

    if not indices_to_evaluate:
        print("❌ Error: No vector store indices available to evaluate.")
        return

    results = {}
    for model_name, store in indices_to_evaluate.items():
        print(f"\n=======================================================")
        print(f"Evaluating {model_name} on {len(benchmark_df)} samples...")
        print(f"=======================================================")
        metrics, _ = evaluate_store(store, benchmark_df, top_k=args.top_k)
        results[model_name] = metrics

        print(
            f"Top-1 Accuracy: {metrics['overall_top1']}% | Top-3 Hit: {metrics['overall_top3']}% | "
            f"Top-5 Hit: {metrics['overall_top5']}%"
        )
        print(
            f"Division 2D Acc: {metrics['overall_div2']}% | Macro F1: {metrics['overall_macro_f1']}% | "
            f"Latency: {metrics['latency_ms_per_query']} ms/query"
        )
        print("\nPer-Sheet Breakdown:")
        print(metrics["sheet_summaries"].to_string(index=False))

    generate_markdown_report(results, output_report_path, benchmark_name=benchmark_path.stem)


if __name__ == "__main__":
    main()

