from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {
        "service": "ML Service",
        "status": "running",
        "description": "MLflow Model Management Service"
    } 