"""Script para construir todos los VectorStores del Data Lake de ClassifAI-LAC.

Itera automáticamente sobre todos los CSVs encontrados en data/raw/ y genera
los índices vectoriales correspondientes en data/indices/<nombre_clasificador>/.

Uso:
    python src/build_index.py                          # Construir todos los índices
    python src/build_index.py --classifier ciuo08_es   # Construir uno solo
    python src/build_index.py --list                   # Listar CSVs disponibles
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.vectorisers import HuggingFaceVectoriser

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
RAW_DIR = ROOT / "data" / "raw"
INDICES_DIR = ROOT / "data" / "indices"


def get_available_csvs() -> list[Path]:
    """Retorna los CSVs base disponibles en data/raw/."""
    if not RAW_DIR.exists():
        return []
    # Se excluyen los archivos de ejemplos y los temporales
    return sorted([p for p in RAW_DIR.glob("*.csv") if "_examples" not in p.name and not p.name.startswith(".tmp")])


def build_single_index(csv_path: Path, vectoriser: HuggingFaceVectoriser) -> None:
    """Construye el VectorStore para un CSV dado y sus ejemplos."""
    import polars as pl

    classifier_name = csv_path.stem
    out_dir = INDICES_DIR / classifier_name

    example_files = sorted(RAW_DIR.glob(f"{classifier_name}_examples*.csv"))
    temp_csv_path = RAW_DIR / f".tmp_merged_{classifier_name}.csv"

    print(f"\n{'─' * 55}")
    print(f"  Clasificador : {classifier_name}")
    print(f"  Origen Base  : {csv_path.name}")
    if example_files:
        print(f"  Ejemplos     : {len(example_files)} archivo(s) detectado(s)")
    print(f"  Destino      : data/indices/{classifier_name}/")
    print(f"{'─' * 55}")

    if out_dir.exists():
        print("  🧹 Limpiando índice previo...")
        shutil.rmtree(out_dir, ignore_errors=True)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Combinar archivos si hay ejemplos
    dfs = []
    try:
        base_df = pl.read_csv(csv_path, schema_overrides={"id": pl.String, "text": pl.String}, ignore_errors=True)
        dfs.append(base_df)
    except Exception as e:
        print(f"Error leyendo archivo base {csv_path}: {e}")
        raise

    for ex_file in example_files:
        try:
            ex_df = pl.read_csv(ex_file, schema_overrides={"id": pl.String, "text": pl.String}, ignore_errors=True)
            dfs.append(ex_df)
        except Exception as e:
            print(f"Error leyendo archivo de ejemplos {ex_file}: {e}")

    # Concatenar en diagonal alinea las columnas y rellena nulls
    merged_df = pl.concat(dfs, how="diagonal")
    merged_df.write_csv(temp_csv_path)

    # Cambiar al directorio data/ para que VectorStore use rutas relativas correctas
    original_cwd = os.getcwd()
    os.chdir(ROOT / "data")
    try:
        store = VectorStore(
            file_name=str(temp_csv_path.relative_to(ROOT / "data")),
            data_type="csv",
            vectoriser=vectoriser,
            output_dir=str(out_dir.relative_to(ROOT / "data")),
            overwrite=True,
        )
        msg_extras = f" (incluye {len(example_files)} docs de ejemplos)" if example_files else ""
        print(f"  ✅ Índice construido — {store.num_vectors} entradas{msg_extras}")
    finally:
        os.chdir(original_cwd)
        # Limpiar archivo temporal concatenado
        if temp_csv_path.exists():
            temp_csv_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Construye el Data Lake vectorial de ClassifAI-LAC")
    parser.add_argument(
        "--classifier",
        type=str,
        default=None,
        help="Nombre del clasificador a construir (ej. ciuo08_es). Si no se especifica, construye todos.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista los CSVs disponibles en data/raw/ sin construir nada.",
    )
    args = parser.parse_args()

    available = get_available_csvs()

    if args.list:
        print("\n📋 CSVs disponibles en data/raw/:")
        if not available:
            print("  (ninguno encontrado)")
        for csv_path in available:
            idx_path = INDICES_DIR / csv_path.stem
            status = "✅ indexado" if idx_path.exists() else "⬜ sin indexar"
            print(f"  {status}  {csv_path.name}  ({csv_path.stat().st_size // 1024} KB)")
        return

    if not available:
        print(f"❌ No se encontraron CSVs en {RAW_DIR}")
        print("   Ejecuta primero los scrapers en poc/scrapers/")
        sys.exit(1)

    # Filtrar por clasificador si se especificó
    if args.classifier:
        targets = [p for p in available if p.stem == args.classifier]
        if not targets:
            print(f"❌ No se encontró '{args.classifier}.csv' en data/raw/")
            print(f"   Disponibles: {[p.stem for p in available]}")
            sys.exit(1)
    else:
        targets = available

    print("=" * 55)
    print("  ClassifAI-LAC — Construcción del Data Lake Vectorial")
    print(f"  Modelo: {MODEL}")
    print(f"  Clasificadores a indexar: {len(targets)}")
    print("=" * 55)

    INDICES_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar el modelo una sola vez (caro en memoria)
    print("\n[1/2] Cargando modelo HuggingFace (puede tomar unos segundos)...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    print("  ✅ Modelo cargado")

    print(f"\n[2/2] Construyendo {len(targets)} índice(s)...")
    errors = []
    for csv_path in targets:
        try:
            build_single_index(csv_path, vectoriser)
        except Exception as e:
            print(f"  ❌ Error procesando {csv_path.name}: {e}")
            errors.append((csv_path.name, str(e)))

    print("\n" + "=" * 55)
    print(f"  Resultado: {len(targets) - len(errors)}/{len(targets)} índices construidos")
    if errors:
        print("  Errores:")
        for name, err in errors:
            print(f"    - {name}: {err}")
    print("=" * 55)


if __name__ == "__main__":
    main()
