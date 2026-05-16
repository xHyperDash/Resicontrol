import sqlite3
from config import DB_PATH
from logger import logger


def get_connection():
    """Crea una conexion a la base de datos con configuracion optimizada."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(cursor: sqlite3.Cursor):
    """Crea todas las tablas si no existen."""
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario  TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            rol      TEXT    NOT NULL CHECK(rol IN ('admin','operador','residente'))
        );

        CREATE TABLE IF NOT EXISTS residentes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad    TEXT    NOT NULL,
            nombre    TEXT    NOT NULL,
            telefono  TEXT,
            email     TEXT,
            placa     TEXT    NOT NULL UNIQUE,
            qr_code   TEXT,
            activo    INTEGER NOT NULL DEFAULT 1,
            creado_en TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS parqueaderos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            numero   TEXT    NOT NULL UNIQUE,
            tipo     TEXT    NOT NULL CHECK(tipo IN ('residente','visitante')),
            estado   TEXT    NOT NULL DEFAULT 'libre' CHECK(estado IN ('libre','ocupado')),
            placa    TEXT,
            desde    TEXT
        );

        CREATE TABLE IF NOT EXISTS accesos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo         TEXT    NOT NULL CHECK(tipo IN ('residente','visitante')),
            nombre       TEXT,
            cedula       TEXT,
            placa        TEXT,
            invitado_por TEXT,
            entrada      TEXT    NOT NULL,
            salida       TEXT,
            operador     TEXT,
            parqueadero  TEXT
        );

        CREATE TABLE IF NOT EXISTS incidentes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT    NOT NULL,
            nivel       TEXT    NOT NULL DEFAULT 'bajo'
                        CHECK(nivel IN ('bajo','medio','alto')),
            operador    TEXT,
            fecha       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );
    """)


def create_indexes(cursor: sqlite3.Cursor):
    """Crea indices para optimizar consultas frecuentes."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_accesos_cedula    ON accesos(cedula)",
        "CREATE INDEX IF NOT EXISTS idx_accesos_placa     ON accesos(placa)",
        "CREATE INDEX IF NOT EXISTS idx_accesos_entrada   ON accesos(entrada)",
        "CREATE INDEX IF NOT EXISTS idx_accesos_salida    ON accesos(salida)",
        "CREATE INDEX IF NOT EXISTS idx_residentes_placa  ON residentes(placa)",
        "CREATE INDEX IF NOT EXISTS idx_parqueaderos_est  ON parqueaderos(estado)",
        "CREATE INDEX IF NOT EXISTS idx_incidentes_fecha  ON incidentes(fecha)",
    ]
    for sql in indexes:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass


def add_audit_columns(cursor: sqlite3.Cursor):
    """Agrega columnas de auditoria si no existen (migracion)."""
    try:
        cursor.execute("ALTER TABLE accesos ADD COLUMN modificado_por TEXT")
        logger.info("Columna 'modificado_por' agregada a accesos")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE accesos ADD COLUMN modificado_en TEXT")
        logger.info("Columna 'modificado_en' agregada a accesos")
    except sqlite3.OperationalError:
        pass


def seed_parqueaderos(cursor: sqlite3.Cursor):
    """Crea los parqueaderos si la tabla esta vacia."""
    cursor.execute("SELECT COUNT(*) FROM parqueaderos")
    if cursor.fetchone()[0] == 0:
        datos = []
        for i in range(1, 11):
            datos.append((f"R{i:02d}", "residente"))
        for i in range(1, 11):
            datos.append((f"V{i:02d}", "visitante"))
        cursor.executemany(
            "INSERT INTO parqueaderos (numero, tipo) VALUES (?,?)", datos
        )
        logger.info("Parqueaderos inicializados (10 residentes + 10 visitantes)")


def insert_default_users(cursor: sqlite3.Cursor, hash_fn):
    """Inserta admin y portero con contraseñas hasheadas si no existen."""
    defaults = [
        ("admin",   "admin123", "admin"),
        ("portero", "1234",     "operador"),
    ]
    for usuario, pwd, rol in defaults:
        try:
            cursor.execute(
                "INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,?)",
                (usuario, hash_fn(pwd), rol),
            )
            logger.info(f"Usuario por defecto creado: {usuario} ({rol})")
        except sqlite3.IntegrityError:
            pass


def migrar_contrasenas(cursor: sqlite3.Cursor, hash_fn):
    """
    Migra contraseñas SHA-256 legacy a bcrypt.
    Se llama al inicio de la aplicacion.
    """
    cursor.execute("SELECT id, usuario, password FROM usuarios")
    for row in cursor.fetchall():
        uid, user, old_hash = row["id"], row["usuario"], row["password"]
        if len(old_hash) == 64 and all(c in "0123456789abcdef" for c in old_hash.lower()):
            pass  # Se migrara al hacer login
    return 0