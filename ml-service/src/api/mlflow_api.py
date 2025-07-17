from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from services.mlflow_client import MLflowService
from config.config import Config
from utils.logger import setup_logger
from mlflow.tracking import MlflowClient

logger = setup_logger()
router = APIRouter()

# MLflow service'i başlat
config = Config.from_env()
mlflow_service = MLflowService(config.mlflow)

class ModelSubmissionRequest(BaseModel):
    model_name: str
    model_type: str
    problem_type: str  # classification, regression gibi
    metrics: Dict[str, Any]
    run_name: Optional[str] = None

@router.post("/submit-model")
async def submit_model(
    file: UploadFile = File(...),
    model_name: str = Form(None),
    model_type: str = Form(None),
    problem_type: str = Form(None),
    data_file_name: str = Form(None),
    metrics: str = Form(None),
    run_name: str = Form(None),
    description: str = Form(None)
):
    """
    Analysis service'ten model ve metrikleri al, MLflow'a kaydet
    Sadece model dosyası ve metrikler işlenir, artifact dosyaları loglanmaz.
    """
    try:
        model_data = await file.read()
        # Metrics'i parse et
        if metrics:
            try:
                metrics_dict = json.loads(metrics)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Geçersiz JSON formatı")
        else:
            metrics_dict = {}
        # Model ismini belirle
        if not model_name:
            model_name = file.filename.split('.')[0] if file.filename else "unknown_model"
        if not model_type:
            model_type = "unknown"
        logger.info(f"Gelen problem_type: '{problem_type}'")
        if not problem_type:
            problem_type = "unknown"
        # Run name'i oluştur
        if not run_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"{model_name}_{model_type}_{timestamp}"
        logger.info(f"MLFLOW_API: data_file_name = {data_file_name}")
        # MLflow'a kaydet
        run_id = mlflow_service.log_model_and_metrics(
            model_data=model_data,
            metrics=metrics_dict,
            model_name=model_name,
            model_type=model_type,
            problem_type=problem_type,
            data_file_name=data_file_name,
            run_name=run_name
        )
        # Model versiyonunu bul
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        latest_version = max([int(v.version) for v in versions]) if versions else None
        # Description varsa model versiyonuna ata
        if description and latest_version is not None:
            client.update_model_version(
                name=model_name,
                version=latest_version,
                description=description
            )
        logger.info(f"Model başarıyla kaydedildi. Run ID: {run_id}, Version: {latest_version}")
        return {
            "message": "Model başarıyla MLflow'a kaydedildi",
            "run_id": run_id,
            "model_name": model_name,
            "model_type": model_type,
            "problem_type": problem_type,
            "run_name": run_name,
            "model_version": latest_version
        }
    except Exception as e:
        logger.error(f"Model kaydetme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Model kaydetme hatası: {str(e)}")
    
    

