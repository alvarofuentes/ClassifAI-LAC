import pytest
import polars as pl
import pandas as pd
from unittest.mock import MagicMock
from classifai.utils.text_sanitizer import TextSanitizer
from classifai.utils.hierarchy import get_common_prefix
from classifai.servers.pydantic_models import ResultsList, ResultEntry
from classifai.servers.main import convert_dataframe_to_pydantic_response

def test_text_sanitizer_cleans_invisible_chars():
    """Verifica que se eliminen caracteres de control y BOM."""
    dirty_text = "\ufeffTexto\x00 con\x07 basura\x1f"
    clean_text = TextSanitizer.clean_text(dirty_text)
    assert clean_text == "Texto con basura"
    assert "\ufeff" not in clean_text
    assert "\x00" not in clean_text

def test_text_sanitizer_normalization_nfkc():
    """Verifica la normalización Unicode (acentos compuestos vs simples)."""
    # 'a' + '´' (combinated) vs 'á' (single char)
    decomposed = "Azu\u0301car" 
    normalized = TextSanitizer.clean_text(decomposed)
    assert normalized == "Azúcar"
    assert len(normalized) == 6 # Azúcar (6 chars)

def test_hierarchy_get_common_prefix():
    """Valida el cálculo del Longest Common Prefix para códigos."""
    # LCP de 01260104 y 01260200 es 01260
    assert get_common_prefix(["01260104", "01260105", "01260200"]) == "01260"
    assert get_common_prefix(["2211", "2212", "2213"]) == "221"
    assert get_common_prefix(["123", "456"]) == ""

def test_api_ambiguity_logic_detection():
    """
    Verifica que la conversión a Pydantic detecte ambigüedad 
    cuando los scores son muy cercanos (delta < 0.05).
    """
    mock_data = {
        "query_id": ["q1", "q1"],
        "query_text": ["frijoles", "frijoles"],
        "doc_id": ["0126", "2139"],
        "doc_text": ["Frijol crudo", "Frijol volteado"],
        "score": [0.850, 0.849],
        "rank": [1, 2]
    }
    df = pd.DataFrame(mock_data)
    
    # meta debe contener keys si queremos simular metadata, o vacio si no.
    meta = {}
    
    response = convert_dataframe_to_pydantic_response(df, meta)
    
    assert len(response.data) == 1
    assert response.data[0].is_ambiguous is True
    # 0126 y 2139 no tienen prefijo común fuera de ""
    assert response.data[0].suggested_root == ""

def test_api_not_ambiguous_when_clear_winner():
    """Verifica que NO haya ambigüedad si el ganador es claro (delta > 0.05)."""
    mock_data = {
        "query_id": ["q1", "q1"],
        "query_text": ["leche", "leche"], # Dos filas para el mismo query_id
        "doc_id": ["2211", "9999"],
        "doc_text": ["Leche entera", "Piedra"],
        "score": [0.950, 0.400], 
        "rank": [1, 2]
    }
    df = pd.DataFrame(mock_data)
    meta = {}
    
    response = convert_dataframe_to_pydantic_response(df, meta)
    assert response.data[0].is_ambiguous is False
    assert response.data[0].suggested_root == ""
