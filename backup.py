"""
Backup Manager para ResiControl
- Backup automático diario a las 00:00
- Backup manual bajo demanda
- Retención configurable (por defecto 30 días)
"""

import os
import shutil
import glob
import sqlite3
import threading
import time
import schedule
from datetime import datetime
from config import DB_PATH, BACKUP_DIR, LOG_DIR
from logger import logger

MAX_BACKUPS = 30  # Retener los últimos 30 backups


def crear_backup() -> tuple[bool, str]:
    """Crea un backup de la base de datos. Retorna (éxito, mensaje)."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")

    try:
        # WAL mode permite copiar el archivo mientras la app está activa
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Backup creado exitosamente: {backup_path}")
        _limpiar_backups_antiguos()
        return True, f"Backup creado: backup_{timestamp}.db"
    except PermissionError:
        msg = "No se pudo crear backup: permiso denegado"
        logger.error(msg)
        return False, msg
    except Exception as e:
        msg = f"Error al crear backup: {e}"
        logger.error(msg)
        return False, msg


def restaurar_backup(backup_path: str) -> tuple[bool, str]:
    """Restaura la base de datos desde un archivo de backup."""
    try:
        if not os.path.exists(backup_path):
            return False, "Archivo de backup no encontrado"

        # Crear backup de seguridad antes de restaurar
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore = os.path.join(BACKUP_DIR, f"pre_restore_{ts}.db")
        shutil.copy2(DB_PATH, pre_restore)

        shutil.copy2(backup_path, DB_PATH)
        logger.info(f"Backup restaurado: {backup_path}")
        return True, "Restauración completada exitosamente"
    except Exception as e:
        logger.error(f"Error al restaurar backup: {e}")
        return False, f"Error: {e}"


def _limpiar_backups_antiguos():
    """Elimina backups que excedan el límite de retención."""
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")))
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        try:
            os.remove(oldest)
            logger.info(f"Backup eliminado (retención): {os.path.basename(oldest)}")
        except Exception as e:
            logger.error(f"Error eliminando backup {oldest}: {e}")


def get_backups_list() -> list:
    """Retorna lista de backups ordenados del más reciente al más antiguo."""
    backups = glob.glob(os.path.join(BACKUP_DIR, "backup_*.db"))
    return sorted(backups, reverse=True)


# ─── Scheduler (thread daemon) ────────────────────────────────────────────────

_scheduler_running = False


def _backup_scheduler_loop():
    """Loop interno que ejecuta schedule cada minuto."""
    global _scheduler_running
    schedule.every().day.at("00:00").do(_scheduled_backup)
    while _scheduler_running:
        schedule.run_pending()
        time.sleep(60)


def _scheduled_backup():
    """Callback ejecutado por el scheduler."""
    success, msg = crear_backup()
    if success:
        logger.info(f"Backup automático: {msg}")
    else:
        logger.error(f"Backup automático FALLÓ: {msg}")


def iniciar_scheduler():
    """Inicia el hilo daemon que ejecuta backups automáticos."""
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True
    thread = threading.Thread(target=_backup_scheduler_loop, daemon=True, name="BackupScheduler")
    thread.start()
    logger.info("Backup scheduler iniciado (backup diario a las 00:00)")


def detener_scheduler():
    """Detiene el scheduler de backups."""
    global _scheduler_running
    _scheduler_running = False
    schedule.clear()
    logger.info("Backup scheduler detenido")