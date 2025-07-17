from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from services.mlflow_client import MLflowService
from config.config import Config
from utils.logger import setup_logger
import os
import zipfile
import io
import tempfile

router = APIRouter()
logger = setup_logger()
config = Config.from_env()
mlflow_service = MLflowService(config.mlflow)

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

def api_response(success: bool, data: Any = None, error: str = None):
    return {"success": success, "data": data, "error": error}

@router.get("/models", response_model=APIResponse)
async def list_models():
    """Tüm modelleri ve tiplerini (classification/regression) ayırarak listeler."""
    result = mlflow_service.list_models_by_type()
    if result is not None:
        return api_response(True, result)
    return api_response(False, None, "Model listesi getirme hatası")

@router.get("/models/{model_name}", response_model=APIResponse)
async def get_model_versions(model_name: str):
    """Bir modelin tüm versiyonlarını ve tipini getirir."""
    result = mlflow_service.get_model_versions(model_name)
    if result is not None:
        return api_response(True, result)
    return api_response(False, None, "Model versiyonları getirme hatası")

@router.get("/models/{model_name}/latest", response_model=APIResponse)
async def get_latest_model(model_name: str):
    """Bir modelin en son versiyonunu getirir."""
    latest_model = mlflow_service.get_latest_model_version(model_name)
    if latest_model:
        return api_response(True, latest_model)
    return api_response(False, None, "Model bulunamadı")

@router.get("/models/{model_name}/version/{version}", response_model=APIResponse)
async def get_model_version(model_name: str, version: int):
    """Bir modelin istenen versiyonunu getirir."""
    model = mlflow_service.get_model_version(model_name, version)
    if model:
        return api_response(True, model)
    return api_response(False, None, "Model veya versiyon bulunamadı")

@router.get("/runs/{run_id}/metrics", response_model=APIResponse)
async def get_run_metrics(run_id: str):
    metrics = mlflow_service.get_run_metrics(run_id)
    if metrics:
        return api_response(True, {"run_id": run_id, "metrics": metrics})
    return api_response(False, None, "Run bulunamadı")

@router.post("/models/compare", response_model=APIResponse)
async def compare_models(request: Dict[str, List[str]]):
    comparison = mlflow_service.compare_models(request.get("run_ids", []))
    if comparison is not None:
        return api_response(True, comparison)
    return api_response(False, None, "Model karşılaştırma hatası")

@router.get("/models/{model_name}/version/{version}/download")
async def download_model(model_name: str, version: int, background_tasks: BackgroundTasks):
    """Belirli bir model versiyonunun artifact dosyasını zip olarak indirir."""
    model = mlflow_service.get_model_version(model_name, version)
    if not model:
        raise HTTPException(status_code=404, detail="Model veya versiyon bulunamadı")
    run_id = model["run_id"]
    # Sadece algorithm_type (model_type) kullanılacak
    model_type = model.get("algorithm_type") or "model"
    local_path = mlflow_service.download_model_artifact(run_id)
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Model artifact bulunamadı")
    # Dosya isimlerini oluştur
    safe_model_name = model_name.replace(" ", "_").replace("/", "_")
    safe_model_type = str(model_type).replace(" ", "_").replace("/", "_")
    zip_filename = f"{safe_model_name}_{safe_model_type}.zip"
    pkl_filename = f"{safe_model_name}_{safe_model_type}.pkl"
    # Geçici zip dosyası oluştur
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(local_path, arcname=pkl_filename)
        zip_path = tmp_zip.name
    background_tasks.add_task(os.remove, zip_path)
    return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")

@router.get("/health", response_model=APIResponse)
async def health_check():
    try:
        experiments = mlflow_service.client.search_experiments()
        data = {
            "mlflow_connection": "ok",
            "tracking_uri": config.mlflow.tracking_uri,
            "experiment_name": config.mlflow.experiment_name,
            "total_experiments": len(experiments)
        }
        return api_response(True, data)
    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e}")
        return api_response(False, None, str(e)) 