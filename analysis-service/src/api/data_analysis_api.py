from fastapi import APIRouter, UploadFile, File, Form
from data.loader import DataLoader
from data.preprocessor import DataPreprocessor
import tempfile
import pandas as pd
from fastapi.responses import JSONResponse
import os
import json
from utils.logger import logger

router = APIRouter()

@router.post("/analyze")
async def analyze_data(file: UploadFile = File(...)):
    """
    Yüklenen veri dosyasını analiz eder ve önişleme önerileri sunar.
    """
    try:
        # Dosyayı geçici olarak kaydet
        suffix = '.' + file.filename.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        # DataLoader ile yükle
        loader = DataLoader(tmp_path)
        df = loader.load_data()
        if df is None:
            return JSONResponse(status_code=400, content={"error": "Veri yüklenemedi"})
        # Analiz ve öneriler
        analysis = loader.analyze_data_structure(df)
        suggestions = loader.suggest_preprocessing_steps(df)
        # Geçici dosyayı sil
        os.unlink(tmp_path)
        return {
            "data_analysis": analysis,
            "preprocessing_suggestions": suggestions
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/preprocess")
async def preprocess_data(
    file: UploadFile = File(...),
    config: str = Form(None),
    target_column: str = Form(None)
):
    """
    Yüklenen veri dosyasını ve önişleme ayarlarını alır, önişleme uygular ve sonucu döner.
    """
    try:
        suffix = '.' + file.filename.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        df = pd.read_csv(tmp_path)
        config_dict = json.loads(config) if config else {}
        preprocessor = DataPreprocessor(config=config_dict)
        # Target sütunu kullanıcıdan alınabilir veya otomatik tespit edilir
        X_train, X_test, y_train, y_test = preprocessor.preprocess(df, target_column=target_column)
        info = preprocessor.get_preprocessing_info()
        # Sonuçları DataFrame olarak birleştir (örnek: sadece train setini dönebiliriz)
        processed_df = pd.DataFrame(X_train, columns=info['feature_names'][:X_train.shape[1]])
        # Sonuçları JSON olarak döndür
        os.unlink(tmp_path)
        return {
            "preprocessing_info": info,
            "processed_data": processed_df.to_dict(orient="records"),  # TÜM SATIRLAR
            "y_train": y_train.tolist()
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)}) 