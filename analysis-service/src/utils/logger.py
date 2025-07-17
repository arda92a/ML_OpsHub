from loguru import logger
import sys
from config.config import Config

config = Config()
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.log_level
)
# Artık doğrudan 'from utils.logger import logger' ile kullanılabilir.