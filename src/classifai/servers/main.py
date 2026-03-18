# pylint: disable=C0301
"""This module provides functionality for creating a start a restAPI service which
allows a user to call the search methods of different VectorStore objects, from
an api-endpoint.

These functions interact with the ClassifAI PackageIndexer modules
VectorStore objects, such that their embed and search methods are exposed on
restAPI endpoints, in a FastAPI restAPI service started with these functions.
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import Annotated, Literal

import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from ..exceptions import ConfigurationError, DataValidationError
from ..indexers.dataclasses import (
    VectorStoreEmbedInput,
    VectorStoreReverseSearchInput,
    VectorStoreSearchInput,
)
from ..indexers.main import VectorStore
from .pydantic_models import (
    ClassifaiData,
    EmbeddingsList,
    EmbeddingsResponseBody,
    ResultsResponseBody,
    RevClassifaiData,
    RevResultsResponseBody,
    convert_dataframe_to_pydantic_response,
    convert_dataframe_to_reverse_search_pydantic_response,
)


def get_router(vector_stores: list[VectorStore], endpoint_names: list[str]) -> APIRouter:
    """Create and return a `FastAPI.APIRouter` with search endpoints.

    Args:
        vector_stores (list[VectorStore]): A list of `VectorStore` objects, each responsible for handling embedding and search operations for a specific endpoint.
        endpoint_names (list[str]): A list of endpoint names corresponding to the vector stores.

    Returns:
        (APIRouter): Router with intialized search endpoints

    Raises:
        `DataValidationError`: Raised if the input parameters are invalid.
        `ConfigurationError`: Raised if one or more of the `vector_stores` are invalid.

    """
    # ---- Validate startup args -> DataValidationError / ConfigurationError
    if not isinstance(vector_stores, list) or not isinstance(endpoint_names, list):
        raise DataValidationError(
            "vector_stores and endpoint_names must be lists.",
            context={
                "vector_stores_type": type(vector_stores).__name__,
                "endpoint_names_type": type(endpoint_names).__name__,
            },
        )

    if len(vector_stores) != len(endpoint_names):
        raise DataValidationError(
            "The number of vector stores must match the number of endpoint names.",
            context={"n_vector_stores": len(vector_stores), "n_endpoint_names": len(endpoint_names)},
        )

    if any(not isinstance(x, str) or not x.strip() for x in endpoint_names):
        raise DataValidationError(
            "All endpoint_names must be non-empty strings.",
            context={"endpoint_names": endpoint_names},
        )

    if len(set(endpoint_names)) != len(endpoint_names):
        raise DataValidationError(
            "endpoint_names must be unique.",
            context={"endpoint_names": endpoint_names},
        )

    for i, vs in enumerate(vector_stores):
        if not isinstance(vs, VectorStore):
            raise ConfigurationError(
                "vector_store must be an instance of the VectorStore class.",
                context={"index": i, "vector_store_type": type(vs).__name__},
            )

    logging.info("Starting ClassifAI Router")
    router = APIRouter()
    vector_stores_dict: dict[str, VectorStore] = dict(zip(endpoint_names, vector_stores, strict=True))
    make_endpoints(router, vector_stores_dict)

    @router.get("/", description="UI accessibility")
    def docs():
        """Redirect users to the API documentation page.

        Returns:
            (RedirectResponse): A response object that redirects the user to the `/docs` page.
        """
        start_page = RedirectResponse(url="/docs")
        return start_page

    return router


def get_server(vector_stores: list[VectorStore], endpoint_names: list[str]) -> FastAPI:
    """Create and return a `FastAPI` server with search endpoints.

    Args:
        vector_stores (list[VectorStore]): A list of `VectorStore` objects, each responsible for handling embedding and search operations for a specific endpoint.
        endpoint_names (list[str]): A list of endpoint names corresponding to the `VectorStore`s to be exposed.

    Returns:
        (FastAPI): Server with intialized search endpoints
    """
    logging.info("Generating ClassifAI API")

    app = FastAPI(title="ClassifAI Demo Server", description="This is a demo server of the ClassifAI server")
    router = get_router(vector_stores, endpoint_names)
    app.include_router(router)
    return app


def run_server(vector_stores: list[VectorStore], endpoint_names: list[str], port: int = 8000):
    """Create and run a `FastAPI` server with search endpoints.

    Args:
        vector_stores (list[VectorStore]): A list of `VectorStore` objects, each responsible for handling embedding and search operations for a specific endpoint.
        endpoint_names (list[str]): A list of endpoint names corresponding to the `VectorStore`s to be exposed.
        port (int): [optional] The port on which the API server will run. Defaults to 8000.

    Raises:
        `DataValidationError`: Raised if the input parameters are invalid, e.g. `port` value is out of bounds.
    """
    logging.info("Starting ClassifAI API")

    MAX_PORT, MIN_PORT = 65535, 1
    if not isinstance(port, int) or port < MIN_PORT or port > MAX_PORT:
        raise DataValidationError(
            "port must be an integer between 1 and 65535.",
            context={"port": port},
        )

    app = get_server(vector_stores, endpoint_names)
    uvicorn.run(app, port=port, log_level="info")


def make_endpoints(router: APIRouter | FastAPI, vector_stores_dict: dict[str, VectorStore]):
    """Create and register the different endpoints to your app.

    Args:
        router (APIRouter | FastAPI): The FastAPI application instance.
        vector_stores_dict (dict[str, VectorStore]): The name of the endpoint to be created.
    """
    for endpoint_name, vector_store in vector_stores_dict.items():
        logging.info("Registering endpoints for: %s", endpoint_name)
        _create_embedding_endpoint(router, endpoint_name, vector_store)
        _create_search_endpoint(router, endpoint_name, vector_store)
        _create_reverse_search_endpoint(router, endpoint_name, vector_store)
        _create_batch_endpoints(router, endpoint_name, vector_store)


def _create_embedding_endpoint(router: APIRouter | FastAPI, endpoint_name: str, vector_store: VectorStore):
    """Create and register an embedding endpoint for a specific `VectorStore`.

    Args:
        router (APIRouter | FastAPI): The `FastAPI` application instance.
        endpoint_name (str): The name of the endpoint to be created.
        vector_store: The vector store object responsible for generating embeddings.

    The created endpoint accepts POST requests with input data, generates embeddings
    for the provided documents, and returns the results in a structured format.
    """

    @router.post(f"/{endpoint_name}/embed", description=f"{endpoint_name} embedding endpoint")
    async def embedding_endpoint(data: ClassifaiData) -> EmbeddingsResponseBody:
        input_ids = [x.id for x in data.entries]
        documents = [x.description for x in data.entries]

        input_data = VectorStoreEmbedInput({"id": input_ids, "text": documents})

        output_data = vector_store.embed(input_data)

        returnable = []
        for _, row in output_data.iterrows():
            returnable.append(
                EmbeddingsList(
                    idx=row["id"],
                    description=row["text"],
                    embedding=row["embedding"].tolist(),  # Convert numpy array to list
                )
            )
        return EmbeddingsResponseBody(data=returnable)


def _create_search_endpoint(router: APIRouter | FastAPI, endpoint_name: str, vector_store: VectorStore):
    """Create and register a search endpoint for a specific `VectorStore`.

    Args:
        router (APIRouter | FastAPI): The `FastAPI` application instance.
        endpoint_name (str): The name of the endpoint to be created.
        vector_store: The `VectorStore` object responsible for performing search operations.

    The created endpoint accepts POST requests with input data and a query parameter
    specifying the number of results to return. It performs a search operation using
    the vector store and returns the results in a structured format.
    """

    @router.post(f"/{endpoint_name}/search", description=f"{endpoint_name} search endpoint")
    async def search_endpoint(
        data: ClassifaiData,
        n_results: Annotated[
            int,
            Query(
                description="The number of knowledgebase results to return per input query.",
                ge=1,  # Ensure at least one result is returned
            ),
        ] = 10,
    ) -> ResultsResponseBody:
        input_ids = [x.id for x in data.entries]
        queries = [x.description for x in data.entries]

        input_data = VectorStoreSearchInput({"id": input_ids, "query": queries})
        output_data = vector_store.search(query=input_data, n_results=n_results)

        ##post processing of the Vectorstore outputobject
        formatted_result = convert_dataframe_to_pydantic_response(
            df=output_data,
            meta_data=vector_store.meta_data,
        )

        return formatted_result


def _create_reverse_search_endpoint(router: APIRouter | FastAPI, endpoint_name: str, vector_store: VectorStore):
    """Create and register a reverse_search endpoint for a specific vector store.

    Args:
        router (APIRouter | FastAPI): The `FastAPI` application instance.
        endpoint_name (str): The name of the endpoint to be created.
        vector_store: The `VectorStore` object responsible for performing search operations.

    The created endpoint accepts POST requests with input data and a query parameter
    specifying the number of results to return. It performs a reverse search operation using
    the vector store and returns the results in a structured format.
    """

    @router.post(f"/{endpoint_name}/reverse_search", description=f"{endpoint_name} reverse query endpoint")
    def reverse_search_endpoint(
        data: RevClassifaiData,
        max_n_results: Annotated[
            int | Literal[-1],
            Query(description="The max number of results to return, set to -1 to return all results."),
        ] = 100,
        partial_match: Annotated[
            bool, Query(description="Flag to use partial `starts_with` matching for queries")
        ] = False,
    ) -> RevResultsResponseBody:
        # Enforce the ≥1 rule manually, only when not -1
        if max_n_results != -1 and max_n_results < 1:
            raise HTTPException(422, "max_n_results must be -1 or >= 1")

        input_ids = [x.id for x in data.entries]
        queries = [x.code for x in data.entries]

        input_data = VectorStoreReverseSearchInput({"id": input_ids, "doc_id": queries})
        output_data = vector_store.reverse_search(input_data, max_n_results=max_n_results, partial_match=partial_match)

        formatted_result = convert_dataframe_to_reverse_search_pydantic_response(
            df=output_data,
            meta_data=vector_store.meta_data,
        )
        return formatted_result


def _create_batch_endpoints(router: APIRouter | FastAPI, endpoint_name: str, vector_store: VectorStore):
    """Crea los endpoints asíncronos para procesamiento por lotes (Fase 2a)."""
    # Directorio temporal para los archivos batch
    BATCH_DIR = os.path.join("data", "batch_tmp")
    os.makedirs(BATCH_DIR, exist_ok=True)

    @router.post(f"/{endpoint_name}/batch", description=f"{endpoint_name} batch processing (CSV)")
    async def batch_start_endpoint(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        lang: str = Query("es", description="Language for output descriptions (es, en, pt...)"),
    ):
        from ..batch_processor import process_batch_job
        from .jobs import job_manager

        # Mimetype & Extension check
        allowed_mimes = ["text/csv", "application/vnd.ms-excel", "text/plain"]
        if not file.filename.endswith(".csv") or file.content_type not in allowed_mimes:
            raise HTTPException(400, "Solo se admiten archivos .csv válidos")

        # Payload limit check (Max 50MB)
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > 50 * 1024 * 1024:
            raise HTTPException(413, "El archivo supera el límite de 50MB en RAM permitido.")

        # Crear entrada en el Gestor de Trabajos
        job_id = job_manager.create_job(classifier=endpoint_name, filename=file.filename)

        input_filepath = os.path.join(BATCH_DIR, f"{job_id}_input.csv")
        output_filepath = os.path.join(BATCH_DIR, f"{job_id}_output.csv")

        # Guardar archivo subido asíncronamente
        with open(input_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Encolar procesamiento iterativo
        background_tasks.add_task(
            process_batch_job,
            job_id=job_id,
            classifier=endpoint_name,
            vector_store=vector_store,
            input_filepath=input_filepath,
            output_filepath=output_filepath,
            lang=lang,
        )

        return {"job_id": job_id, "status": "Job enqueued", "filename": file.filename}

    @router.get(f"/{endpoint_name}/batch/{{job_id}}/status", description="Check batch job status")
    async def batch_status_endpoint(job_id: str):
        from .jobs import job_manager

        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job no encontrado o expirado")
        return job

    @router.get(f"/{endpoint_name}/batch/{{job_id}}/download", description="Download processed batch CSV")
    async def batch_download_endpoint(job_id: str):
        from .jobs import job_manager

        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job no encontrado")

        if job["status"] != "COMPLETED":
            raise HTTPException(400, f"El trabajo no está completo. Estado actual: {job['status']}")

        if not job["output_file"] or not os.path.exists(job["output_file"]):
            raise HTTPException(500, "El archivo de salida se perdió o no se generó correctamente")

        return FileResponse(
            path=job["output_file"], filename=f"classifai_{endpoint_name}_{job_id}.csv", media_type="text/csv"
        )
