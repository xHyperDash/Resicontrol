"""
Módulo de gestión de códigos QR para ResiControl.
- Generación de QR para residentes
- Escaneo de QR desde cámara
- Gestión de archivos QR en disco
"""

import os
import sys
import sqlite3
import glob
from config import QR_DIR, DB_PATH
from logger import logger


# ─── Rutas ────────────────────────────────────────────────────────────────────

def get_qr_path(placa: str) -> str:
    """Retorna la ruta absoluta del archivo QR para una placa dada."""
    nombre_archivo = f"qr_{placa.upper().replace(' ', '_')}.png"
    return os.path.join(QR_DIR, nombre_archivo)


# ─── Generación ───────────────────────────────────────────────────────────────

def generar_qr(placa: str) -> tuple[bool, str]:
    """
    Genera un código QR para una placa de vehículo.
    Guarda la imagen en qrs/ y actualiza la ruta en la BD.
    Retorna (éxito, mensaje_o_ruta).
    """
    try:
        import qrcode

        placa_upper = placa.strip().upper()
        if not placa_upper:
            return False, "Placa no proporcionada"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(placa_upper)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        ruta = get_qr_path(placa_upper)
        img.save(ruta)

        # Actualizar ruta en BD
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE residentes SET qr_code=? WHERE placa=?", (ruta, placa_upper))
        conn.commit()
        conn.close()

        logger.info(f"QR generado para placa {placa_upper} → {ruta}")
        return True, ruta

    except ImportError:
        msg = "Librería qrcode no instalada"
        logger.warning(msg)
        return False, msg
    except Exception as e:
        logger.error(f"Error generando QR para {placa}: {e}")
        return False, str(e)


# ─── Escaneo ──────────────────────────────────────────────────────────────────

def escanear_qr(frame) -> str | None:
    """
    Decodifica un frame de video y retorna la placa si se detecta un QR.
    Retorna la placa (str) o None si no se detecta nada.
    """
    try:
        import cv2
        import pyzbar.pyzbar as pyzbar

        decoded_objects = pyzbar.decode(frame)
        if decoded_objects:
            data: str = decoded_objects[0].data.decode("utf-8").strip().upper()
            logger.info(f"QR escaneado: placa={data}")
            return data
    except ImportError:
        logger.warning("Librerías de cámara no disponibles (cv2/pyzbar)")
    except Exception as e:
        logger.error(f"Error escaneando frame: {e}")
    return None


def buscar_residente_por_placa(placa: str, cursor: sqlite3.Cursor) -> dict | None:
    """Busca un residente activo por placa. Retorna dict o None."""
    cursor.execute(
        "SELECT id, unidad, nombre, telefono, email, placa FROM residentes WHERE placa=? AND activo=1",
        (placa.upper(),)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def abrir_archivo(ruta: str):
    """Abre un archivo con la aplicación predeterminada del sistema."""
    if not os.path.exists(ruta):
        return
    try:
        if sys.platform == "win32":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            os.system(f'open "{ruta}"')
        else:
            os.system(f'xdg-open "{ruta}"')
    except Exception as e:
        logger.error(f"Error abriendo archivo {ruta}: {e}")


def listar_qrs() -> list:
    """Retorna la lista de archivos QR en el directorio."""
    return sorted(glob.glob(os.path.join(QR_DIR, "qr_*.png")))