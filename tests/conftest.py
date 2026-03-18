from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from classifai.i18n import _i18n_cache
from classifai.indexers import VectorStore
from classifai.servers.main import get_server


def mock_search(payload=None, n_results=3, **kwargs):
    data = {"query_id": [], "query_text": [], "doc_id": [], "doc_text": [], "score": [], "rank": []}

    # Manejar inputs de endpoint /search
    if payload is None and "inputs" in kwargs:
        # endpoint_search -> inputs = VectorStoreSearchInput(...)
        payload = kwargs["inputs"]
    elif payload is None and "query" in kwargs:
        # otra posibilidad
        pass

    ids = payload.data.get("id", ["1"]) if hasattr(payload, "data") else ["1"]
    queries = payload.data.get("query", [""]) if hasattr(payload, "data") else [""]

    for idx in range(len(ids)):
        qid = str(ids[idx])
        for r in range(1, n_results + 1):
            data["query_id"].append(qid)
            data["query_text"].append(queries[idx])
            data["doc_id"].append(f"MOCK-{r}")
            data["doc_text"].append(f"Mocking desc {r}")
            data["score"].append(1.0 - (0.1 * r))
            data["rank"].append(r)

    return pd.DataFrame(data)


@pytest.fixture
def mock_vector_store():
    # Instanciamos la clase base sin conectarla a disco usando mocks
    store = MagicMock(spec=VectorStore)
    store.num_vectors = 5
    store.meta_data = {}  # Vacio para no pedir keys extra en el formatter
    # Importante: para pasar el isinstance(store, VectorStore) en get_server, el MagicMock con spec lo simula.

    # Pero el código usa type() en algunos lados? get_server hace isinstance(store, VectorStore), spec lo pasa
    store.__class__ = VectorStore
    store.search.side_effect = mock_search
    return store


@pytest.fixture
def api_client(mock_vector_store):
    app = get_server(vector_stores=[mock_vector_store], endpoint_names=["ciiu4_es"])
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def setup_i18n_mock():
    """Inyecta diccionarios de mentira para no depender del disco."""
    _i18n_cache.clear()
    _i18n_cache["ciiu4"] = {"es": {"mock-1": "Cultivos agrícolas"}, "en": {"mock-1": "Agricultural crops"}}
    yield
    _i18n_cache.clear()
