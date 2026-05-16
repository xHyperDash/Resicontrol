"""
Generador de reportes PDF y CSV para ResiControl.
"""

import csv
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from config import DB_PATH
from models import obtener_historial
from logger import logger


def generar_pdf(fecha_ini: str, fecha_fin: str, tipo: str, usuario: str) -> tuple[bool, str]:
    """
    Genera un reporte PDF de accesos entre dos fechas.
    Retorna (éxito, mensaje_o_ruta).
    """
    try:
        filas = obtener_historial_between(fecha_ini, fecha_fin, tipo)

        nombre_pdf = f"reporte_{fecha_ini}_a_{fecha_fin}.pdf"
        doc = SimpleDocTemplate(
            nombre_pdf, pagesize=letter,
            leftMargin=36, rightMargin=36,
            topMargin=48, bottomMargin=36,
        )
        estilos = getSampleStyleSheet()
        elementos = []

        titulo = Paragraph(
            f"<b>ResiControl — Reporte de Accesos</b><br/>{fecha_ini} al {fecha_fin}",
            estilos["Title"],
        )
        elementos.append(titulo)
        elementos.append(Spacer(1, 16))
        elementos.append(
            Paragraph(
                f"Generado por: {usuario}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                estilos["Normal"],
            )
        )
        elementos.append(Spacer(1, 20))

        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador"]
        datos_tabla = [encabezados] + [
            [str(v) if v is not None else "—" for v in row] for row in filas
        ]

        tabla = Table(datos_tabla, repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elementos.append(tabla)
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph(f"Total de registros: {len(filas)}", estilos["Normal"]))

        doc.build(elementos)
        logger.info(f"PDF generado: {nombre_pdf} ({len(filas)} registros)")
        return True, nombre_pdf

    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return False, str(e)


def generar_csv(fecha_ini: str, fecha_fin: str, tipo: str) -> tuple[bool, str]:
    """
    Genera un archivo CSV de accesos entre dos fechas.
    Retorna (éxito, ruta).
    """
    try:
        filas = obtener_historial_between(fecha_ini, fecha_fin, tipo)

        nombre_csv = f"reporte_{fecha_ini}_a_{fecha_fin}.csv"
        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador"]

        with open(nombre_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(encabezados)
            for row in filas:
                writer.writerow([str(v) if v is not None else "" for v in row])

        logger.info(f"CSV generado: {nombre_csv} ({len(filas)} registros)")
        return True, nombre_csv

    except Exception as e:
        logger.error(f"Error generando CSV: {e}")
        return False, str(e)


def obtener_historial_between(fecha_ini: str, fecha_fin: str, tipo: str) -> list:
    """Obtiene historial filtrado por fechas y tipo."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT tipo, nombre, cedula, placa, entrada, salida, operador
        FROM accesos
        WHERE DATE(entrada) BETWEEN ? AND ?
    """
    params = [fecha_ini, fecha_fin]
    if tipo != "Todos":
        query += " AND tipo=?"
        params.append(tipo)
    query += " ORDER BY entrada DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]