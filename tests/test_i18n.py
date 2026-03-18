from classifai.i18n import get_description


def test_i18n_exact_match():
    """Prueba que el módulo encuentra la descripción en el idioma pedido."""
    desc = get_description("ciiu4_es", "MOCK-1", lang="en")
    assert desc == "Agricultural crops"


def test_i18n_fallback_to_es():
    """Prueba fallback al español ("es") si el idioma solicitado ("fr") no existe."""
    desc = get_description("ciiu4_es", "MOCK-1", lang="fr")
    assert desc == "Cultivos agrícolas"


def test_i18n_fallback_not_found():
    """Prueba que devuelve None si el código no existe y no hay fallback posible."""
    desc = get_description("ciiu4_es", "INVENTADO", lang="en")
    assert desc is None


def test_i18n_api_endpoint_normalization():
    """Valida cómo se normaliza el endpoint name ('ciiu4_es' -> base 'ciiu4')."""
    desc = get_description("ciiu4_es", "MOCK-1", lang="es")
    assert desc == "Cultivos agrícolas"
