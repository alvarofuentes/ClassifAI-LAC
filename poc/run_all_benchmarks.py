"""Script unificado de Benchmarks — ClassifAI-LAC (Fase 1.5).

Este script lee todos los CSVs en data/benchmarks/ y evalúa su accuracy
(Top-1 y Top-3) golpeando directamente la API local de ClassifAI-LAC.
Genera un reporte consolidado en Markdown.

Requisito: La API debe estar corriendo (`python src/serve_api.py`)
"""

import csv
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
BENCHMARKS_DIR = ROOT / "data" / "benchmarks"
REPORT_PATH = ROOT / "data" / "benchmarks" / "reporte_benchmarks.md"
API_URL = "http://localhost:8000/{classifier}/search"


def run_benchmark_for_classifier(classifier: str, filepath: Path) -> dict:
    """Lee el CSV de benchmark y evalúa contra la API."""
    cases = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(row)

    if not cases:
        return None

    # Preparar payload para la API
    entries = [{"id": row["id_registro"], "description": row["literal"]} for row in cases]
    payload = json.dumps({"entries": entries}).encode("utf-8")

    url = API_URL.format(classifier=classifier)
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  ❌ Error consultando la API para {classifier}: {e}")
        return None

    # Procesar resultados
    # La API retorna: {"data": [{"input_id": "...", "response": [{"label": "...", "score": ...}, ...]}]}
    hits_top1 = 0
    hits_top3 = 0
    total = len(cases)

    # Crear diccionario de respuestas por ID
    api_responses = {item["input_id"]: item["response"] for item in result.get("data", [])}

    for case in cases:
        case_id = case["id_registro"]
        ground_truth = str(case["ground_truth"])

        preds = api_responses.get(case_id, [])
        top_codes = [str(p["label"]) for p in preds]

        if top_codes and top_codes[0] == ground_truth:
            hits_top1 += 1
        if ground_truth in top_codes[:3]:
            hits_top3 += 1

    return {
        "classifier": classifier,
        "total_cases": total,
        "top1_acc": hits_top1 / total if total > 0 else 0,
        "top3_acc": hits_top3 / total if total > 0 else 0,
    }


def main():
    print("=" * 65)
    print("ClassifAI-LAC — Ejecución Unificada de Benchmarks (Fase 1.5)")
    print("=" * 65)

    if not BENCHMARKS_DIR.exists():
        print(f"❌ No se encontró la carpeta {BENCHMARKS_DIR}")
        return

    csvs = list(BENCHMARKS_DIR.glob("benchmark_*.csv"))
    if not csvs:
        print("❌ No hay archivos benchmark_*.csv para evaluar.")
        return

    print(f"Encontrados {len(csvs)} archivos de prueba.\n")
    results = []

    for path in sorted(csvs):
        # Extraer nombre del clasificador (ej. benchmark_ciiu4.csv -> ciiu4_es)
        # Nota: asume que el índice en la API tiene sufijo _es
        classifier_base = path.stem.replace("benchmark_", "")
        classifier_api = f"{classifier_base}_es"

        print(f"▶ Evaluando: {classifier_api} ({path.name})...", end="", flush=True)
        res = run_benchmark_for_classifier(classifier_api, path)
        if res:
            results.append(res)
            print(f" ✅ [Top-1: {res['top1_acc']:.1%} | Top-3: {res['top3_acc']:.1%}]")

    if not results:
        print("\n❌ No se pudieron evaluar resultados. ¿Está corriendo la API?")
        return

    # Generar reporte en Markdown
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Reporte de Benchmarks Sintéticos — ClassifAI-LAC (Fase 1.5)\n\n")
        f.write("Evaluación de la precisión de los modelos estadísticos con data sintética.\n\n")
        f.write("| Clasificador | Casos | Top-1 Accuracy | Top-3 Accuracy |\n")
        f.write("|---|---|---|---|\n")
        for r in results:
            f.write(
                f"| `{r['classifier']}` | {r['total_cases']} | **{r['top1_acc']:.1%}** | **{r['top3_acc']:.1%}** |\n"
            )

        avg_t1 = sum(r["top1_acc"] for r in results) / len(results)
        avg_t3 = sum(r["top3_acc"] for r in results) / len(results)
        f.write(
            f"| **Promedio Global** | **{sum(r['total_cases'] for r in results)}** | **{avg_t1:.1%}** | **{avg_t3:.1%}** |\n"
        )

    print("\n" + "=" * 65)
    print(f"📊 Reporte generado en: {REPORT_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
