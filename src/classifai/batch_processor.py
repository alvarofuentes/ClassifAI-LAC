"""Motor de Procesamiento Batch Asíncrono para ClassifAI-LAC (Fase 2a).

Procesa masivamente archivos CSV por lotes (chunks) de forma asíncrona,
evitando bloqueos en el hilo principal y consumos excesivos de RAM.
Añade 9 columnas (top 1, 2, y 3) y guarda resultados iterativamente.
"""

import logging
import math

import pandas as pd

from classifai.i18n import get_description
from classifai.indexers import VectorStore
from classifai.indexers.dataclasses import VectorStoreSearchInput
from classifai.servers.jobs import STATUS_COMPLETED, STATUS_FAILED, STATUS_PROCESSING, job_manager

logger = logging.getLogger(__name__)

CHUNK_SIZE = 5000  # Cantidad de registros por pasada en memoria


def process_batch_job(
    job_id: str, classifier: str, vector_store: VectorStore, input_filepath: str, output_filepath: str, lang: str = "es"
):
    """Rutina ejecutada vía BackgroundTasks.
    Lee CSV por chunks, clasifica y escribe salida intermitente.
    """
    logger.info(f"[{job_id}] Iniciando tarea batch para {classifier} en idioma {lang}")
    job_manager.update_status(job_id, status=STATUS_PROCESSING, progress=0.0, message="Iniciando lectura en chunks")

    try:
        with open(input_filepath, encoding="utf-8") as f:
            total_rows = sum(1 for _ in f) - 1
        if total_rows <= 0:
            job_manager.update_status(job_id, status=STATUS_FAILED, message="El archivo CSV está vacío o sin registros")
            return

        total_chunks = math.ceil(total_rows / CHUNK_SIZE)
        job_manager.update_status(
            job_id, status=STATUS_PROCESSING, message=f"Total a procesar: {total_rows} filas en {total_chunks} lotes"
        )

        # Variables para escritura iterativa (el primero lleva header)
        first_chunk = True

        for i, chunk in enumerate(pd.read_csv(input_filepath, chunksize=CHUNK_SIZE, dtype=str, encoding="utf-8")):
            # Validar columnas (buscamos ID y Literal, pero seremos flexibles)
            cols = list(chunk.columns)

            # Buscar columna de ID
            id_col = None
            if "id_registro" in cols:
                id_col = "id_registro"
            elif "id" in cols:
                id_col = "id"

            # Si no hay ID, autogeneramos uno temporal
            if not id_col:
                chunk["_auto_id"] = [f"r_{i * CHUNK_SIZE + j}" for j in range(len(chunk))]
                id_col = "_auto_id"

            # Buscar columna de Literal
            literal_col = None
            if "literal" in cols:
                literal_col = "literal"
            elif "text" in cols:
                literal_col = "text"
            elif "descripcion" in cols:
                literal_col = "descripcion"
            else:
                # Si no existe, usamos la primera col string que no sea el id
                candidates = [c for c in cols if c != id_col]
                literal_col = candidates[0] if candidates else id_col

            # Preparar inputs para vector_store
            query_ids = list(chunk[id_col].astype(str).values)
            query_texts = list(chunk[literal_col].astype(str).values)

            # 1. Búsqueda Vectorial
            search_input = VectorStoreSearchInput({"id": query_ids, "query": query_texts})
            raw_results = vector_store.search(search_input, n_results=3)

            # Convertir a pandas si es necesario (pandera df)
            res_df = raw_results.to_pandas() if hasattr(raw_results, "to_pandas") else raw_results

            # 2. Reestructurar las 9 columnas (top 1 a 3)
            # res_df tiene: query_id, doc_id, doc_text, score, rank (1 a 3)
            # Ordenamos para asegurar que estén iterables
            res_df = res_df.sort_values(by=["query_id", "rank"])

            result_map = {}
            for _, row in res_df.iterrows():
                qid = str(row["query_id"])
                rnk = str(row["rank"])
                if qid not in result_map:
                    result_map[qid] = {}

                # Rescate multi-idioma
                code = str(row["doc_id"])
                # Intentamos buscar en i18n
                i18n_desc = get_description(api_endpoint_name=classifier, code=code, lang=lang)
                desc = i18n_desc if i18n_desc else str(row["doc_text"])

                result_map[qid][f"codigo_{rnk}"] = code
                result_map[qid][f"descripcion_{rnk}"] = desc
                result_map[qid][f"prob_{rnk}"] = round(float(row["score"]), 4)

            # 3. Concatenar resultados al chunk original
            new_cols = {
                "codigo_1": [],
                "descripcion_1": [],
                "prob_1": [],
                "codigo_2": [],
                "descripcion_2": [],
                "prob_2": [],
                "codigo_3": [],
                "descripcion_3": [],
                "prob_3": [],
            }

            for _, row in chunk.iterrows():
                qid = str(row[id_col])
                r_data = result_map.get(qid, {})
                for k, v_list in new_cols.items():
                    v_list.append(r_data.get(k, ""))

            # Añadir al df y remover columna temporal si se creó
            for k, v_list in new_cols.items():
                chunk[k] = v_list

            if "_auto_id" in chunk.columns:
                chunk.drop(columns=["_auto_id"], inplace=True)

            # 4. Escribir/appendear a disco
            mode = "w" if first_chunk else "a"
            header = first_chunk
            chunk.to_csv(output_filepath, mode=mode, header=header, index=False, encoding="utf-8-sig")
            first_chunk = False

            # Actualizar progreso
            processed_so_far = (i + 1) * CHUNK_SIZE
            progress = min(100.0, (processed_so_far / total_rows) * 100)

            job_manager.update_status(
                job_id,
                status=STATUS_PROCESSING,
                progress=progress,
                message=f"Procesando lote {i + 1} de {total_chunks}",
                processed_chunks=i + 1,
            )
            logger.info(f"[{job_id}] Avance: {progress:.1f}%")

        # Fin del for
        job_manager.update_status(
            job_id,
            status=STATUS_COMPLETED,
            progress=100.0,
            message="Archivo finalizado con éxito",
            output_file=output_filepath,
        )
        logger.info(f"[{job_id}] Trabajo completado y guardado en {output_filepath}")

    except Exception as e:
        logger.error(f"[{job_id}] Fallo crítico: {e}")
        job_manager.update_status(job_id, status=STATUS_FAILED, message="Error durante procesamiento", error=str(e))
