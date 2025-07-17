from fastapi import FastAPI
from .mlflow_read_api import router as mlflow_router
from utils.logger import setup_logger

logger = setup_logger()

app = FastAPI(
    title="Backend Service",
    description="MLflow Model Read Service",
    version="1.0.0"
)

app.include_router(mlflow_router, prefix="/api/mlflow", tags=["MLflow"]) 