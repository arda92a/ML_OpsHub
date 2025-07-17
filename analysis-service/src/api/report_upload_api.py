from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from src.storage.minio_client import MinIOClient
from config.config import MinIOConfig
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from io import BytesIO
from minio.error import S3Error
import zipfile
from pydantic import BaseModel
import unicodedata
import re as regex
from typing import List

def slugify(value: str) -> str:
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = regex.sub(r'[^a-zA-Z0-9_-]+', '_', value)
    value = value.strip('_').lower()
    return value

router = APIRouter()

# MinIO yapılandırması ve client başlatılıyor
minio_client = MinIOClient(config=MinIOConfig.from_env())

@router.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    report_name: str = Form(...),
    dataset_name: str = Form(...)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yükleyebilirsiniz.")

    try:
        data = await file.read()
        # Klasör yapısı: reports/{dataset_name}/{report_name}_vX.pdf (slugify)
        base_name = slugify(report_name)
        folder = f"reports/{slugify(dataset_name)}"
        uploaded_object_name = minio_client.upload_report_bytes(
            file_data=data,
            base_name=base_name,
            ext="pdf",
            folder=folder
        )
        return {"message": f"Rapor '{uploaded_object_name}' başarıyla yüklendi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beklenmeyen hata: {str(e)}")



class ReportRequest(BaseModel):
    version: int
    name: str
    dataset_name: str

@router.post("/download-report")
def download_report(request: ReportRequest):
    object_name = f"reports/{slugify(request.dataset_name)}/{slugify(request.name)}_v{request.version}.pdf"
    try:
        file_bytes = minio_client.download_report(object_name)  # PDF bytes
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{slugify(request.name)}_v{request.version}.pdf", file_bytes)
        zip_buffer.seek(0)
        zip_filename = f"{slugify(request.name)}_v{request.version}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Rapor bulunamadı: {str(e)}")


class DeleteReportRequest(BaseModel):
    name: str
    version: int
    dataset_name: str

@router.post("/delete-report")
def delete_report(request: DeleteReportRequest):
    object_name = f"reports/{slugify(request.dataset_name)}/{slugify(request.name)}_v{request.version}.pdf"
    try:
        minio_client.client.remove_object(minio_client.config.bucket_name, object_name)
        return {"message": f"Rapor '{object_name}' başarıyla silindi."}
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"Rapor bulunamadı veya silinirken hata oluştu: {str(e)}")

class MultiReportRequest(BaseModel):
    reports: List[dict]  # Her biri {name, version, dataset_name}

@router.post("/download-multi-reports")
def download_multi_reports(request: MultiReportRequest):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for rep in request.reports:
            object_name = f"reports/{slugify(rep['dataset_name'])}/{slugify(rep['name'])}_v{rep['version']}.pdf"
            try:
                file_bytes = minio_client.download_report(object_name)
                zip_file.writestr(f"{slugify(rep['name'])}_v{rep['version']}.pdf", file_bytes)
            except Exception:
                continue
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=dataset_reports.zip"}
    )

@router.get("/list-datasets")
def list_datasets():
    try:
        datasets = minio_client.list_datasets()
        return {"datasets": datasets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset listesi hatası: {str(e)}")

@router.get("/list-reports/{dataset_name}")
def list_reports(dataset_name: str):
    try:
        reports = minio_client.list_reports(dataset_name)
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor listesi hatası: {str(e)}")