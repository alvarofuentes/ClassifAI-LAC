"""Gestor de estados para jobs asíncronos (Fase 2a).

Maneja el estado en memoria de los trabajos de procesamiento en lote (Batch).
Soporta estados: PENDING, PROCESSING, COMPLETED, FAILED.
"""

import uuid
from datetime import datetime
from threading import Lock
from typing import Any

# Tipos de estado
STATUS_PENDING = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"


class JobManager:
    """Implementación thread-safe para rastrear tareas en background."""

    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create_job(self, classifier: str, filename: str, total_chunks: int = 0) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "classifier": classifier,
                "filename": filename,
                "status": STATUS_PENDING,
                "progress": 0.0,
                "message": "En cola para procesamiento",
                "total_chunks": total_chunks,
                "processed_chunks": 0,
                "output_file": None,
                "error": None,
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": None,
            }
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._jobs.get(job_id, None)

    def update_status(
        self,
        job_id: str,
        status: str,
        progress: float | None = None,
        message: str | None = None,
        processed_chunks: int | None = None,
        output_file: str | None = None,
        error: str | None = None,
    ):
        with self._lock:
            if job_id not in self._jobs:
                return

            job = self._jobs[job_id]
            job["status"] = status

            if progress is not None:
                job["progress"] = progress
            if message is not None:
                job["message"] = message
            if processed_chunks is not None:
                job["processed_chunks"] = processed_chunks
            if output_file is not None:
                job["output_file"] = output_file
            if error is not None:
                job["error"] = error

            if status in [STATUS_COMPLETED, STATUS_FAILED]:
                job["completed_at"] = datetime.utcnow().isoformat()
                if status == STATUS_COMPLETED and progress is None:
                    job["progress"] = 100.0


# Singleton en memoria para toda la aplicación FastAPI
job_manager = JobManager()
