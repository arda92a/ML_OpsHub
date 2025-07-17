from minio import Minio
from minio.error import S3Error
from io import BytesIO
from config.config import MinIOConfig
from src.utils.logger import logger

class MinIOClient:
    def __init__(self, config: MinIOConfig):
        self.config = config
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Bucket'ın var olduğundan emin ol, yoksa oluştur"""
        try:
            if not self.client.bucket_exists(self.config.bucket_name):
                self.client.make_bucket(self.config.bucket_name)
                logger.info(f"Bucket '{self.config.bucket_name}' oluşturuldu")
            else:
                logger.info(f"Bucket '{self.config.bucket_name}' zaten mevcut")
        except S3Error as e:
            logger.error(f"Bucket işlemi hatası: {e}")
            raise


    def upload_report_bytes(self, file_data: bytes, base_name: str, ext: str = "pdf", folder: str = "reports") -> str:
        """
        API'den gelen dosyayı bellekteyken yükler.
        Aynı isimde dosya varsa son versiyona 1 ekler.
        base_name örn: "rapor"
        ext örn: "pdf" ya da "txt"
        Dönüş: yüklenen dosyanın tam ismi, örn: "rapor_v3.pdf"
        """
        try:
            objects = self.client.list_objects(self.config.bucket_name, prefix=f"{folder}/")
            versions = []
            for obj in objects:
                name = obj.object_name  # örn: reports/dataset1/rapor_v1.pdf
                prefix = f"{folder}/{base_name}_v"
                suffix = f".{ext}"
                if name.startswith(prefix) and name.endswith(suffix):
                    v_str = name[len(prefix):-len(suffix)]
                    if v_str.isdigit():
                        versions.append(int(v_str))
            next_version = max(versions) + 1 if versions else 1
            object_name = f"{folder}/{base_name}_v{next_version}.{ext}"

            self.client.put_object(
                bucket_name=self.config.bucket_name,
                object_name=object_name,
                data=BytesIO(file_data),
                length=len(file_data),
                content_type=f"application/{ext}",
            )
            logger.info(f"Bellekten '{object_name}' başarıyla yüklendi")
            return object_name
        except S3Error as e:
            logger.error(f"Bellekten rapor yükleme hatası: {e}")
            raise


        
    def download_report(self, object_name: str) -> bytes:
        """
        MinIO'dan raporu byte olarak indir. object_name tam path olmalı (ör: reports/dataset/rapor_v1.pdf)
        """
        try:
            response = self.client.get_object(self.config.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Rapor '{object_name}' indirildi")
            return data
        except S3Error as e:
            logger.error(f"Rapor indirme hatası: {e}")
            raise

    def list_datasets(self) -> list:
        """
        reports/ altındaki tüm dataset klasörlerini listeler.
        """
        try:
            objects = self.client.list_objects(self.config.bucket_name, prefix="reports/", recursive=False)
            datasets = set()
            for obj in objects:
                parts = obj.object_name.split("/")
                if len(parts) > 1:
                    datasets.add(parts[1])
            return sorted(list(datasets))
        except S3Error as e:
            logger.error(f"Dataset listesi hatası: {e}")
            return []

    def list_reports(self, dataset_name: str) -> list:
        """
        Belirli bir dataset/proje altındaki tüm raporları ve versiyonlarını listeler.
        """
        try:
            prefix = f"reports/{dataset_name}/"
            objects = self.client.list_objects(self.config.bucket_name, prefix=prefix)
            reports = []
            for obj in objects:
                name = obj.object_name[len(prefix):]  # sadece dosya adı
                if name.endswith(".pdf"):
                    reports.append(name)
            return sorted(reports)
        except S3Error as e:
            logger.error(f"Rapor listesi hatası: {e}")
            return []
