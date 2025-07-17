import sys
from pathlib import Path
import uvicorn
from config.config import Config
from utils.logger import setup_logger

# Path setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.ml_api_server import app  # FastAPI app nesnesi artık burada

logger = setup_logger()

def main():
    """Ana uygulama başlatıcı"""
    logger.info("ML Service başlatılıyor...")
    
    # Konfigürasyon
    config = Config.from_env()
    
    logger.info(f"MLflow Tracking URI: {config.mlflow.tracking_uri}")
    logger.info(f"Experiment Name: {config.mlflow.experiment_name}")
    logger.info(f"API Host: {config.api.host}:{config.api.port}")
    
    # Uvicorn ile server'ı başlat
    uvicorn.run(
        "api.ml_api_server:app",
        host=config.api.host,
        port=config.api.port,
        reload=False,
        log_level=config.log_level.lower()
    )

if __name__ == "__main__":
    main()