import os
from dataclasses import dataclass, field

@dataclass
class MLflowConfig:
    tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME")
    artifact_path: str = os.getenv("MLFLOW_ARTIFACT_PATH", "models")
    registered_model_name: str = os.getenv("MLFLOW_REGISTERED_MODEL_NAME", "classification-model")
    
    @staticmethod
    def from_env() -> "MLflowConfig":
        return MLflowConfig(
            tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
            experiment_name=os.getenv("MLFLOW_EXPERIMENT_NAME"),
            artifact_path=os.getenv("MLFLOW_ARTIFACT_PATH", "models"),
            registered_model_name=os.getenv("MLFLOW_REGISTERED_MODEL_NAME", "classification-model")
        )

@dataclass
class APIConfig:
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8001"))
    analysis_service_url: str = os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8000")
    
    @staticmethod
    def from_env() -> "APIConfig":
        return APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8001")),
            analysis_service_url=os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8000")
        )

@dataclass
class Config:
    mlflow: MLflowConfig = field(default_factory=MLflowConfig)
    api: APIConfig = field(default_factory=APIConfig)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def from_env() -> "Config":
        return Config(
            mlflow=MLflowConfig.from_env(),
            api=APIConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )