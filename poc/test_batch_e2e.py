"""
Script de Prueba E2E para Procesamiento Batch (Fase 2a).

1. Genera un CSV sintético con 10.000 registros aleatorios.
2. Lo envía al endpoint /batch de la API.
3. Lo "pollea" consultando su estado asíncrono.
4. Cuando finaliza, descarga el CSV resultante.
"""

import csv
import time
import requests
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEST_CSV_PATH = ROOT / "poc" / "dummy_10k.csv"
DOWNLOAD_PATH = ROOT / "poc" / "dummy_10k_result.csv"

# Usaremos un vectorstore más pequeño y rápido para el test, ej. ciiu4_es
CLASSIFIER = "ciiu4_es"
BASE_URL = f"http://localhost:8000/{CLASSIFIER}/batch"

SAMPLE_TEXTS = [
    "taller de reparación de automóviles",
    "cultivo de tomates orgánicos",
    "servicios de desarrollo web e informático",
    "fábrica de galletas y panadería",
    "empresa de extracción pesquera",
    "restaurante de comida rápida"
]

def generate_dummy_csv():
    """Genera 10,000 registros."""
    print(f"[1/4] Generando CSV sintético de 10.000 registros en {TEST_CSV_PATH}...")
    with open(TEST_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id_registro", "literal"])
        for i in range(1, 10001):
            writer.writerow([f"DOC-{i}", random.choice(SAMPLE_TEXTS)])

def upload_to_api() -> str:
    print(f"\n[2/4] Enviando archivo al API ({BASE_URL})...")
    with open(TEST_CSV_PATH, "rb") as f:
        files = {"file": ("dummy_10k.csv", f, "text/csv")}
        params = {"lang": "es"}
        res = requests.post(BASE_URL, files=files, params=params)
    
    res.raise_for_status()
    data = res.json()
    job_id = data["job_id"]
    print(f"  ✅ Archivo recibido correctamente. ID del Job: {job_id}")
    return job_id

def poll_status(job_id: str):
    url = f"{BASE_URL}/{job_id}/status"
    print(f"\n[3/4] Monitoreando el estado del Job en {url} ...")
    
    start_time = time.time()
    while True:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        
        status = data["status"]
        progress = data["progress"]
        print(f"  [{status}] Avance: {progress:.1f}%")
        
        if status == "COMPLETED":
            break
        elif status == "FAILED":
            print(f"  ❌ Fallo del proceso: {data.get('error')}")
            break
            
        time.sleep(2)
        
    elapsed = time.time() - start_time
    print(f"  ⏱ Tiempo total de procesamiento API: {elapsed:.1f} segundos")

def download_result(job_id: str):
    url = f"{BASE_URL}/{job_id}/download"
    print(f"\n[4/4] Descargando CSV procesado desde {url} ...")
    
    res = requests.get(url)
    res.raise_for_status()
    
    with open(DOWNLOAD_PATH, "wb") as f:
        f.write(res.content)
        
    print(f"  ✅ Guardado en {DOWNLOAD_PATH}")
    
    # Check headers
    with open(DOWNLOAD_PATH, "r", encoding="utf-8-sig") as f:
        header = f.readline().strip()
        print("\n  🔍 Muestra de cabecera descargada:")
        print(f"      {header}")

if __name__ == "__main__":
    generate_dummy_csv()
    job_id = upload_to_api()
    poll_status(job_id)
    download_result(job_id)
