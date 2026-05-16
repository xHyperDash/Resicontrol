import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE, LOG_DIR
import os


def setup_logger(name="ResiControl", level=logging.INFO):
    """Configura y retorna un logger con rotación de archivos."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicar handlers si se llama múltiples veces
    if logger.handlers:
        return logger

    # Handler de archivo con rotación (5 MB, 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Handler de consola (opcional, útil en desarrollo)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_format)
    logger.addHandler(console_handler)

    return logger


# Instancia global
logger = setup_logger()