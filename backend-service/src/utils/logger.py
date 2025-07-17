import logging
import sys
import os
from datetime import datetime

def setup_logger(name: str = "ml-service", level: str = None):
    """Logger kurulumu"""
    
    # Log level'i belirle
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Logger'ı oluştur
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Eğer handler zaten varsa, tekrar ekleme
    if logger.handlers:
        return logger
    
    # Formatter oluştur
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    log_dir = os.getenv("LOG_DIR", "/tmp/logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger 