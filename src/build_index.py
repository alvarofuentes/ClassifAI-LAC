"""Script para construir el VectorStore de producción para la API."""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.vectorisers import HuggingFaceVectoriser

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DATA_CSV = ROOT / "data" / "ciuo08_es.csv"
OUT_DIR = ROOT / "data" / "vectorstore_ciuo08_es"


def main():
    print(f"==================================================")
    print(f"ClassifAI-LAC — Construyendo VectorStore CIUO-08")
    print(f"Modelo: {MODEL}")
    print(f"Origen: {DATA_CSV}")
    print(f"Destino: {OUT_DIR}")
    print(f"==================================================\n")

    # Limpiar directorio si existe previamente (evita errores de sobrescritura de classifai)
    if OUT_DIR.exists():
        print(f"Limpiando directorio destino previo...")
        shutil.rmtree(OUT_DIR, ignore_errors=True)
    
    # 1. Cargar vectorizador
    print("[1/2] Cargando modelo HuggingFace...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)

    # 2. Construir índice
    print("\n[2/2] Construyendo VectorStore...")
    
    # Nos movemos al directorio padre para que classifai guarde la carpeta 
    # con el nombre exacto que queremos sin crear subdirectorios anidados confusos.
    import os
    os.chdir(ROOT / "data")
    
    store = VectorStore(
        file_name="ciuo08_es.csv",
        data_type="csv",
        vectoriser=vectoriser,
        output_dir="vectorstore_ciuo08_es",
        overwrite=True,
    )
    
    print(f"\n✅ VectorStore construido exitosamente con {store.num_vectors} entradas.")
    print(f"Ruta: {ROOT / 'data' / 'vectorstore_ciuo08_es'}")

if __name__ == "__main__":
    main()
