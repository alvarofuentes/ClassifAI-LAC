![ONS Logo](./ONS_Logo_Digital_Colour_Landscape_English_RGB.svg)

### A tool produced by the UK Office for National Statistics - Central Data Science & AI group, extended for Latin America and the Caribbean (ClassifAI-LAC)

# ClassifAI-LAC (Multi-Classifier)

ClassifAI is a free, open-source (MIT Licence) Python package that simplifies semantic search and Retrieval Augmented Generation (RAG) pipelines for classification tasks in the production of official statistics. 

**ClassifAI-LAC** is an extended implementation that provides a **dynamic multi-classifier architecture**, specifically designed to ingest, index, and serve *simultaneously* multiple official statistical catalogs (such as ISCO, ISIC, COICOP, CPC, ICCS, etc.) through a unified API.

Use cases:

- **Web Apps**: ClassifAI-LAC provides a production-ready REST interface that serves as a backend for institutional web applications needing to code free text.
- **Pipelines / Batch Processing**: Mass processing of survey responses using job queues and the API.
- **Analysis**: "Out-of-the-box" precision requiring no training or fine-tuning, dependent solely on the quality of the knowledgebase (Vector Data Lake).

## Key Features of the LAC Architecture:

- **Unified Vector Data Lake**: Automatically builds multiple vector indices from raw data CSV files (`data/raw/`).
- **Dynamic API Server**: Automatically detects all available indices in `data/indices/` and spins up independent endpoints per classifier (`/{classifier}/search`, `/embed`, etc.).
- **Multilingual Support**: Optimized evaluation using multilingual models (e.g., `paraphrase-multilingual-mpnet-base-v2`) that support natural language input in English, Spanish, Portuguese, etc.

## What are semantic search and RAG?

**Semantic search** uses a vectoriser (usually a language model) to convert each document into a vector (embedding). When a query arrives from a user, it is embedded the same way and compared to the knowledgebase by calculating similarities. The top *N* closest entries are returned along with their labels, descriptions, and scores.

**Retrieval-augmented generation (RAG)** involves feeding search results into the prompt of a generative language model to refine the classification or explain the result.

## Installation

Install dependencies using `uv` (recommended) or `pip`. 

```bash
# Full sync using uv (includes dev dependencies)
uv sync

# Or install the original UK ONS package using pip:
pip install "classifai[all] @ https://github.com/datasciencecampus/classifai/releases/download/v0.2.1/classifai-0.2.1-py3-none-any.whl"
```

## Quick Start: Multi-Classifier Architecture

ClassifAI-LAC automates the handling of multiple classification catalogs.

#### Step 1: Feed the Data Lake
Place your classification catalogs in CSV format (with `id` and `text` columns) inside the `data/raw/` folder. Example: `isco08_en.csv`, `isic4_en.csv`.

#### Step 2: Compile Vector Indices
Run the unified build script. This will load the model just once and generate the VectorStores for all your catalogs seamlessly.

```bash
python src/build_index.py
```
Pre-compiled indices will be stored in `data/indices/`.

#### Step 3: Run the API Server
The server will dynamically detect available indices and expose their corresponding endpoints.

```bash
python src/serve_api.py --port 8000
```

#### Step 4: Query the API
The API supports simultaneous REST queries across different classifications.

```bash
# Example search in the ISCO-08 catalog
curl -X POST http://localhost:8000/ciuo08_es/search \
  -H "Content-Type: application/json" \
  -d '{"entries":[{"id":"1","description":"hospital nurse"}]}'
```

## Project Structure

* `data/raw/` - Raw official classification catalogs in CSV format.
* `data/indices/` - Compiled Vector Data Lake.
* `data/benchmarks/` - Synthetic test cases to evaluate classifier accuracy.
* `poc/` - Proof-of-concept scripts, scrapers, and evaluation routines.
* `src/classifai/` - Core Python package source code (embedding engine, FastAPI).

## Development and Contribution

If you are a developer working on ClassifAI-LAC, make sure to active the virtual environment and install pre-commit hooks:

```bash
make setup-git-hooks
uv lock
uv sync
```

To run python checks:
```bash
make check-python
```

For the original language usage check [README.md](./README.md).

---
## Acknowledgements and Attribution

The original algorithmic core of this project was developed by the **Data Science Campus at the UK Office for National Statistics (ONS)**. 

**ClassifAI-LAC** is an extended fork (under the MIT License) organically adapted to support dynamic async multi-classifier architectures, massive batch processing, and multilingual support required by ECLAC and statistical institutes in Latin America and the Caribbean. We thank the original authors and maintainers at the ONS repository and The Alan Turing Institute for their invaluable initial contribution to the Open Source ecosystem.
