"""Servicio API REST para ClassifAI-LAC (CIUO-08)."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifai.indexers import VectorStore
from classifai.servers.main import run_server
from classifai.vectorisers import HuggingFaceVectoriser

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
VS_DIR = ROOT / "data" / "vectorstore_ciuo08_es"

def main():
    print("==================================================")
    print("ClassifAI-LAC — Iniciando Servicio API REST")
    print("==================================================\n")

    if not VS_DIR.exists():
        print(f"❌ Error: No se encontró el VectorStore en {VS_DIR}")
        print("Ejecuta primero: python src/build_index.py")
        sys.exit(1)

    print("[1/3] Cargando modelo HuggingFace...")
    vectoriser = HuggingFaceVectoriser(model_name=MODEL)
    
    print(f"\n[2/3] Cargando VectorStore desde {VS_DIR}...")
    store = VectorStore.from_filespace(
        folder_path=str(VS_DIR), 
        vectoriser=vectoriser
    )
    
    print("\n[3/3] Levantando servidor rápido (Uvicorn/FastAPI)...")
    print("👉 Puedes probar la API en: http://localhost:8000/docs")
    
    # Inicia la API y bloquea la ejecución
    run_server([store], endpoint_names=["ciuo08"])

if __name__ == "__main__":
    main()
