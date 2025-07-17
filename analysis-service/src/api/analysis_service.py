from fastapi import FastAPI, UploadFile, File
from .report_upload_api import router as report_router
from .model_managment_api import router as model_router
from data.loader import DataLoader
import tempfile
import pandas as pd
from fastapi.responses import JSONResponse
from .data_analysis_api import router as data_analysis_router

app = FastAPI()
app.include_router(report_router, prefix="/api", tags=["Report Upload"])
app.include_router(model_router, prefix="/api/models", tags=["Models"])
app.include_router(data_analysis_router, prefix="/api/data", tags=["Data Analysis"]) 