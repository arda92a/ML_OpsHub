import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.decomposition import PCA
from typing import Tuple, Dict, Any, List, Optional, Union
from utils.logger import logger
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self, config: Dict[str, Any] = None):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.one_hot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.imputers = {}
        self.feature_selector = None
        self.pca = None
        self.feature_names = None
        self.target_encoder = None
        self.preprocessing_steps = []
        self.config = config or {}
        self.scaling_method = self.config.get('scaling_method', 'standard')
        self.imputation_method = self.config.get('imputation_method', 'median')
        self.encoding_method = self.config.get('encoding_method', 'auto')
        self.feature_selection = self.config.get('feature_selection', False)
        self.n_features = self.config.get('n_features', 'auto')
        self.pca_components = self.config.get('pca_components', None)
        self.handle_outliers = self.config.get('handle_outliers', False)
        self.outlier_method = self.config.get('outlier_method', 'iqr')
    
    def auto_detect_target_column(self, df: pd.DataFrame) -> Optional[str]:
        potential_targets = []
        for col in df.columns:
            unique_count = df[col].nunique()
            if unique_count == 2:
                potential_targets.append((col, 'binary', unique_count))
            elif 2 < unique_count <= 20:
                potential_targets.append((col, 'multiclass', unique_count))
            elif unique_count > 20 and df[col].dtype in [np.number]:
                potential_targets.append((col, 'regression', unique_count))
        if potential_targets:
            potential_targets.sort(key=lambda x: x[2])
            logger.info(f"Potansiyel target sütunlar: {potential_targets}")
            return potential_targets[0][0]
        return None

    def analyze_column_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        column_types = {
            'numeric': [],
            'categorical_low': [],
            'categorical_high': [],
            'datetime': [],
            'binary': [],
            'text': []
        }
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                column_types['datetime'].append(col)
            elif df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                if df[col].nunique() == 2:
                    column_types['binary'].append(col)
                else:
                    column_types['numeric'].append(col)
            elif df[col].dtype == 'object':
                unique_count = df[col].nunique()
                if unique_count == 2:
                    column_types['binary'].append(col)
                elif unique_count <= 10:
                    column_types['categorical_low'].append(col)
                elif unique_count <= 50:
                    column_types['categorical_high'].append(col)
                else:
                    column_types['text'].append(col)
            else:
                column_types['categorical_low'].append(col)
        return column_types

    def handle_missing_values(self, df: pd.DataFrame, column_types: Dict[str, List[str]]) -> pd.DataFrame:
        df_processed = df.copy()
        numeric_cols = column_types['numeric']
        if numeric_cols:
            if self.imputation_method == 'knn':
                imputer = KNNImputer(n_neighbors=5)
                df_processed[numeric_cols] = imputer.fit_transform(df_processed[numeric_cols])
                self.imputers['numeric'] = imputer
            else:
                strategy = self.imputation_method if self.imputation_method in ['mean', 'median'] else 'median'
                imputer = SimpleImputer(strategy=strategy)
                df_processed[numeric_cols] = imputer.fit_transform(df_processed[numeric_cols])
                self.imputers['numeric'] = imputer
        categorical_cols = column_types['categorical_low'] + column_types['categorical_high'] + column_types['binary']
        if categorical_cols:
            # bool dtype olanları stringe çevir
            for col in categorical_cols:
                if df_processed[col].dtype == bool:
                    df_processed[col] = df_processed[col].astype(str)
            imputer = SimpleImputer(strategy='most_frequent')
            df_processed[categorical_cols] = imputer.fit_transform(df_processed[categorical_cols])
            self.imputers['categorical'] = imputer
        self.preprocessing_steps.append("Missing values handled")
        return df_processed

    def process_outliers(self, df: pd.DataFrame, column_types: Dict[str, List[str]]) -> pd.DataFrame:
        if not self.handle_outliers:
            return df
        df_processed = df.copy()
        numeric_cols = column_types['numeric']
        for col in numeric_cols:
            if self.outlier_method == 'iqr':
                Q1 = df_processed[col].quantile(0.25)
                Q3 = df_processed[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_processed[col] = np.clip(df_processed[col], lower_bound, upper_bound)
            elif self.outlier_method == 'zscore':
                z_scores = np.abs((df_processed[col] - df_processed[col].mean()) / df_processed[col].std())
                df_processed[col] = np.where(z_scores > 3, df_processed[col].median(), df_processed[col])
        self.preprocessing_steps.append("Outliers handled")
        return df_processed

    def encode_categorical_variables(self, df: pd.DataFrame, column_types: Dict[str, List[str]]) -> pd.DataFrame:
        df_processed = df.copy()
        binary_cols = column_types['binary']
        for col in binary_cols:
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col].astype(str))
            self.label_encoders[col] = le
        categorical_low = column_types['categorical_low']
        if categorical_low:
            if self.encoding_method == 'onehot' or (self.encoding_method == 'auto' and len(categorical_low) <= 5):
                encoded_df = pd.get_dummies(df_processed[categorical_low], prefix=categorical_low)
                df_processed = df_processed.drop(columns=categorical_low)
                df_processed = pd.concat([df_processed, encoded_df], axis=1)
                self.preprocessing_steps.append("One-hot encoding applied")
            else:
                for col in categorical_low:
                    le = LabelEncoder()
                    df_processed[col] = le.fit_transform(df_processed[col].astype(str))
                    self.label_encoders[col] = le
                self.preprocessing_steps.append("Label encoding applied")
        categorical_high = column_types['categorical_high']
        for col in categorical_high:
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col].astype(str))
            self.label_encoders[col] = le
        text_cols = column_types['text']
        if text_cols:
            df_processed = df_processed.drop(columns=text_cols)
            logger.warning(f"Text sütunları kaldırıldı: {text_cols}")
        return df_processed

    def handle_datetime_features(self, df: pd.DataFrame, column_types: Dict[str, List[str]]) -> pd.DataFrame:
        df_processed = df.copy()
        datetime_cols = column_types['datetime']
        for col in datetime_cols:
            df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
            df_processed[f'{col}_year'] = df_processed[col].dt.year
            df_processed[f'{col}_month'] = df_processed[col].dt.month
            df_processed[f'{col}_day'] = df_processed[col].dt.day
            df_processed[f'{col}_dayofweek'] = df_processed[col].dt.dayofweek
            df_processed[f'{col}_hour'] = df_processed[col].dt.hour
            df_processed[f'{col}_is_weekend'] = df_processed[col].dt.dayofweek.isin([5, 6]).astype(int)
            df_processed = df_processed.drop(columns=[col])
        if datetime_cols:
            self.preprocessing_steps.append("Datetime features extracted")
        return df_processed

    def scale_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame, numeric_cols: list) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if not numeric_cols:
            return X_train, X_test
        if self.scaling_method == 'standard':
            scaler = StandardScaler()
        elif self.scaling_method == 'minmax':
            scaler = MinMaxScaler()
        elif self.scaling_method == 'robust':
            scaler = RobustScaler()
        else:
            scaler = StandardScaler()
        X_train_scaled = X_train.copy()
        X_test_scaled = X_test.copy()
        X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
        X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])
        self.scaler = scaler
        self.preprocessing_steps.append(f"Features scaled using {self.scaling_method}")
        return X_train_scaled, X_test_scaled

    def select_features(self, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, task_type: str) -> Tuple[np.ndarray, np.ndarray]:
        if not self.feature_selection:
            return X_train, X_test
        if self.n_features == 'auto':
            n_features = min(20, X_train.shape[1] // 2)
        else:
            n_features = min(self.n_features, X_train.shape[1])
        if task_type == 'regression':
            score_func = f_regression
        else:
            score_func = f_classif
        selector = SelectKBest(score_func=score_func, k=n_features)
        X_train_selected = selector.fit_transform(X_train, y_train)
        X_test_selected = selector.transform(X_test)
        self.feature_selector = selector
        self.preprocessing_steps.append(f"Feature selection applied: {n_features} features selected")
        return X_train_selected, X_test_selected

    def apply_pca(self, X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if self.pca_components is None:
            return X_train, X_test
        if isinstance(self.pca_components, float):
            n_components = self.pca_components
        else:
            n_components = min(self.pca_components, X_train.shape[1])
        pca = PCA(n_components=n_components)
        X_train_pca = pca.fit_transform(X_train)
        X_test_pca = pca.transform(X_test)
        self.pca = pca
        self.preprocessing_steps.append(f"PCA applied: {pca.n_components_} components")
        return X_train_pca, X_test_pca

    def detect_task_type(self, y: pd.Series) -> str:
        if y.dtype == 'object' or y.nunique() <= 20:
            return 'classification'
        else:
            return 'regression'

    def preprocess(self, df: pd.DataFrame, target_column: str = None, test_size: float = 0.2, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        logger.info("Dinamik veri ön işleme başlıyor...")
        if target_column is None:
            target_column = self.auto_detect_target_column(df)
            if target_column is None:
                raise ValueError("Target sütunu tespit edilemedi. Lütfen target_column parametresini belirtin.")
            logger.info(f"Otomatik tespit edilen target sütun: {target_column}")
        df_processed = df.copy()
        column_types = self.analyze_column_types(df_processed.drop(columns=[target_column]))
        logger.info(f"Sütun tipleri: {column_types}")
        X = df_processed.drop(columns=[target_column])
        y = df_processed[target_column]
        task_type = self.detect_task_type(y)
        logger.info(f"Task tipi: {task_type}")
        # --- SINIF DAĞILIMI KONTROLÜ ---
        if task_type == 'classification':
            class_counts = pd.Series(y).value_counts()
            if (class_counts < 2).any():
                # Sadece 1 örneğe sahip sınıfları otomatik olarak çıkar
                drop_classes = class_counts[class_counts < 2].index.tolist()
                logger.warning(f"Aşağıdaki sınıflar sadece 1 örneğe sahip ve veri setinden çıkarıldı: {drop_classes}")
                mask = ~y.isin(drop_classes)
                X = X[mask]
                y = y[mask]
                class_counts = pd.Series(y).value_counts()
                if (class_counts < 2).any():
                    raise ValueError(f"Her sınıfta en az 2 örnek olmalı. Sınıf dağılımı: {class_counts.to_dict()}")
        X = self.handle_datetime_features(X, column_types)
        column_types = self.analyze_column_types(X)
        X = self.handle_missing_values(X, column_types)
        X = self.process_outliers(X, column_types)
        # Train/test split öncesi ölçekleme için numeric sütunları belirle
        numeric_cols = column_types['numeric']
        # Train/test split
        if task_type == 'classification':
            self.target_encoder = LabelEncoder()
            y_encoded = self.target_encoder.fit_transform(y)
        else:
            y_encoded = y.values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y_encoded if task_type == 'classification' else None
        )
        # Sadece sayısal sütunlara scale uygula
        X_train_scaled, X_test_scaled = self.scale_features(X_train, X_test, numeric_cols)
        # Tüm train/test'e encoding uygula
        X_train_encoded = self.encode_categorical_variables(X_train_scaled, self.analyze_column_types(X_train_scaled))
        X_test_encoded = self.encode_categorical_variables(X_test_scaled, self.analyze_column_types(X_test_scaled))
        # Feature selection ve PCA
        X_train_selected, X_test_selected = self.select_features(X_train_encoded.values, y_train, X_test_encoded.values, task_type)
        X_train_final, X_test_final = self.apply_pca(X_train_selected, X_test_selected)
        self.feature_names = X_train_encoded.columns.tolist()
        logger.info(f"Veri işlendi - Train: {X_train_final.shape}, Test: {X_test_final.shape}")
        logger.info(f"Uygulanan preprocessing adımları: {self.preprocessing_steps}")
        return X_train_final, X_test_final, y_train, y_test

    def get_preprocessing_info(self) -> Dict[str, Any]:
        return {
            'preprocessing_steps': self.preprocessing_steps,
            'feature_names': self.feature_names,
            'scaling_method': self.scaling_method,
            'imputation_method': self.imputation_method,
            'encoding_method': self.encoding_method,
            'n_features_selected': self.feature_selector.k if self.feature_selector else None,
            'pca_components': self.pca.n_components_ if self.pca else None,
            'target_encoder': self.target_encoder is not None
        }
    
    