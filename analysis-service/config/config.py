import os
from dataclasses import dataclass, field


@dataclass
class MinIOConfig:
    endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    bucket_name: str = os.getenv("MINIO_BUCKET", "ml-models")
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    @staticmethod
    def from_env() -> "MinIOConfig":
        return MinIOConfig(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket_name=os.getenv("MINIO_BUCKET", "ml-models"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )


@dataclass
class ModelConfig:
    model_name: str =os.getenv("MODEL_NAME", "default_model")
    model_type: str =os.getenv("MODEL_TYPE", "random_forest")
    test_size: float =float(os.getenv("TEST_SIZE", "0.2"))
    random_state: int = int(os.getenv("RANDOM_STATE", "42"))

    @staticmethod
    def from_env() -> "ModelConfig":
        return ModelConfig(
            model_name=os.getenv("MODEL_NAME", "default_model"),
            model_type=os.getenv("MODEL_TYPE", "random_forest"),
            test_size=float(os.getenv("TEST_SIZE", "0.2")),
            random_state=int(os.getenv("RANDOM_STATE", "42")),
        )


@dataclass
class Config:
    minio: MinIOConfig = field(default_factory=MinIOConfig)
    model: ModelConfig = field(default_factory=ModelConfig) 
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    data_path: str = os.getenv("DATA_PATH", "/app/data")

    @staticmethod
    def from_env() -> "Config":
        return Config(
            minio=MinIOConfig.from_env(),
            model=ModelConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            data_path=os.getenv("DATA_PATH", "/app/data"),
        )
