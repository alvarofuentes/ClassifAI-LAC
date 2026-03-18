"""
Script para construir todos los VectorStores del Data Lake de ClassifAI-LAC.

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
    """Retorna todos los CSVs disponibles en data/raw/."""
    if not RAW_DIR.exists():
        return []
    return sorted(RAW_DIR.glob("*.csv"))


def build_single_index(csv_path: Path, vectoriser: HuggingFaceVectoriser) -> None:
    """Construye el VectorStore para un CSV dado."""
    # El nombre del índice es el stem del CSV (ej. 'ciuo08_es', 'ciiu4_es')
    classifier_name = csv_path.stem
    out_dir = INDICES_DIR / classifier_name

    print(f"\n{'─'*55}")
    print(f"  Clasificador : {classifier_name}")
    print(f"  Origen       : {csv_path.name}")
    print(f"  Destino      : data/indices/{classifier_name}/")
    print(f"{'─'*55}")

    if out_dir.exists():
        print(f"  🧹 Limpiando índice previo...")
        shutil.rmtree(out_dir, ignore_errors=True)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Cambiar al directorio data/ para que VectorStore use rutas relativas correctas
    original_cwd = os.getcwd()
    os.chdir(ROOT / "data")
    try:
        store = VectorStore(
            file_name=str(csv_path.relative_to(ROOT / "data")),
            data_type="csv",
            vectoriser=vectoriser,
            output_dir=str(out_dir.relative_to(ROOT / "data")),
            overwrite=True,
        )
        print(f"  ✅ Índice construido — {store.num_vectors} entradas")
    finally:
        os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(
        description="Construye el Data Lake vectorial de ClassifAI-LAC"
    )
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
