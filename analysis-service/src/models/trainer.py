from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor, ExtraTreesClassifier, ExtraTreesRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

import numpy as np
from typing import Dict, Any, Tuple
from utils.logger import logger
import joblib
import os

class ModelTrainer:
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.feature_importance_ = None
    
    def create_model(self) -> object:
        """Seçilen model tipine göre model oluştur"""
        # --- Classification Modelleri ---
        if self.model_type == "random_forest":
            return RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42, n_jobs=-1)
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
        elif self.model_type == "logistic_regression":
            return LogisticRegression(random_state=42, max_iter=1000, C=1.0, solver='liblinear')
        elif self.model_type == "svm":
            return SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42)
        elif self.model_type == "knn":
            return KNeighborsClassifier(n_neighbors=5, weights='distance')
        elif self.model_type == "decision_tree":
            return DecisionTreeClassifier(max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42)
        elif self.model_type == "xgboost" and XGBOOST_AVAILABLE:
            return xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, eval_metric='logloss')
        elif self.model_type == "lightgbm" and LIGHTGBM_AVAILABLE:
            return lgb.LGBMClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, verbose=-1)
        elif self.model_type == "extra_trees":
            return ExtraTreesClassifier(n_estimators=100, max_depth=10, random_state=42)
        # --- Regression Modelleri ---
        elif self.model_type == "linear_regression":
            return LinearRegression()
        elif self.model_type == "ridge":
            return Ridge(alpha=1.0, random_state=42)
        elif self.model_type == "lasso":
            return Lasso(alpha=0.1, random_state=42)
        elif self.model_type == "elasticnet":
            return ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
        elif self.model_type == "random_forest_regressor":
            return RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42, n_jobs=-1)
        elif self.model_type == "gradient_boosting_regressor":
            return GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
        elif self.model_type == "svr":
            return SVR(kernel='rbf', C=1.0, gamma='scale')
        elif self.model_type == "knn_regressor":
            return KNeighborsRegressor(n_neighbors=5, weights='distance')
        elif self.model_type == "decision_tree_regressor":
            return DecisionTreeRegressor(max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42)
        elif self.model_type == "xgboost_regressor" and XGBOOST_AVAILABLE:
            return xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, eval_metric='rmse')
        elif self.model_type == "lightgbm_regressor" and LIGHTGBM_AVAILABLE:
            return lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, verbose=-1)
        elif self.model_type == "extra_trees_regressor":
            return ExtraTreesRegressor(n_estimators=100, max_depth=10, random_state=42)
        else:
            raise ValueError(f"Desteklenmeyen model tipi: {self.model_type}")
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              **kwargs) -> Dict[str, Any]:
        """Modeli eğit"""
        logger.info(f"{self.model_type} modeli eğitiliyor...")
        
        self.model = self.create_model()
        
        # Model eğitimi
        if self.model_type in ["xgboost", "lightgbm"] and X_val is not None:
            # XGBoost ve LightGBM için validation set kullan
            if self.model_type == "xgboost":
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=10,
                    verbose=False
                )
            else:  # lightgbm
                self.model.fit(
                    X_train, y_train,
                    validation_sets=[(X_val, y_val)],
                    callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
                )
        else:
            # Diğer modeller için basit fit
            self.model.fit(X_train, y_train)
        
        # Feature importance'ı al (varsa)
        training_info = {}
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance_ = self.model.feature_importances_
            training_info['feature_importance'] = self.feature_importance_.tolist()
        
        # Model parametrelerini kaydet
        training_info['model_params'] = self.model.get_params()
        
        logger.info(f"{self.model_type} eğitimi tamamlandı")
        return training_info
    
    def save_model(self, filepath: str) -> bool:
        """Modeli kaydet"""
        try:
            joblib.dump(self.model, filepath)
            logger.info(f"Model kaydedildi: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Model kaydetme hatası: {e}")
            return False