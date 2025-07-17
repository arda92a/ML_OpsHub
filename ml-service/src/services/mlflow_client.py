import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional, List
import joblib
import tempfile
import os
from config.config import MLflowConfig
from utils.logger import setup_logger

logger = setup_logger()

class MLflowService:
    def __init__(self, config: MLflowConfig):
        self.config = config
        self.client = MlflowClient(tracking_uri=config.tracking_uri)
        mlflow.set_tracking_uri(config.tracking_uri)
    
    def _setup_experiment(self):
        """MLflow experiment'i oluştur veya mevcut olanı kullan"""
        try:
            experiment_name = self.config.experiment_name or "default"
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                try:
                    experiment_id = mlflow.create_experiment(experiment_name)
                except Exception as e:
                    # Eğer başka bir servis aynı anda oluşturduysa, tekrar dene
                    experiment = mlflow.get_experiment_by_name(experiment_name)
                    if experiment is not None:
                        experiment_id = experiment.experiment_id
                    else:
                        logger.error(f"Experiment kurulumu hatası: {e}")
                        raise
            else:
                experiment_id = experiment.experiment_id
            mlflow.set_experiment(experiment_name)
            self.experiment_id = experiment_id
        except Exception as e:
            logger.error(f"Experiment kurulumu hatası: {e}")
            raise
    
    def log_model_and_metrics(self, 
                            model_data: bytes,
                            metrics: Dict[str, Any],
                            model_name: str,
                            model_type: str,
                            problem_type: str,
                            data_file_name: str,
                            run_name: Optional[str] = None) -> str:
        """Model ve metrikleri MLflow'a kaydet"""
        logger.info(f"MLFLOW_CLIENT: data_file_name = {data_file_name}")
        data_file_name_no_ext = os.path.splitext(data_file_name)[0] if data_file_name else "unknown_data"
        experiment_name = f"{problem_type}_{data_file_name_no_ext}" if problem_type and data_file_name_no_ext else (self.config.experiment_name or "default")
        client = MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=run_name) as run:
            try:
                # Temporary file'a model'i kaydet
                with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
                    tmp_file.write(model_data)
                    tmp_model_path = tmp_file.name
                # Model'i yükle
                model = joblib.load(tmp_model_path)
                # Model parametrelerini log et
                if hasattr(model, 'get_params'):
                    params = model.get_params()
                    for key, value in params.items():
                        if value is not None:
                            mlflow.log_param(key, value)
                # Model tipini ve ismini log et
                mlflow.log_param("model_type", model_type)
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("problem_type", problem_type)
                # Evaluation metrikleri log et
                if "evaluation_metrics" in metrics:
                    eval_metrics = metrics["evaluation_metrics"]
                    mlflow.log_metric("accuracy", eval_metrics.get("accuracy", 0))
                    mlflow.log_metric("precision", eval_metrics.get("precision", 0))
                    mlflow.log_metric("recall", eval_metrics.get("recall", 0))
                    mlflow.log_metric("f1_score", eval_metrics.get("f1_score", 0))
                    if eval_metrics.get("roc_auc"):
                        mlflow.log_metric("roc_auc", eval_metrics["roc_auc"])
                # Training info log et (varsa)
                if "training_info" in metrics:
                    training_info = metrics["training_info"]
                    if "model_params" in training_info:
                        for key, value in training_info["model_params"].items():
                            if value is not None and key not in ["random_state"]:
                                mlflow.log_param(f"train_{key}", value)
                # Config bilgilerini log et
                if "config" in metrics:
                    config_info = metrics["config"]
                    for key, value in config_info.items():
                        mlflow.log_param(f"config_{key}", value)
                # Model'i MLflow'a kaydet
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=self.config.artifact_path,
                    registered_model_name=model_name
                )
                # Confusion matrix'i artifact olarak kaydet
                if "evaluation_metrics" in metrics and "confusion_matrix" in metrics["evaluation_metrics"]:
                    import json
                    cm_data = {
                        "confusion_matrix": metrics["evaluation_metrics"]["confusion_matrix"]
                    }
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_cm:
                        json.dump(cm_data, tmp_cm)
                        tmp_cm_path = tmp_cm.name
                    mlflow.log_artifact(tmp_cm_path, "evaluation")
                    os.unlink(tmp_cm_path)
                # Temporary model file'ı temizle
                os.unlink(tmp_model_path)
                run_id = run.info.run_id
                logger.info(f"Model ve metrikler MLflow'a kaydedildi. Run ID: {run_id}")
                return run_id
            except Exception as e:
                logger.error(f"MLflow kayıt hatası: {e}")
                raise
    
    def _get_or_create_experiment(self, experiment_name):
        if not experiment_name:
            experiment_name = "default"
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            try:
                experiment_id = client.create_experiment(experiment_name)
                experiment = client.get_experiment(experiment_id)
            except Exception as e:
                if "RESOURCE_ALREADY_EXISTS" in str(e) or "UNIQUE constraint failed" in str(e):
                    experiment = client.get_experiment_by_name(experiment_name)
                else:
                    raise
        return experiment
    
    