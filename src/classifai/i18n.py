"""Módulo de Soporte Multilingüe (i18n) para ClassifAI-LAC (Fase 2a).

Permite cargar diccionarios de descripciones por idioma y retornar la
traducción correcta de un código dado. Funciona como un caché en memoria.
"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Diccionario anidado en memoria: {classifier: {lang: {code: description}}}
# Ejemplo: {"ciuo08": {"es": {"2211": "Médico general"}, "en": {"2211": "General Medical Practitioner"}}}
_i18n_cache: dict[str, dict[str, dict[str, str]]] = {}


def load_all_dictionaries(data_dir: Path):
    """Escanea la carpeta data/raw en busca de catálogos y los carga en memoria.
    Archivos esperados: {clasificador}_{lang}.csv (ej. ciuo08_es.csv, ciuo08_en.csv)
    El CSV debe tener columnas 'id' y 'text'.
    """
    logger.info("Cargando diccionarios i18n desde %s...", data_dir)

    if not data_dir.exists():
        logger.warning("Directorio de diccionarios %s no existe.", data_dir)
        return

    for csv_file in data_dir.glob("*.csv"):
        # Parsear nombre: ciuo08_es.csv -> classifier="ciuo08", lang="es"
        # O si es ciiu4_es.csv -> classifier="ciiu4", lang="es"
        stem = csv_file.stem
        parts = stem.split("_")

        if len(parts) >= 2:
            lang = parts[-1]
            # Todo menos el idioma es el nombre del clasificador
            # ¡Atención! El nombre del endpoint en API es la carpeta entera en 'indices' (ej. ciuo08_es)
            # Para facilitar la relación, indexamos por nombre exacto del índice y un sufijo lang.
            # En realidad, si el índice es "ciuo08_es", buscaríamos su equivalente "en".
            # Es más sencillo cachear por la dupla nombre archivo: ciuo08_en.
            classifier_base = "_".join(parts[:-1])  # ej: "ciuo08"
        else:
            classifier_base = stem
            lang = "es"  # fallback

        load_dictionary(classifier_base, lang, csv_file)


def load_dictionary(classifier_base: str, lang: str, file_path: Path):
    """Carga un solo archivo CSV al caché i18n."""
    if classifier_base not in _i18n_cache:
        _i18n_cache[classifier_base] = {}

    _i18n_cache[classifier_base][lang] = {}

    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Normalizar columnas (esperamos 'id' y 'text')
            id_col = None
            text_col = None
            if reader.fieldnames:
                for col in reader.fieldnames:
                    col_lower = col.lower()
                    if col_lower in {"id", "id_clasificacion"}:
                        id_col = col
                    if col_lower in {"text", "descripcion"}:
                        text_col = col

            if not id_col or not text_col:
                # Fallback empírico asumiendo primera pos es id, segunda es text
                id_col = reader.fieldnames[0]
                text_col = reader.fieldnames[1]

            for row in reader:
                code_str = str(row[id_col]).strip().lower()
                desc_str = str(row[text_col]).strip()
                _i18n_cache[classifier_base][lang][code_str] = desc_str

        logger.info(f"i18n Cache: {classifier_base} [{lang}] -> {len(_i18n_cache[classifier_base][lang])} entradas")
    except Exception as e:
        logger.error(f"Error cargando diccionario {file_path}: {e}")


def get_description(api_endpoint_name: str, code: str, lang: str = "es") -> str | None:
    """Retorna la descripción traducida de un código.
    api_endpoint_name asume formato como "ciuo08_es" u "ocupaciones".
    """
    # Intentar extraer base (ej: ciuo08_es -> ciuo08)
    base = api_endpoint_name
    if base.endswith("_" + base.split("_")[-1]) and len(base.split("_")[-1]) == 2:
        base = "_".join(base.split("_")[:-1])

    code_normalized = str(code).strip().lower()

    # Intentar en el idioma solicitado
    if base in _i18n_cache and lang in _i18n_cache[base] and code_normalized in _i18n_cache[base][lang]:
        return _i18n_cache[base][lang][code_normalized]

    # Fallback 1: Buscar en español ("es") por defecto LAC
    if base in _i18n_cache and "es" in _i18n_cache[base] and code_normalized in _i18n_cache[base]["es"]:
        return _i18n_cache[base]["es"][code_normalized]

    # Fallback 2: Buscar en CUALQUIER idioma disponible
    if base in _i18n_cache:
        for _available_lang, dct in _i18n_cache[base].items():
            if code_normalized in dct:
                return dct[code_normalized]

    return None
