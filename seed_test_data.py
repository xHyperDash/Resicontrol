"""
Seed script: populates sample data for development/demo.
Run: python seed_test_data.py
Idempotent — safe to run multiple times (skips existing records).
"""
import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH
from models import crear_residente, registrar_incidente
from logger import logger

NOW = datetime.now()
TODAY = NOW.strftime("%Y-%m-%d")


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _exists(table, column, value):
    conn = _conn()
    row = conn.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (value,)).fetchone()
    conn.close()
    return row is not None


def seed_residentes():
    datos = [
        ("301", "Maria Lopez",      "123456789", "3001112233", "maria@mail.com",   "XYZ789"),
        ("302", "Carlos Perez",     "987654321", "3002223344", "carlos@mail.com",  "ABC123"),
        ("303", "Ana Martinez",     "456789123", "3003334455", "ana@mail.com",     "DEF456"),
        ("101", "Pedro Ramirez",    "789123456", "3004445566", "pedro@mail.com",   "GHI789"),
        ("102", "Lucia Gomez",      "321654987", "3005556677", "lucia@mail.com",   "JKL012"),
        ("201", "Sofia Hernandez",  "654321789", "3006667788", "sofia@mail.com",   "MNO345"),
        ("202", "Diego Torres",     "147258369", "3007778899", "diego@mail.com",   "PQR678"),
        ("103", "Valentina Ortiz",  "369258147", "3008889900", "vale@mail.com",    "STU901"),
    ]
    created = 0
    for unidad, nombre, cedula, tel, email, placa in datos:
        if _exists("residentes", "placa", placa):
            continue
        ok, msg = crear_residente(unidad, nombre, cedula, tel, email, placa)
        if ok:
            created += 1
    if created:
        logger.info(f"Seed: {created} residentes creados")
    else:
        logger.info("Seed: residentes ya existen")


def seed_accesos():
    conn = _conn()
    existing = conn.execute("SELECT COUNT(*) FROM accesos").fetchone()[0]
    if existing > 0:
        conn.close()
        logger.info("Seed: accesos ya existen")
        return

    def ts(days=0, hours=0):
        dt = NOW - timedelta(days=days, hours=hours)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    registros = [
        ("residente", "Maria Lopez",     "123456789", "XYZ789", "301", ts(hours=2),                ts(hours=0.5)),
        ("residente", "Carlos Perez",    "987654321", "ABC123", "302", ts(hours=4),                ts(hours=1)),
        ("residente", "Ana Martinez",    "456789123", "DEF456", "303", ts(days=1, hours=3),        ts(days=1, hours=1)),
        ("residente", "Pedro Ramirez",   "789123456", "GHI789", "101", ts(days=2, hours=5),        ts(days=2, hours=0.5)),
        ("residente", "Sofia Hernandez", "654321789", "MNO345", "201", ts(hours=1),                None),
        ("visitante", "Jose Garcia",     "111222333", "LMN456", "301", ts(hours=3),                ts(hours=1.5)),
        ("visitante", "Laura Rojas",     "444555666", "OPQ789", "302", ts(hours=6),                ts(hours=2)),
        ("visitante", "Andres Castro",   "777888999", "RST012", "303", ts(days=1),                 ts(days=1, hours=2)),
        ("visitante", "Carmen Diaz",     "222333444", "UVW345", "101", ts(hours=0.5),              None),
        ("visitante", "Fernando Ruiz",   "555666777", "XYZ890", "102", ts(hours=7),                ts(hours=4)),
    ]

    for tipo, nombre, cedula, placa, unidad, entrada, salida in registros:
        conn.execute(
            "INSERT INTO accesos (tipo, nombre, cedula, placa, invitado_por, entrada, salida, operador) VALUES (?,?,?,?,?,?,?,?)",
            (tipo, nombre, cedula, placa, unidad, entrada, salida, "admin"),
        )
    conn.commit()
    conn.close()
    logger.info(f"Seed: {len(registros)} accesos creados")


def seed_incidentes():
    conn = _conn()
    existing = conn.execute("SELECT COUNT(*) FROM incidentes").fetchone()[0]
    if existing > 0:
        conn.close()
        logger.info("Seed: incidentes ya existen")
        return

    items = [
        ("Ruido excesivo en unidad 301 después de las 11 PM", "bajo"),
        ("Vehículo mal estacionado en zona de visitantes",    "bajo"),
        ("Discusión en el área de piscina",                   "medio"),
        ("Intento de ingreso sin identificación",             "medio"),
        ("Daño en cámara de seguridad del parqueadero",       "alto"),
    ]
    for desc, nivel in items:
        registrar_incidente(desc, nivel, "admin")
    logger.info(f"Seed: {len(items)} incidentes creados")


def seed_parqueo():
    conn = _conn()
    existing = conn.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='ocupado'").fetchone()[0]
    if existing > 0:
        conn.close()
        logger.info("Seed: parqueaderos ya asignados")
        return
    libre = conn.execute("SELECT numero FROM parqueaderos WHERE placa IS NULL AND tipo='visitante' LIMIT 3").fetchall()
    if len(libre) < 3:
        conn.close()
        return
    for i, placa in enumerate(["LMN456", "OPQ789", "RST012"]):
        num = libre[i]["numero"]
        conn.execute("UPDATE parqueaderos SET estado='ocupado', placa=?, desde=? WHERE numero=?",
                     (placa, NOW.strftime("%Y-%m-%d %H:%M:%S"), num))
    conn.commit()
    conn.close()
    logger.info("Seed: 3 parqueaderos asignados")


def main():
    import sys
    if "--help" in sys.argv:
        print("Seed test data for ResiControl")
        print("Usage: python seed_test_data.py")
        print("Idempotent — safe to run multiple times.")
        return

    seed_residentes()
    seed_accesos()
    seed_incidentes()
    seed_parqueo()
    logger.info("Seed completado. Datos de prueba listos.")


if __name__ == "__main__":
    main()
