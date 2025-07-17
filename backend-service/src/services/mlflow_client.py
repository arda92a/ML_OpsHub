import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional, List
from config.config import MLflowConfig
from utils.logger import setup_logger

logger = setup_logger()

def handle_mlflow_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} hatası: {e}")
            return None
    return wrapper

class MLflowService:
    def __init__(self, config: MLflowConfig):
        self.config = config
        self.client = MlflowClient(tracking_uri=config.tracking_uri)
        mlflow.set_tracking_uri(config.tracking_uri)
        # Set experiment_id
        experiment = self._get_or_create_experiment(config.experiment_name)
        self.experiment_id = experiment if experiment else None

    def _get_or_create_experiment(self, experiment_name):
        if not experiment_name:
            experiment_name = "default"
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(experiment_name)
            experiment = client.get_experiment(experiment_id)
        return experiment

    @handle_mlflow_error
    def get_latest_model_version(self, model_name: str = None) -> Optional[Dict[str, Any]]:
        """Get the latest model version info."""
        model_name = model_name or self.config.registered_model_name
        versions = self.client.get_latest_versions(
            model_name, stages=["None", "Staging", "Production"]
        )
        if versions:
            latest_version = max(versions, key=lambda x: int(x.version))
            return {
                "name": latest_version.name,
                "version": latest_version.version,
                "stage": latest_version.current_stage,
                "run_id": latest_version.run_id,
                "created_timestamp": latest_version.creation_timestamp
            }
        return None

    @handle_mlflow_error
    def get_run_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics, params, tags, and status for a run."""
        run = self.client.get_run(run_id)
        return {
            "metrics": run.data.metrics,
            "params": run.data.params,
            "tags": run.data.tags,
            "status": run.info.status,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time
        }

    @handle_mlflow_error
    def compare_models(self, run_ids: List[str]) -> Dict[str, Any]:
        """Birden fazla modeli run_id'leri üzerinden karşılaştırır."""
        comparison_data = {}
        for run_id in run_ids:
            run_data = self.get_run_metrics(run_id)
            if run_data:
                comparison_data[run_id] = {
                    "accuracy": run_data["metrics"].get("accuracy", 0),
                    "f1_score": run_data["metrics"].get("f1_score", 0),
                    "precision": run_data["metrics"].get("precision", 0),
                    "recall": run_data["metrics"].get("recall", 0),
                    "model_type": run_data["params"].get("model_type", "unknown")
                }
        if comparison_data:
            best_run = max(comparison_data.items(), key=lambda x: x[1]["accuracy"])
            comparison_data["best_model"] = {
                "run_id": best_run[0],
                "metrics": best_run[1]
            }
        return comparison_data

    @handle_mlflow_error
    def get_experiment_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Deneye ait son çalıştırmaları (run) listeler."""
        if not self.experiment_id:
            return []
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            order_by=["start_time DESC"],
            max_results=limit
        )
        return [
            {
                "run_id": run.info.run_id,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "status": run.info.status,
                "metrics": run.data.metrics,
                "params": run.data.params
            }
            for run in runs
        ]

    @handle_mlflow_error
    def list_models_by_type(self) -> Dict[str, List[str]]:
        """Kayıtlı modelleri problem_type (classification/regression/diğer) göre listeler."""
        registered_models = list(self.client.search_registered_models())
        result = {"classification": [], "regression": [], "other": []}
        for model in registered_models:
            problem_type = "other"
            if model.latest_versions:
                run_id = model.latest_versions[0].run_id
                run = self.client.get_run(run_id)
                problem_type = run.data.params.get("problem_type", "other")
            result.setdefault(problem_type, result["other"]).append(model.name)
        return result

    @handle_mlflow_error
    def get_model_versions(self, model_name: str) -> Dict[str, Any]:
        """Bir modele ait tüm sürümleri ve meta verilerini getirir."""
        model = self.client.get_registered_model(model_name)
        versions = self.client.search_model_versions(f"name='{model_name}'")
        version_list = []
        problem_type = None
        algorithm_type = None
        for v in versions:
            run = self.client.get_run(v.run_id)
            v_problem_type = run.data.params.get("problem_type", None)
            v_algorithm_type = run.data.params.get("model_type", None)
            if not problem_type and v_problem_type:
                problem_type = v_problem_type
            if not algorithm_type and v_algorithm_type:
                algorithm_type = v_algorithm_type
            artifact_exists = self._artifact_exists(v.run_id)
            version_list.append({
                "version": v.version,
                "stage": v.current_stage,
                "run_id": v.run_id,
                "created_timestamp": v.creation_timestamp,
                "artifact_exists": artifact_exists
            })
        return {
            "model_name": model_name,
            "problem_type": problem_type,
            "algorithm_type": algorithm_type,
            "versions": version_list
        }

    @handle_mlflow_error
    def get_model_version(self, model_name: str, version: int) -> Optional[Dict[str, Any]]:
        """Bir modelin belirli bir sürümünü getirir."""
        mv = self.client.get_model_version(model_name, str(version))
        run = self.client.get_run(mv.run_id)
        problem_type = run.data.params.get("problem_type", "other")
        model_type = run.data.params.get("model_type", None)
        return {
            "model_name": model_name,
            "version": mv.version,
            "stage": mv.current_stage,
            "run_id": mv.run_id,
            "created_timestamp": mv.creation_timestamp,
            "problem_type": problem_type,
            "algorithm_type": model_type
        }

    def _artifact_exists(self, run_id: str, artifact_path: str = "models/MLmodel") -> bool:
        """Belirtilen artifact dosyasının mevcut olup olmadığını kontrol eder."""
        try:
            # Artifact'lar listelenmeye çalışılır; bulunamazsa hata fırlatılır
            artifacts = self.client.list_artifacts(run_id, path="models")
            return any(a.path == artifact_path for a in artifacts)
        except Exception:
            return False

    @handle_mlflow_error
    def download_model_artifact(self, run_id: str, artifact_path: str = "models/model.pkl") -> Optional[str]:
        """Belirtilen artifact dosyasını indirerek yerel dizine kaydeder."""
        try:
            local_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path)
            return local_path
        except Exception as e:
            logger.error(f"Artifact indirme hatası: {e}")
            return None 