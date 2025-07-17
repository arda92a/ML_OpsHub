from fastapi import FastAPI
from .mlflow_api import router as mlflow_router
from .health import router as health_router
from .root import router as root_router
from utils.logger import setup_logger

logger = setup_logger()

app = FastAPI(
    title="ML Service",
    description="MLflow Model Management Service",
    version="1.0.0"
)

# Router'ları ekle
app.include_router(mlflow_router, prefix="/api/mlflow", tags=["MLflow"])
app.include_router(health_router)
app.include_router(root_router) 