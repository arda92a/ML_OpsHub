import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from utils.logger import logger
import os
from pathlib import Path

class DataLoader:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.supported_formats = {
            '.csv': self._load_csv,
            '.json': self._load_json,
            '.xlsx': self._load_excel,
            '.xls': self._load_excel,
            '.txt': self._load_txt
        }
    
    def load_data(self, filename: str = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        Dosya uzantısına göre otomatik veri yükleme
        """
        try:
            # Eğer self.data_path bir dosya ise doğrudan onu kullan
            if os.path.isfile(self.data_path):
                file_path = self.data_path
            else:
                if filename is None:
                    logger.error("Klasör yolu verildi ancak dosya adı belirtilmedi.")
                    return None
                file_path = os.path.join(self.data_path, filename)
            if not os.path.exists(file_path):
                logger.error(f"Dosya bulunamadı: {file_path}")
                return None
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Desteklenmeyen dosya formatı: {file_ext}")
                return None
            df = self.supported_formats[file_ext](file_path, **kwargs)
            if df is not None:
                logger.info(f"Veri yüklendi: {df.shape} boyutunda")
                logger.info(f"Sütunlar: {list(df.columns)}")
                logger.info(f"Veri tipleri: {df.dtypes.to_dict()}")
                logger.info(f"Eksik değerler: {df.isnull().sum().to_dict()}")
            return df
        except Exception as e:
            logger.error(f"Veri yükleme hatası: {e}")
            return None
    
    def _load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """CSV dosyası yükleme"""
        default_params = {
            'encoding': 'utf-8',
            'sep': ',',
            'na_values': ['', ' ', 'null', 'NULL', 'nan', 'NaN', 'NA', 'n/a', 'N/A']
        }
        default_params.update(kwargs)
        
        # Encoding problemlerini çözme
        try:
            return pd.read_csv(file_path, **default_params)
        except UnicodeDecodeError:
            logger.warning("UTF-8 encoding başarısız, latin-1 deneniyor...")
            default_params['encoding'] = 'latin-1'
            return pd.read_csv(file_path, **default_params)
    
    def _load_json(self, file_path: str, **kwargs) -> pd.DataFrame:
        """JSON dosyası yükleme"""
        default_params = {'orient': 'records'}
        default_params.update(kwargs)
        return pd.read_json(file_path, **default_params)
    
    def _load_excel(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Excel dosyası yükleme"""
        default_params = {'sheet_name': 0}
        default_params.update(kwargs)
        return pd.read_excel(file_path, **default_params)

    def _load_txt(self, file_path: str, **kwargs) -> pd.DataFrame:
        """TXT dosyası yükleme (delimiter otomatik algılama)"""
        # Delimiter otomatik algılama
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        # Olası delimiter'ları kontrol et
        delimiters = [',', '\t', ';', '|', ' ']
        delimiter_counts = {d: first_line.count(d) for d in delimiters}
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        
        default_params = {'sep': best_delimiter}
        default_params.update(kwargs)
        return self._load_csv(file_path, **default_params)
    
    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Veri yapısını analiz et
        """
        analysis = {
            'shape': tuple(int(x) for x in df.shape),
            'columns': list(df.columns),
            'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_values': {col: int(df[col].isnull().sum()) for col in df.columns},
            'missing_percentage': {col: float((df[col].isnull().sum() / len(df) * 100)) for col in df.columns},
            'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(df.select_dtypes(include=['object', 'category']).columns),
            'datetime_columns': list(df.select_dtypes(include=['datetime64']).columns),
            'unique_values': {col: int(df[col].nunique()) for col in df.columns},
            'memory_usage': int(df.memory_usage(deep=True).sum()),
            'duplicated_rows': int(df.duplicated().sum())
        }
        
        # Potansiyel target sütunlarını tespit et
        potential_targets = []
        for col in df.columns:
            unique_count = int(df[col].nunique())
            # Binary veya az sayıda unique değere sahip sütunlar
            if 2 <= unique_count <= 10:
                potential_targets.append({
                    'column': col,
                    'unique_count': unique_count,
                    'unique_values': [str(val) for val in df[col].unique()]
                })
        
        analysis['potential_target_columns'] = potential_targets
        
        return analysis
    
    def suggest_preprocessing_steps(self, df: pd.DataFrame) -> List[str]:
        """
        Veri analizine göre önişleme adımları öner
        """
        suggestions = []
        
        # Eksik değer kontrolü
        missing_percent = df.isnull().sum() / len(df) * 100
        high_missing_cols = missing_percent[missing_percent > 50].index.tolist()
        
        if len(high_missing_cols) > 0:
            suggestions.append(f"Yüksek eksik değerli sütunları kaldırın: {high_missing_cols}")
        
        # Kategorik değişken kontrolü
        categorical_cols = df.select_dtypes(include=['object']).columns
        high_cardinality_cols = [col for col in categorical_cols if df[col].nunique() > 50]
        
        if len(high_cardinality_cols) > 0:
            suggestions.append(f"Yüksek kardinaliteli kategorik sütunları işleyin: {high_cardinality_cols}")
        
        # Sayısal değişken kontrolü
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            suggestions.append("Sayısal sütunları standartlaştırın")
        
        # Duplicate kontrolü
        if df.duplicated().sum() > 0:
            suggestions.append(f"Duplicate satırları kaldırın: {df.duplicated().sum()} adet")
        
        # Outlier kontrolü
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > len(df) * 0.05:  # %5'ten fazla outlier varsa
                suggestions.append(f"'{col}' sütununda outlier kontrolü yapın")
        
        return suggestions
    
    
  