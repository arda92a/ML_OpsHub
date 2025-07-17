import json
import os
import datetime
from pathlib import Path
from config.config import Config
from data.loader import DataLoader
from data.preprocessor import DataPreprocessor
from models.trainer import ModelTrainer
from models.evaluator import ModelEvaluator
from storage.minio_client import MinIOClient
from utils.logger import logger
import requests
import numpy as np

def send_model_to_mlflow(model_path, model_name, model_type, metrics, problem_type, data_file_name, artifact_paths=None):
    mlflow_url = os.getenv("MLFLOW_SERVICE_URL", "http://ml-service:8001/api/mlflow/submit-model")
    logger.info(f"MLflow servisine model gönderiliyor: {mlflow_url}")
    logger.info(f"MLFLOW_SEND: data_file_name = {data_file_name}")
    files = {
        "file": (os.path.basename(model_path), open(model_path, "rb"), "application/octet-stream")
    }
    data_file_name_no_ext = os.path.splitext(data_file_name)[0] if data_file_name else "unknown_data"
    payload = {
        "model_name": model_name,
        "model_type": model_type,
        "problem_type": problem_type,
        "data_file_name": data_file_name_no_ext,
        "metrics": json.dumps(metrics)
    }
    response = requests.post(mlflow_url, data=payload, files=files)
    if response.status_code == 200:
        logger.info(f"Model MLflow'a başarıyla yollandı: {response.json()}")
        return response.json()
    else:
        logger.error(f"MLflow'a model gönderme hatası: {response.text}")
        return None

def to_python_type(val):
    if isinstance(val, np.generic):
        return val.item()
    elif isinstance(val, np.ndarray):
        return val.tolist()
    return val

def train_model_pipeline(data_path=None, model_name=None, model_type=None, test_size=None, random_state=None, target_column=None, problem_type=None, data_file_name=None):
    logger.info("Analysis Service API üzerinden model eğitimi başlatılıyor...")
    config = Config()
    if data_path is not None:
        config.data_path = data_path
    if model_name is not None:
        config.model.model_name = model_name
    if test_size is not None:
        config.model.test_size = float(test_size)
    if random_state is not None:
        config.model.random_state = int(random_state)
    if target_column is None:
        target_column = 'Type'
    model_types = model_type if isinstance(model_type, list) else [model_type]
    results = []
    data_loader = DataLoader(config.data_path)
    logger.info("Veri yükleniyor...")
    df = data_loader.load_data()
    if df is None:
        raise Exception("Veri yüklenemedi")
    data_file_name_no_ext = data_file_name if data_file_name else os.path.basename(config.data_path) if config.data_path else "unknown_data"
    data_file_name_no_ext = os.path.splitext(data_file_name_no_ext)[0]
    import json as _json
    data_summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict()
    }
    data_summary_path = "/tmp/data_summary.json"
    with open(data_summary_path, "w", encoding="utf-8") as f:
        _json.dump(data_summary, f, ensure_ascii=False, indent=2)
    preprocessor = DataPreprocessor()
    logger.info("Veri ön işleniyor...")
    X_train, X_test, y_train, y_test = preprocessor.preprocess(
        df,
        target_column=target_column,
        test_size=config.model.test_size,
        random_state=config.model.random_state
    )
    # Model listelerini güncelle
    classification_models = [
        "random_forest", "gradient_boosting", "logistic_regression", "svm", "knn", "decision_tree",
        "xgboost", "lightgbm", "catboost", "extra_trees"
    ]
    regression_models = [
        "linear_regression", "ridge", "lasso", "elasticnet",
        "random_forest_regressor", "gradient_boosting_regressor", "svr", "knn_regressor", "decision_tree_regressor",
        "xgboost_regressor", "lightgbm_regressor", "catboost_regressor", "extra_trees_regressor"
    ]
    for mt in model_types:
        config.model.model_type = mt
        trainer = ModelTrainer(model_type=mt)
        evaluator = ModelEvaluator()
        minio_client = MinIOClient(config.minio)
        try:
            logger.info(f"Model eğitiliyor... ({mt})")
            training_info = trainer.train(
                X_train, y_train
            )
            logger.info("Model değerlendiriliyor...")
            metrics = evaluator.evaluate(trainer.model, X_test, y_test, trainer.model_type)
            metrics = {k: to_python_type(v) for k, v in metrics.items()}
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f"{config.model.model_name}_{mt}_{timestamp}.pkl"
            model_path = f"/tmp/{model_filename}"
            trainer.save_model(model_path)
            if problem_type:
                _problem_type = problem_type
            else:
                if mt in classification_models:
                    _problem_type = "classification"
                elif mt in regression_models:
                    _problem_type = "regression"
                else:
                    _problem_type = "other"
            mlflow_response = send_model_to_mlflow(model_path, config.model.model_name, mt, {
                "training_info": training_info,
                "evaluation_metrics": metrics
            }, problem_type=_problem_type, data_file_name=data_file_name_no_ext)
            result = {
                "model_type": mt,
                "model_filename": model_filename,
                "metrics": metrics,
                "mlflow_sent": mlflow_response is not None
            }
            if mlflow_response:
                result["model_version"] = mlflow_response.get("model_version")
                result["run_id"] = mlflow_response.get("run_id")
                result["mlflow_model_name"] = mlflow_response.get("model_name")
            if hasattr(preprocessor, 'target_encoder') and preprocessor.target_encoder is not None:
                result["class_labels"] = preprocessor.target_encoder.classes_.tolist()
            for k, v in result.items():
                if isinstance(v, dict):
                    result[k] = {ik: to_python_type(iv) for ik, iv in v.items()}
                elif isinstance(v, list):
                    result[k] = [to_python_type(iv) for iv in v]
                else:
                    result[k] = to_python_type(v)
            results.append(result)
            if mlflow_response:
                logger.info("Model başarıyla MLflow servisine gönderildi.")
            else:
                logger.error("Model MLflow servisine gönderilemedi.")
            logger.info("="*50)
            logger.info("ANALİZ SERVİSİ TAMAMLANDI")
            logger.info("="*50)
            logger.info(f"Model: {model_filename}")
            logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
            logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
            logger.info(f"Precision: {metrics['precision']:.4f}")
            logger.info(f"Recall: {metrics['recall']:.4f}")
            if metrics.get('roc_auc'):
                logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
            logger.info("="*50)
        except Exception as e:
            logger.error(f"Analysis Service hatası: {e}")
            results.append({"model_type": mt, "error": str(e)})
    return results 