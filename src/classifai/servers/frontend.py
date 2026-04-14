import json
import logging
from pathlib import Path
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

frontend_router = APIRouter()

# Paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
LOCALES_DIR = FRONTEND_DIR / "locales"

# Setup Jinja2 Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load translations
translations: dict[str, dict[str, str]] = {}
for locale_file in LOCALES_DIR.glob("*.json"):
    lang_code = locale_file.stem
    with open(locale_file, encoding="utf-8") as f:
        translations[lang_code] = json.load(f)

def get_translator(lang: str):
    # Fallback to Spanish 'es' if language not supported
    active_dict = translations.get(lang, translations.get("es", {}))
    def translate(key: str) -> str:
        return active_dict.get(key, key)
    return translate

def get_available_classifiers(translate_func):
    # BASE_DIR is src/classifai. Its parent is src. Its parent.parent is the project root.
    indices_dir = BASE_DIR.parent.parent / "data" / "indices"
    if not indices_dir.exists():
        return []
        
    color_map = ["border-primary", "border-secondary", "border-cyan-600", "border-amber-500", "border-emerald-500", "border-indigo-500"]
    icon_map = ["work", "factory", "shopping_cart", "schedule", "account_balance", "nutrition", "inventory_2"]
    
    clfs = []
    # Usar solo los directorios válidos como en serve_api.py
    dirs = sorted([d.name for d in indices_dir.iterdir() if d.is_dir() and (d / "vectors.parquet").exists()])
    
    # Exclude dummy/test classifiers (if any)
    exclude = []
    dirs = [d for d in dirs if d not in exclude]
    
    for i, name in enumerate(dirs):
        clfs.append({
            "id": name,
            "name": translate_func(f"{name}_name"),
            "description": translate_func(f"{name}_desc"),
            "version": "v1.0",
            "status": "Online",
            "border_color": color_map[i % len(color_map)],
            "icon_color": color_map[i % len(color_map)].replace('border-', 'text-'),
            "icon": icon_map[i % len(icon_map)]
        })
    return clfs

@frontend_router.get("/ui", response_class=HTMLResponse, description="UI Dashboard")
async def dashboard(request: Request, lang: str = Query("es")):
    """Serves the main dashboard UI."""
    translate_func = get_translator(lang)
    classifiers = get_available_classifiers(translate_func)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "lang": lang,
            "_": translate_func,
            "active_tab": "dashboard",
            "classifiers": classifiers,
            "total_classifiers": len(classifiers)
        }
    )

@frontend_router.get("/query", response_class=HTMLResponse, description="Live Query UI")
async def live_query(request: Request, lang: str = Query("es")):
    translate_func = get_translator(lang)
    classifiers = get_available_classifiers(translate_func)
    return templates.TemplateResponse(
        "query.html",
        {
            "request": request,
            "lang": lang,
            "_": translate_func,
            "active_tab": "query",
            "classifiers": classifiers
        }
    )

@frontend_router.get("/batch", response_class=HTMLResponse, description="Batch UI")
async def batch_processing(request: Request, lang: str = Query("es")):
    translate_func = get_translator(lang)
    classifiers = get_available_classifiers(translate_func)
    jobs = []
    return templates.TemplateResponse(
        "batch.html",
        {
            "request": request,
            "lang": lang,
            "_": translate_func,
            "active_tab": "batch",
            "classifiers": classifiers,
            "jobs": jobs
        }
    )

@frontend_router.get("/archive", response_class=HTMLResponse, description="Archive UI")
async def archive(request: Request, lang: str = Query("es")):
    return templates.TemplateResponse(
        "archive.html",
        {
            "request": request,
            "lang": lang,
            "_": get_translator(lang),
            "active_tab": "archive"
        }
    )

# Admin UI routes
@frontend_router.get("/admin/training", response_class=HTMLResponse, description="Admin Training Hub UI")
async def admin_training(request: Request, lang: str = Query("es")):
    translate_func = get_translator(lang)
    classifiers = get_available_classifiers(translate_func)
    return templates.TemplateResponse(
        "admin_training.html",
        {
            "request": request,
            "lang": lang,
            "_": translate_func,
            "active_tab": "admin",
            "classifiers": classifiers
        }
    )

from pydantic import BaseModel
class ExampleInput(BaseModel):
    id: str
    text: str

@frontend_router.post("/api/admin/examples/{classifier}", description="Append new example for a classifier")
async def add_example(classifier: str, data: ExampleInput):
    import csv
    from datetime import datetime
    
    # Check if this classifier exists roughly
    indices_dir = BASE_DIR.parent.parent / "data" / "indices"
    if not (indices_dir / classifier).exists():
        from fastapi import HTTPException
        raise HTTPException(404, "Classifier not found")
        
    file_path = BASE_DIR.parent.parent / "data" / "raw" / f"{classifier}_examples_manual.csv"
    
    file_exists = file_path.exists()
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id", "text", "added_at"])
        writer.writerow([data.id, data.text, datetime.now().isoformat()])
        
    return {"status": "success", "message": "Example appended"}

from fastapi import UploadFile, File
import io

@frontend_router.post("/api/admin/examples_upload/{classifier}", description="Upload CSV of examples")
async def upload_examples(classifier: str, file: UploadFile = File(...)):
    import csv
    from datetime import datetime
    from fastapi import HTTPException
    
    indices_dir = BASE_DIR.parent.parent / "data" / "indices"
    if not (indices_dir / classifier).exists():
        raise HTTPException(404, "Classifier not found")
        
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be valid UTF-8 CSV")
        
    reader = csv.reader(io.StringIO(text_content))
    rows = list(reader)
    if not rows:
        raise HTTPException(400, "Empty CSV file")
        
    # Assume first row could be header if it contains non-code like 'id', 'code'
    if rows[0][0].lower() in ['id', 'código', 'codigo', 'code']:
        rows = rows[1:]
        
    if not rows or len(rows[0]) < 2:
        raise HTTPException(400, "CSV must have at least two columns: ID, Text")
        
    file_path = BASE_DIR.parent.parent / "data" / "raw" / f"{classifier}_examples_manual.csv"
    file_exists = file_path.exists()
    
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id", "text", "added_at"])
        
        count = 0
        now_str = datetime.now().isoformat()
        for row in rows:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                writer.writerow([row[0].strip(), row[1].strip(), now_str])
                count += 1
                
    return {"status": "success", "message": f"{count} examples appended from file"}

@frontend_router.post("/api/admin/rebuild/{classifier}", description="Rebuild VectorStore for classifier")
async def rebuild_classifier(classifier: str):
    import sys
    import os
    import subprocess
    from classifai.indexers import VectorStore
    
    build_script = str(BASE_DIR.parent.parent / "src" / "build_index.py")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        result = subprocess.run(
            [sys.executable, build_script, "--classifier", classifier], 
            check=True, 
            cwd=str(BASE_DIR.parent.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env
        )
    except subprocess.CalledProcessError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {e.stderr or e.stdout or str(e)}")

        
    # Hot Reload in memory
    from classifai.servers.main import GLOBAL_VECTOR_STORES
    if classifier in GLOBAL_VECTOR_STORES:
        vec_store_dir = BASE_DIR.parent.parent / "data" / "indices" / classifier
        old_store = GLOBAL_VECTOR_STORES[classifier]
        try:
            new_store = VectorStore.from_filespace(str(vec_store_dir), old_store.vectoriser, old_store.hooks)
            GLOBAL_VECTOR_STORES[classifier] = new_store
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Failed to load new VectorStore into memory: {str(e)}")
            
    return {"status": "success", "message": f"Index for {classifier} rebuilt and hot reloaded"}

