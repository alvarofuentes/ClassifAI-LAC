"""
Servicio API REST multi-clasificador para ClassifAI-LAC.

Detecta automáticamente todos los índices vectoriales disponibles en data/indices/
y levanta un endpoint /search, /embed y /reverse_search para cada uno.

Uso:
    python src/serve_api.py                    # Cargar todos los índices
    python src/serve_api.py --port 8080        # Puerto personalizado
    python src/serve_api.py --only ciuo08_es   # Solo un clasificador
    python src/serve_api.py --list             # Listar índices disponibles y salir
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.servers.main import run_server
from classifai.vectorisers import HuggingFaceVectoriser

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
INDICES_DIR = ROOT / "data" / "indices"


def get_available_indices() -> list[Path]:
    """Retorna todos los índices disponibles en data/indices/."""
    if not INDICES_DIR.exists():
        return []
    return sorted(
        [d for d in INDICES_DIR.iterdir() if d.is_dir() and (d / "vectors.parquet").exists()]
    )


def main():
    parser = argparse.ArgumentParser(
        description="ClassifAI-LAC — Servicio API multi-clasificador"
    )
    parser.add_argument("--port", type=int, default=8000, help="Puerto HTTP (default: 8000)")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Cargar solo este clasificador (ej. ciuo08_es). Si no se especifica, carga todos.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista los índices disponibles y sale.",
    )
    args = parser.parse_args()

    available = get_available_indices()

    if args.list:
        print("\n📋 Índices disponibles en data/indices/:")
        if not available:
            print("  (ninguno — ejecuta primero: python src/build_index.py)")
        for idx in available:
            meta = idx / "metadata.json"
            print(f"  ✅  {idx.name}  →  POST /{idx.name}/search")
        return

    if not available:
        print(f"❌ No se encontraron índices en {INDICES_DIR}")
        print("   Ejecuta primero: python src/build_index.py")
        sys.exit(1)

    # Filtrar por --only si se especificó
    if args.only:
        targets = [d for d in available if d.name == args.only]
        if not targets:
            print(f"❌ No se encontró el índice '{args.only}' en data/indices/")
            print(f"   Disponibles: {[d.name for d in available]}")
            sys.exit(1)
    else:
        targets = available

    print("=" * 58)
    print("  ClassifAI-LAC — Servicio API REST Multi-Clasificador")
    print(f"  Modelo  : {MODEL}")
    print(f"  Índices : {len(targets)} clasificador(es)")
    print("=" * 58)

    print("\n[1/3] Cargando modelo HuggingFace (puede tomar unos segundos)...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    print("  ✅ Modelo cargado")

    print(f"\n[2/3] Cargando {len(targets)} índice(s) vectorial(es)...")
    stores = []
    endpoint_names = []

    for idx_dir in targets:
        name = idx_dir.name
        print(f"  📂 Cargando: {name} ...", end=" ", flush=True)
        try:
            store = VectorStore.from_filespace(
                folder_path=str(idx_dir),
                vectoriser=vectoriser,
            )
            stores.append(store)
            endpoint_names.append(name)
            print(f"✅ ({store.num_vectors} entradas)")
        except Exception as e:
            print(f"❌ ERROR: {e}")

    if not stores:
        print("\n❌ No se pudo cargar ningún índice. Abortando.")
        sys.exit(1)

    print(f"\n[3/3] Levantando servidor en http://localhost:{args.port}")
    print("\n👉 Endpoints disponibles:")
    for name in endpoint_names:
        print(f"   POST http://localhost:{args.port}/{name}/search")
    print(f"\n📖 Documentación interactiva: http://localhost:{args.port}/docs")
    print("─" * 58)

    run_server(stores, endpoint_names=endpoint_names, port=args.port)


if __name__ == "__main__":
    main()
