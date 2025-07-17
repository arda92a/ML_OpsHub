import requests
import json
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from services.training_service import train_model_pipeline
from utils.logger import logger

router = APIRouter()
# logger = logging.getLogger("analysis-service")  # Artık loguru kullanılacak

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001/api/mlflow")

class ModelSubmissionRequest(BaseModel):
    model_name: str
    model_type: str
    metrics: Dict[str, Any]
    run_name: Optional[str] = None

class TrainRequest(BaseModel):
    model_name: str
    model_type: str
    test_size: float
    random_state: int
    # Gerekirse başka parametreler eklenebilir

@router.get("/latest-model")
async def get_latest_model(model_name: Optional[str] = None):
    """
    MLflow'dan en son model versiyonunu alır
    """
    try:
        params = {}
        if model_name:
            params["model_name"] = model_name
        
        response = requests.get(f"{ML_SERVICE_URL}/models/latest", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Latest model getirme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-model")
async def train_model(
    model_name: str = Form(...),
    model_type: List[str] = Form(...),
    test_size: float = Form(...),
    random_state: Optional[int] = Form(None),
    target_column: str = Form(...),
    problem_type: str = Form(None),
    data_file: UploadFile = File(...)
):
    """
    API üzerinden model eğitimi başlatır.
    """
    try:
        # Dosyayı geçici olarak kaydet
        file_bytes = await data_file.read()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        # Yüklenen dosyanın gerçek adını (uzantısız) al
        data_file_name = os.path.splitext(data_file.filename)[0]
        logger.info(f"MODEL_TRAIN: data_file.filename = {data_file.filename}, data_file_name = {data_file_name}")
        results = train_model_pipeline(
            data_path=tmp_path,
            model_name=model_name,
            model_type=model_type,
            test_size=test_size,
            random_state=random_state,
            target_column=target_column,
            problem_type=problem_type,
            data_file_name=data_file_name
        )
        return {"message": "Model(ler) eğitimi tamamlandı", "results": results}
    except Exception as e:
        logger.error(f"Eğitim hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))
