def test_search_endpoint_success(api_client):
    """Prueba que el endpoint normal search devuelve 3 resultados exitosamente"""
    payload = {
        "entries": [
            {"id": "doc_1", "description": "busco ingeniero de software"}
        ]
    }
    # Asegúrate de usar el endpoint cargado en el fixture api_client (por defecto: /ciiu4_es)
    response = api_client.post("/ciiu4_es/search", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    
    # Check results (mock vector store returns 3)
    entry = data["data"][0]
    assert "response" in entry
    assert len(entry["response"]) == 10
    assert entry["response"][0]["label"] == "MOCK-1"
    
def test_search_endpoint_empty_payload(api_client):
    """Pydantic debe bloquear una request sin 'entries'"""
    response = api_client.post("/ciiu4_es/search", json={})
    # FastApi lanza un 422 Unprocessable Entity
    assert response.status_code == 422

def test_search_endpoint_long_description(api_client):
    """Fase 2b: Pydantic idealmente bloquea textos increíblemente largos (simulado)"""
    # En este test comprobamos que no colapsa, devuelve OK o 422 si Pydantic tiene max_length
    payload = {
        "entries": [
            {"id": "spam_1", "description": "A" * 50000}
        ]
    }
    response = api_client.post("/ciiu4_es/search", json=payload)
    # Por ahora FastAPI procesa sin problemas o el vector store corta, verificamos que no sea 500
    assert response.status_code in [200, 422]
