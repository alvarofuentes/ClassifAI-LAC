![ONS Logo](./ONS_Logo_Digital_Colour_Landscape_English_RGB.svg)

### Una herramienta del grupo de Ciencia de Datos e IA de la Oficina Nacional de Estadística (ONS) del Reino Unido, extendida para América Latina y el Caribe (ClassifAI-LAC)

# ClassifAI-LAC (Multi-Clasificador)

ClassifAI es un paquete de Python de código abierto (Licencia MIT) que simplifica la búsqueda semántica y los pipelines de Generación Aumentada por Recuperación (RAG) para tareas de clasificación en la producción de estadísticas oficiales. 

**ClassifAI-LAC** es una implementación extendida que proporciona una **arquitectura multi-clasificador dinámica**, diseñada específicamente para ingestar, indexar y servir *simultáneamente* múltiples catálogos estadísticos oficiales (como CIUO, CIIU, COICOP, CPC, ICCS, CAUTAL, etc.) a través de una API unificada.

Casos de uso:

- **Aplicaciones Web**: ClassifAI-LAC proporciona una interfaz REST lista para producción que sirve como backend para aplicaciones web institucionales que necesiten codificar texto libre.
- **Pipelines / Procesamiento por Lotes**: Procesamiento masivo de respuestas de encuestas mediante colas de trabajo y la API.
- **Análisis**: Precisión "out-of-the-box" sin necesidad de entrenamiento o fine-tuning, dependiente únicamente de la calidad de la base de conocimiento (Data Lake vectorial).

## Características principales de la arquitectura LAC:

- **Data Lake Vectorial Unificado**: Permite construir automáticamente múltiples índices vectoriales a partir de archivos de datos crudos (`data/raw/`).
- **Servidor API Dinámico**: Detecta automáticamente todos los índices disponibles en `data/indices/` y levanta endpoints independientes por clasificador (`/{clasificador}/search`, `/embed`, etc.).
- **Capa de Integridad (TextSanitizer)**: Limpieza automática de caracteres invisibles (BOM, control), normalización Unicode (NFKC) y filtrado de filas corruptas durante la indexación.
- **Consenso Jerárquico (LCP)**: Detección de ambigüedad semántica y sugerencia de códigos raíz comunes para facilitar la revisión humana.
- **Soporte Multilingüe**: Evaluador optimizado con modelos multilingües (ej. `paraphrase-multilingual-mpnet-base-v2`) que soportan input natural en español, inglés, portugués, etc.
- **Normalización L2**: Búsqueda optimizada mediante normalización de vectores (Cosine Similarity) para mayor precisión en el emparejamiento de sinónimos.

## ¿Qué es la búsqueda semántica y RAG?

**Búsqueda semántica** utiliza un vectorizador (un modelo de lenguaje) para convertir cada documento en un vector (embedding). Cuando llega una consulta, esta se vectoriza de la misma manera y se compara con la base de conocimiento calculando similitudes. Se retornan las *N* entradas más cercanas con sus etiquetas, descripciones y puntajes.

**RAG (Generación Aumentada por Recuperación)** implica alimentar estos resultados de búsqueda en el prompt de un modelo de lenguaje generativo para refinar la clasificación o explicar el resultado.

## Instalación

Instala las dependencias usando `uv` (recomendado) o `pip`. 

```bash
# Sincronización completa con uv (incluye dependencias de desarrollo)
uv sync

# O instalar el paquete original de UK ONS mediante pip:
pip install "classifai[all] @ https://github.com/datasciencecampus/classifai/releases/download/v0.2.1/classifai-0.2.1-py3-none-any.whl"
```

## Guía Rápida: Arquitectura Multi-Clasificador

ClassifAI-LAC automatiza el manejo de múltiples catálogos de clasificación.

#### Paso 1: Alimentar el Data Lake
Coloca tus catálogos de clasificación en formato CSV (con columnas `id` y `text`) en la carpeta `data/raw/`. Ejemplo: `ciuo08_es.csv`, `ciiu4_es.csv`.

#### Paso 2: Compilar los Índices Vectoriales
Ejecuta el script de construcción unificado. Este cargará el modelo una sola vez y generará los VectorStores para todos tus catálogos.

```bash
python src/build_index.py
```
Los índices compilados se guardarán en `data/indices/`.

#### Paso 3: Levantar el Servidor API
El servidor detectará dinámicamente los índices disponibles y expondrá los endpoints correspondientes.

```bash
python src/serve_api.py --port 8000
```

```bash
# Ejemplo de búsqueda en el catálogo CIUO-08
curl -X POST http://localhost:8000/ciuo08_es/search \
  -H "Content-Type: application/json" \
  -d '{"entries":[{"id":"1","description":"enfermera de hospital"}]}'
```

## Robustez y Calidad de Datos

ClassifAI-LAC incluye una **Capa de Integridad** que actúa como un firewall de datos. Durante la indexación y la búsqueda:
- Se detecta automáticamente la codificación del archivo (UTF-8, ISO-8859-1, etc.).
- Se eliminan caracteres invisibles y de control que suelen corromper las bases de datos estadísticas.
- Se normalizan los textos (NFKC) para asegurar que "Azúcar" y "Azúcar" sean tratados como la misma palabra.

Además, el campo `is_ambiguous` se activa automáticamente en la API cuando la diferencia de probabilidad entre las mejores opciones es menor a un umbral (0.05), sugiriendo una `raiz_comun` (Longest Common Prefix) para guiar al clasificador humano.

## Estructura del Proyecto

* `data/raw/` - Catálogos de clasificación oficiales en CSV.
* `data/indices/` - Data Lake vectorial compilado.
* `data/benchmarks/` - Casos de prueba sintéticos para evaluar la precisión.
* `poc/` - Pruebas de concepto, scrapers y scripts de evaluación.
* `src/classifai/` - Código fuente principal (motor de embeddings, FastAPI).

## Desarrollo y Contribución

Si eres un desarrollador trabajando en ClassifAI-LAC, asegúrate de activar el entorno virtual y los pre-commit hooks:

```bash
make setup-git-hooks
uv lock
uv sync
```

Para verificar el estilo de código:
```bash
make check-python
```

Para documentación original del paquete, ver [README_EN.md](./README_EN.md).

---
## Agradecimientos y Atribución (Acknowledgements)

El núcleo algorítmico original de este proyecto fue desarrollado por el **Data Science Campus de la Oficina Nacional de Estadística (ONS) del Reino Unido**. 

**ClassifAI-LAC** es un *fork* extendido (bajo licencia MIT) adaptado orgánicamente para soportar arquitecturas dinámicas multi-clasificador asíncronas, procesamiento masivo por lotes (batch) y soporte lingüístico requerido por la CEPAL y los institutos de estadística de América Latina y el Caribe. Agradecemos a los autores originales y mantenedores del repositorio ONS The Alan Turing Institute por su invaluable contribución inicial al ecosistema Open Source.
