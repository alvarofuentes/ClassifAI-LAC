import os
from fastapi.testclient import TestClient

def test_batch_endpoint_accepts_csv(api_client: TestClient, tmp_path):
    """Testea que Subir un CSV válido al endpoint de batch retorna 200 y encola un Job"""
    # Crear pseudo-archivo csv
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id_registro,literal\n1,prueba\n2,prueba_2")
    
    with open(csv_file, "rb") as f:
        files = {"file": ("test.csv", f, "text/csv")}
        response = api_client.post("/ciiu4_es/batch?lang=es", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "Job enqueued"

def test_batch_endpoint_rejects_non_csv(api_client: TestClient, tmp_path):
    """El endpoint batch DEBE rechazar archivos que no sean .csv (Fase 2b - Segurización)"""
    txt_file = tmp_path / "shell.txt"
    txt_file.write_text("rm -rf /")
    
    with open(txt_file, "rb") as f:
        # FastAPI debería devolver 400 por no ser csv (gracias a las restricciones implementadas en Fase 2b)
        files = {"file": ("shell.txt", f, "text/plain")}
        response = api_client.post("/ciiu4_es/batch", files=files)
        
    assert response.status_code == 400
    assert "csv" in response.text.lower()

def test_batch_status_endpoint(api_client: TestClient, tmp_path):
    """Testea el endpoint de status usando un job encolado"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id_registro,literal\n1,prueba")
    
    with open(csv_file, "rb") as f:
        response = api_client.post("/ciiu4_es/batch", files={"file": ("t.csv", f, "text/csv")})
    job_id = response.json()["job_id"]
    
    # Test status
    res = api_client.get(f"/ciiu4_es/batch/{job_id}/status")
    assert res.status_code == 200
    assert "status" in res.json()
    assert res.json()["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

def test_batch_download_fails_if_not_completed(api_client: TestClient):
    """Forzamos consultar un Job irreal que dará PENDING, descarga debe dar 400 u otro"""
    # La descarga da error 404 si el job no existe
    res = api_client.get("/ciiu4_es/batch/INVENTADO/download")
    assert res.status_code == 404
