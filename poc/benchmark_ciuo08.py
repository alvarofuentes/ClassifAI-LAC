"""Benchmark de accuracy — Fase 0 ClassifAI-LAC.

Evalúa el rendimiento del pipeline ClassifAI+CIUO-08 en español usando
una muestra sintética con dificultades reales de clasificación:

Tipos de dificultad incluidos:
  [A] Informalidad / jerga regional
  [B] Títulos ambiguos que pueden corresponder a varios códigos
  [C] Descripciones de trabajo mixto (dos ocupaciones)
  [D] Variación regional del español (mismo cargo, distinto nombre)
  [E] Formalidad excesiva o tecnicismo inusual
  [F] Casos "fáciles" (baseline de control)
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.vectorisers import HuggingFaceVectoriser

# ─── Modelo ───────────────────────────────────────────────────────────────────
MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DATA_FILE = str(ROOT / "data" / "raw" / "ciuo08_es.csv")

# ─── Muestra sintética ────────────────────────────────────────────────────────
# Formato: (texto_libre, codigo_correcto, nota_de_dificultad)
# El código correcto es el CIUO-08 a 4 dígitos
SAMPLE = [
    # [F] Casos control — descripción canónica, deberían clasificar bien
    ("Médico generalista en atención primaria", "2212", "F: control fácil"),
    ("Conductor de camión de carga pesada", "8332", "F: control fácil"),
    ("Maestro de escuela primaria", "2341", "F: control fácil"),
    ("Desarrollador de software y aplicaciones", "2514", "F: control fácil"),
    ("Abogado defensor penal", "2611", "F: control fácil"),
    # [A] Informalidad / jerga regional
    ("Chófer de un camión", "8332", "A: 'chófer' en lugar de 'conductor'"),
    ("Profe de primaria", "2341", "A: apócope coloquial 'profe'"),
    ("Maquinista que maneja el tren de pasajeros", "8311", "A: jerga 'maquinista'"),
    ("Gásfiter que arregla cañerías en condominios", "7126", "A: 'gásfiter' (Chile)"),
    ("Barista y mozo en café céntrico", "5132", "A: 'barista+mozo'=camarero de barra"),
    ("Chapista que endereza carrocerías de autos", "7213", "A: oficio específico"),
    ("Cobrador de micro en ruta urbana", "5112", "A: 'cobrador de micro'"),
    # [B] Ambigüedad entre dos o más códigos plausibles
    ("Supervisor de planta industrial", "3122", "B: ambiguo supervisor/gerente mfg"),
    ("Técnico en sistemas informáticos", "3114", "B: puede ser 3114 o 2522"),
    ("Asesor de ventas en empresa de seguros", "3321", "B: agente seguros vs ventas"),
    ("Coordinador de recursos humanos", "2423", "B: especialista o gerente RRHH"),
    ("Inspector de calidad en fábrica", "3172", "B: técnico calidad vs inspector"),
    ("Encargado de bodega y distribución", "4321", "B: empleado control suministros"),
    ("Operario de planta de producción", "8189", "B: código residual maquinaria"),
    ("Auxiliar administrativo en hospital", "4110", "B: admin. vs aux. salud"),
    # [C] Trabajo mixto — el encuestado describe dos actividades a la vez
    ("Cría cerdos y también siembra maíz en el campo", "6130", "C: agropecuario mixto"),
    ("Vende ropa en feria y también cose en casa", "5211", "C: vendedor + costurero"),
    ("Da clases de inglés y traduce documentos", "2643", "C: traductor + docente"),
    ("Cuida a sus hijos y además atiende una pequeña tienda", "5222", "C: trabajo doméstico vs comercio"),
    ("Pinta casas y hace trabajos de plomería cuando hay trabajo", "7131", "C: pintor + plomero"),
    # [D] Variación regional — mismo cargo, nombre diferente
    ("Plomero que instala tuberías de agua", "7126", "D: 'plomero' (MX/AR) = fontanero"),
    ("Contador público certificado", "2411", "D: 'contador público' = contable"),
    ("Mecánico de autos en taller", "7231", "D: 'mecánico de autos'"),
    ("Recolector de basura municipal", "9611", "D: 'recolector de basura'"),
    ("Guardián nocturno de edificio", "5414", "D: 'guardián' = guarda de seguridad"),
    ("Taxista independiente con auto propio", "8322", "D: conductor de automóviles"),
    ("Empleada doméstica que vive en la casa", "9111", "D: 'empleada doméstica'"),
    # [E] Tecnicismo o formalidad inusual
    ("Profesional de la salud en cuidados paliativos", "2221", "E: especialista enfermería"),
    ("Técnico en metrología y calibración industrial", "3172", "E: puede ser 3119 o 3172"),
    ("Operador de sistemas SCADA en planta eléctrica", "3131", "E: control de procesos"),
    ("Promotor sociocultural en comunidades rurales", "2635", "E: trabajador social"),
    ("Analista de datos geoespaciales", "2120", "E: estadístico/matemático"),
    ("Agente de desarrollo económico local", "2422", "E: especialista políticas admin"),
]


def run_benchmark(store: VectorStore, sample: list, n_results: int = 3) -> pd.DataFrame:
    """Ejecuta el benchmark y retorna un DataFrame con los resultados."""
    ids = list(range(len(sample)))
    queries = [row[0] for row in sample]
    [str(row[1]) for row in sample]
    [row[2] for row in sample]

    search_input = VectorStoreSearchInput({"id": ids, "query": queries})
    results = store.search(search_input, n_results=n_results)

    # La API retorna un VectorStoreSearchOutput (pandera DataFrame)
    # con columnas: query_id, query_text, doc_id, doc_text, rank, score
    results_df = results.to_pandas() if hasattr(results, "to_pandas") else results

    rows = []
    for i, (query, correct_code, note) in enumerate(sample):
        # Filtrar resultados de esta consulta, ordenados por rank
        res_i = results_df[results_df["query_id"] == str(i)].sort_values("rank")
        top_codes = res_i["doc_id"].astype(str).tolist()
        top_scores = res_i["score"].tolist()
        top_labels = res_i["doc_text"].tolist()

        top1_code = top_codes[0] if top_codes else ""
        top1_score = top_scores[0] if top_scores else 0.0
        top1_label = top_labels[0] if top_labels else ""

        hit_top1 = top1_code == correct_code
        hit_top3 = correct_code in top_codes[:3]

        rows.append(
            {
                "query": query,
                "correct_code": correct_code,
                "top1_code": top1_code,
                "top1_label": top1_label,
                "top1_score": round(top1_score, 4),
                "hit_top1": hit_top1,
                "hit_top3": hit_top3,
                "difficulty": note[:1],  # Tipo de dificultad (letra)
                "note": note,
            }
        )

    return pd.DataFrame(rows)


def print_results(df: pd.DataFrame) -> None:
    """Imprime los resultados del benchmark de forma legible."""
    print("\n" + "=" * 110)
    print(f"{'#':<4} {'Consulta':<45} {'Correcto':<9} {'Top-1':<9} {'Score':<8} {'T1':<5} {'T3':<5} Nota")
    print("-" * 110)

    for i, row in df.iterrows():
        t1 = "✓" if row["hit_top1"] else "✗"
        t3 = "✓" if row["hit_top3"] else "✗"
        q = row["query"][:44]
        print(
            f"{i:<4} {q:<45} {row['correct_code']:<9} {row['top1_code']:<9} "
            f"{row['top1_score']:<8} {t1:<5} {t3:<5} {row['note']}"
        )

    print("=" * 110)

    # Métricas globales
    top1_acc = df["hit_top1"].mean()
    top3_acc = df["hit_top3"].mean()
    avg_score = df["top1_score"].mean()

    print(f"\n📊 RESULTADOS GLOBALES (n={len(df)})")
    print(f"   Top-1 Accuracy : {top1_acc:.1%}")
    print(f"   Top-3 Accuracy : {top3_acc:.1%}")
    print(f"   Score promedio : {avg_score:.4f}")

    # Métricas por tipo de dificultad
    print("\n📊 ACCURACY POR TIPO DE DIFICULTAD")
    print(f"   {'Tipo':<35} {'n':<5} {'Top-1':<10} {'Top-3'}")
    print(f"   {'-' * 60}")
    tipo_labels = {
        "F": "F: Control / fáciles",
        "A": "A: Jerga / informalidad regional",
        "B": "B: Ambigüedad entre códigos",
        "C": "C: Trabajo mixto",
        "D": "D: Variación regional del español",
        "E": "E: Tecnicismo / formalidad",
    }
    for tipo, label in tipo_labels.items():
        sub = df[df["difficulty"] == tipo]
        if not sub.empty:
            t1 = sub["hit_top1"].mean()
            t3 = sub["hit_top3"].mean()
            print(f"   {label:<35} {len(sub):<5} {t1:<10.1%} {t3:.1%}")

    # Veredicto
    print("\n🏁 VEREDICTO:")
    if top3_acc >= 0.70:
        print("   ✅ Top-3 Accuracy ≥ 70% → Pipeline viable. Avanzar a Fase 1.")
    elif top3_acc >= 0.50:
        print("   ⚠️  Top-3 Accuracy entre 50-70% → Probar con modelo más potente.")
        print("      Sugerencia: paraphrase-multilingual-mpnet-base-v2")
    else:
        print("   ❌ Top-3 Accuracy < 50% → Cambiar a intfloat/multilingual-e5-large.")

    # Exportar resultados
    out_path = ROOT / "poc" / "benchmark_results_mpnet.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 Resultados exportados a: {out_path}")


def main():
    print("=" * 60)
    print("ClassifAI-LAC — Fase 0: Benchmark de Accuracy")
    print(f"Modelo: {MODEL}")
    print(f"Muestra: {len(SAMPLE)} casos (F/A/B/C/D/E)")
    print("=" * 60)

    # Cargar vectorizador y construir store
    print("\n[1/2] Cargando modelo y construyendo VectorStore...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    store = VectorStore(
        file_name=DATA_FILE,
        data_type="csv",
        vectoriser=vectoriser,
        overwrite=True,
    )
    print(f"      [OK] VectorStore creado con {store.num_vectors} entradas CIUO-08")

    # Ejecutar benchmark
    print("\n[2/2] Ejecutando benchmark...")
    df = run_benchmark(store, SAMPLE, n_results=3)

    # Imprimir resultados
    print_results(df)


if __name__ == "__main__":
    main()
