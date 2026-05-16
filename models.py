"""
Models / Capa de datos para ResiControl
Encapsula todas las operaciones CRUD sobre la base de datos.

Todas las funciones aceptan un parametro opcional `conn`.
Si no se proporciona, crean una conexion propia. Esto facilita el testing.
"""

import sqlite3
from datetime import datetime
from config import DB_PATH
from logger import logger


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_conn(conn=None):
    """Si conn es None, crea una nueva. Retorna (conn, should_close)."""
    if conn is not None:
        return conn, False
    return _get_conn(), True


# ─── Usuarios ─────────────────────────────────────────────────────────────────

def crear_usuario(usuario, password_hash, rol, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        real_conn.execute(
            "INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)",
            (usuario, password_hash, rol),
        )
        real_conn.commit()
        logger.info(f"Usuario creado: {usuario} (rol={rol})")
        return True, f"Usuario '{usuario}' creado"
    except sqlite3.IntegrityError:
        logger.warning(f"Intento de crear usuario duplicado: {usuario}")
        return False, f"El usuario '{usuario}' ya existe"
    finally:
        if should_close:
            real_conn.close()


def verificar_usuario(usuario, password, verify_fn, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    row = real_conn.execute(
        "SELECT id, usuario, password, rol FROM usuarios WHERE usuario = ?",
        (usuario,),
    ).fetchone()
    if should_close:
        real_conn.close()
    if row and verify_fn(password, row["password"]):
        return {"id": row["id"], "usuario": row["usuario"], "rol": row["rol"]}
    return None


def obtener_usuarios(conn=None):
    real_conn, should_close = _ensure_conn(conn)
    rows = real_conn.execute("SELECT id, usuario, rol FROM usuarios ORDER BY usuario").fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


def obtener_usuario(uid, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    row = real_conn.execute("SELECT id, usuario, rol FROM usuarios WHERE id = ?", (uid,)).fetchone()
    if should_close:
        real_conn.close()
    return dict(row) if row else None


def eliminar_usuario(uid, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        real_conn.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
        real_conn.commit()
        logger.info(f"Usuario eliminado: id={uid}")
        return True
    except Exception as e:
        logger.error(f"Error eliminando usuario {uid}: {e}")
        return False
    finally:
        if should_close:
            real_conn.close()


# ─── Residentes ───────────────────────────────────────────────────────────────

def crear_residente(unidad, nombre, telefono, email, placa, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        real_conn.execute(
            "INSERT INTO residentes (unidad, nombre, telefono, email, placa) VALUES (?,?,?,?,?)",
            (unidad, nombre, telefono or None, email or None, placa.upper()),
        )
        real_conn.commit()
        logger.info(f"Residente creado: {nombre}")
        return True, "Residente registrado correctamente"
    except sqlite3.IntegrityError:
        return False, f"La placa {placa} ya esta registrada"
    finally:
        if should_close:
            real_conn.close()


def obtener_residentes(filtro="", conn=None):
    real_conn, should_close = _ensure_conn(conn)
    query = "SELECT id, unidad, nombre, telefono, email, placa, qr_code, activo FROM residentes WHERE activo=1"
    params = []
    if filtro:
        query += " AND (nombre LIKE ? OR unidad LIKE ? OR placa LIKE ?)"
        params = [f"%{filtro}%"] * 3
    query += " ORDER BY nombre"
    rows = real_conn.execute(query, params).fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


def obtener_residente(rid, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    row = real_conn.execute(
        "SELECT id, unidad, nombre, telefono, email, placa FROM residentes WHERE id = ?",
        (rid,),
    ).fetchone()
    if should_close:
        real_conn.close()
    return dict(row) if row else None


def editar_residente(rid, unidad, nombre, telefono, email, placa, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        real_conn.execute(
            "UPDATE residentes SET unidad=?, nombre=?, telefono=?, email=?, placa=? WHERE id=?",
            (unidad, nombre, telefono or None, email or None, placa.upper(), rid),
        )
        real_conn.commit()
        logger.info(f"Residente editado: id={rid}")
        return True, "Residente actualizado correctamente"
    except sqlite3.IntegrityError:
        return False, f"La placa {placa} ya esta registrada"
    finally:
        if should_close:
            real_conn.close()


def eliminar_residente(rid, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    real_conn.execute("UPDATE residentes SET activo=0 WHERE id=?", (rid,))
    real_conn.commit()
    logger.info(f"Residente eliminado (soft-delete): id={rid}")
    if should_close:
        real_conn.close()
    return True


# ─── Visitantes / Accesos ────────────────────────────────────────────────────

def registrar_entrada_visitante(nombre, cedula, placa, invitado_por, operador, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        existing = real_conn.execute(
            "SELECT id FROM accesos WHERE cedula=? AND salida IS NULL AND tipo='visitante'",
            (cedula,),
        ).fetchone()
        if existing:
            return False, "Este visitante ya tiene una entrada activa sin salida"

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        real_conn.execute(
            "INSERT INTO accesos (tipo, nombre, cedula, placa, invitado_por, entrada, operador) VALUES (?,?,?,?,?,?,?)",
            ("visitante", nombre, cedula, placa.upper() if placa else None, invitado_por, ahora, operador),
        )
        real_conn.commit()
        logger.info(f"Entrada visitante: {nombre}")
        return True, f"Entrada registrada para {nombre}"
    finally:
        if should_close:
            real_conn.close()


def registrar_salida_visitante(cedula, placa, operador, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if cedula:
            row = real_conn.execute(
                "SELECT id, placa FROM accesos WHERE cedula=? AND salida IS NULL AND tipo='visitante'",
                (cedula,),
            ).fetchone()
        elif placa:
            row = real_conn.execute(
                "SELECT id, placa FROM accesos WHERE placa=? AND salida IS NULL AND tipo='visitante'",
                (placa.upper(),),
            ).fetchone()
        else:
            return False, "Ingrese cedula o placa"

        if not row:
            return False, "No hay entrada activa para esta cedula/placa"

        real_conn.execute("UPDATE accesos SET salida=? WHERE id=?", (ahora, row["id"]))

        if row["placa"]:
            real_conn.execute(
                "UPDATE parqueaderos SET estado='libre', placa=NULL, desde=NULL WHERE placa=?",
                (row["placa"],),
            )

        real_conn.commit()
        logger.info(f"Salida visitante: cedula={cedula}, placa={placa}")
        return True, "Salida registrada correctamente"
    finally:
        if should_close:
            real_conn.close()


def registrar_entrada_residente(placa, operador, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        row = real_conn.execute(
            "SELECT nombre, unidad FROM residentes WHERE placa=? AND activo=1",
            (placa.upper(),),
        ).fetchone()

        if not row:
            return False, "Placa no encontrada en residentes activos"

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        real_conn.execute(
            "INSERT INTO accesos (tipo, nombre, cedula, placa, invitado_por, entrada, operador) VALUES (?,?,?,?,?,?,?)",
            ("residente", row["nombre"], None, placa.upper(), str(row["unidad"]), ahora, operador),
        )
        real_conn.commit()
        return True, f"Entrada registrada: {row['nombre']}"
    finally:
        if should_close:
            real_conn.close()


def obtener_visitantes_activos(conn=None):
    real_conn, should_close = _ensure_conn(conn)
    rows = real_conn.execute("""
        SELECT id, nombre, cedula, placa, invitado_por AS unidad, entrada, operador
        FROM accesos WHERE salida IS NULL AND tipo='visitante'
        ORDER BY entrada DESC LIMIT 30
    """).fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


def obtener_historial(busq="", tipo="Todos", conn=None):
    real_conn, should_close = _ensure_conn(conn)
    query = "SELECT id, tipo, nombre, cedula, placa, entrada, salida, operador FROM accesos WHERE 1=1"
    params = []
    if busq:
        query += " AND (nombre LIKE ? OR cedula LIKE ? OR placa LIKE ?)"
        params = [f"%{busq}%"] * 3
    if tipo != "Todos":
        query += " AND tipo=?"
        params.append(tipo)
    query += " ORDER BY entrada DESC LIMIT 200"
    rows = real_conn.execute(query, params).fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


def editar_acceso(ace_id, nombre, cedula, placa, modificado_por, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        real_conn.execute(
            "UPDATE accesos SET nombre=?, cedula=?, placa=?, modificado_por=?, modificado_en=? WHERE id=? AND salida IS NULL",
            (nombre, cedula, placa.upper() if placa else None, modificado_por, ahora, ace_id),
        )
        real_conn.commit()
        logger.info(f"Acceso editado: id={ace_id} por {modificado_por}")
        return True, "Registro actualizado"
    except Exception as e:
        logger.error(f"Error editando acceso {ace_id}: {e}")
        return False, str(e)
    finally:
        if should_close:
            real_conn.close()


# ─── Parqueaderos ─────────────────────────────────────────────────────────────

def obtener_parqueaderos_resumen(conn=None):
    real_conn, should_close = _ensure_conn(conn)
    libres_r = real_conn.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='libre' AND tipo='residente'").fetchone()[0]
    libres_v = real_conn.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='libre' AND tipo='visitante'").fetchone()[0]
    ocupados = real_conn.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='ocupado'").fetchone()[0]
    if should_close:
        real_conn.close()
    return {"libres_residente": libres_r, "libres_visitante": libres_v, "ocupados": ocupados}


def obtener_parqueaderos_por_tipo(tipo, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    rows = real_conn.execute("SELECT id, numero, estado, placa FROM parqueaderos WHERE tipo=? ORDER BY numero", (tipo,)).fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


def obtener_parqueaderos_libres_visitante(conn=None):
    real_conn, should_close = _ensure_conn(conn)
    rows = real_conn.execute("SELECT numero FROM parqueaderos WHERE tipo='visitante' AND estado='libre'").fetchall()
    if should_close:
        real_conn.close()
    return [r["numero"] for r in rows]


def asignar_parqueadero(numero, placa, operador, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    try:
        row = real_conn.execute("SELECT estado FROM parqueaderos WHERE numero=?", (numero,)).fetchone()
        if not row or row["estado"] == "ocupado":
            return False, "Ese parqueadero ya esta ocupado"

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        real_conn.execute(
            "UPDATE parqueaderos SET estado='ocupado', placa=?, desde=? WHERE numero=?",
            (placa.upper(), ahora, numero),
        )
        real_conn.execute(
            "INSERT INTO accesos (tipo, nombre, cedula, placa, invitado_por, entrada, operador, parqueadero) VALUES (?,?,?,?,?,?,?,?)",
            ("visitante", "Asignacion directa", None, placa.upper(), None, ahora, operador, numero),
        )
        real_conn.commit()
        logger.info(f"Parqueadero {numero} asignado a {placa}")
        return True, f"Parqueadero {numero} asignado a {placa}"
    except Exception as e:
        logger.error(f"Error asignando parqueadero {numero}: {e}")
        return False, str(e)
    finally:
        if should_close:
            real_conn.close()


def liberar_parqueadero(numero, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    real_conn.execute("UPDATE parqueaderos SET estado='libre', placa=NULL, desde=NULL WHERE numero=?", (numero,))
    real_conn.commit()
    logger.info(f"Parqueadero {numero} liberado")
    if should_close:
        real_conn.close()
    return True


# ─── Incidentes ───────────────────────────────────────────────────────────────

def registrar_incidente(descripcion, nivel, operador, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    real_conn.execute("INSERT INTO incidentes (descripcion, nivel, operador) VALUES (?,?,?)",
        (descripcion, nivel, operador))
    real_conn.commit()
    logger.info(f"Incidente registrado: nivel={nivel} por {operador}")
    if should_close:
        real_conn.close()
    return True


def obtener_incidentes(limite=30, conn=None):
    real_conn, should_close = _ensure_conn(conn)
    rows = real_conn.execute(
        "SELECT id, nivel, descripcion, operador, fecha FROM incidentes ORDER BY fecha DESC LIMIT ?",
        (limite,),
    ).fetchall()
    if should_close:
        real_conn.close()
    return [dict(r) for r in rows]


# ─── Metricas ─────────────────────────────────────────────────────────────────

def obtener_metricas(conn=None):
    real_conn, should_close = _ensure_conn(conn)
    hoy = datetime.now().strftime("%Y-%m-%d")
    entradas_hoy = real_conn.execute(
        "SELECT COUNT(*) FROM accesos WHERE entrada LIKE ?", (f"{hoy}%",)
    ).fetchone()[0]
    residentes = real_conn.execute("SELECT COUNT(*) FROM residentes WHERE activo=1").fetchone()[0]
    ocupados = real_conn.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='ocupado'").fetchone()[0]
    dentro = real_conn.execute("SELECT COUNT(*) FROM accesos WHERE salida IS NULL").fetchone()[0]
    if should_close:
        real_conn.close()
    return {
        "entradas_hoy": entradas_hoy,
        "residentes": residentes,
        "ocupados": ocupados,
        "dentro": dentro,
    }