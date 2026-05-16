"""
Tests unitarios para ResiControl.
Ejecutar: pytest tests/ -v
"""

import os
import sys
import sqlite3
import tempfile
import gc
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        );
        CREATE TABLE residentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad TEXT NOT NULL,
            nombre TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            placa TEXT NOT NULL UNIQUE,
            qr_code TEXT,
            activo INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT,
            cedula TEXT,
            placa TEXT,
            invitado_por TEXT,
            entrada TEXT NOT NULL,
            salida TEXT,
            operador TEXT,
            parqueadero TEXT,
            modificado_por TEXT,
            modificado_en TEXT
        );
        CREATE TABLE parqueaderos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'libre',
            placa TEXT,
            desde TEXT
        );
        CREATE TABLE incidentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            nivel TEXT NOT NULL DEFAULT 'bajo',
            operador TEXT,
            fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    yield conn
    conn.close()


def cerrar_conn(conn):
    try:
        conn.close()
    except Exception:
        pass
    gc.collect()


class TestAuth:
    def test_hash_password_returns_string(self):
        from auth import hash_password
        h = hash_password("TestPass123!")
        assert isinstance(h, str) and len(h) > 0

    def test_verify_password_correct(self):
        from auth import hash_password, verify_password
        hashed = hash_password("MiContrasena123!")
        assert verify_password("MiContrasena123!", hashed) is True

    def test_verify_password_incorrect(self):
        from auth import hash_password, verify_password
        hashed = hash_password("Correcta1!")
        assert verify_password("Incorrecta1!", hashed) is False

    def test_needs_rehash_sha256(self):
        import hashlib
        from auth import needs_rehash
        sha = hashlib.sha256("test".encode()).hexdigest()
        assert needs_rehash(sha) is True

    def test_needs_rehash_bcrypt(self):
        from auth import needs_rehash, hash_password
        assert needs_rehash(hash_password("test")) is False

    def test_check_lockout_not_blocked(self):
        from auth import check_lockout
        assert check_lockout("nuevo") == (False, 0)

    def test_password_strength_weak(self):
        from auth import validate_password_strength
        ok, msg = validate_password_strength("corto")
        assert ok is False

    def test_password_strength_strong(self):
        from auth import validate_password_strength
        assert validate_password_strength("Segura123!@#")[0] is True

    def test_blockout_after_max_attempts(self):
        from auth import record_failed_attempt, check_lockout
        for _ in range(5):
            record_failed_attempt("bloq")
        bloqueado, restante = check_lockout("bloq")
        assert bloqueado is True
        assert restante > 0

    def test_get_failed_attempts(self):
        from auth import get_failed_attempts, record_failed_attempt
        assert get_failed_attempts("nuevo") == 0
        record_failed_attempt("nuevo")
        assert get_failed_attempts("nuevo") == 1

    def test_reset_failed_attempts(self):
        from auth import record_failed_attempt, reset_failed_attempts, get_failed_attempts
        record_failed_attempt("usr")
        assert get_failed_attempts("usr") >= 1
        reset_failed_attempts("usr")
        assert get_failed_attempts("usr") == 0


class TestValidators:
    def test_validate_email_valid(self):
        from validators import validate_email
        assert validate_email("a@b.com") is True
        assert validate_email("") is True

    def test_validate_email_invalid(self):
        from validators import validate_email
        assert validate_email("no-email") is False

    def test_validate_cedula_valid(self):
        from validators import validate_cedula
        assert validate_cedula("1234567890") is True

    def test_validate_cedula_too_short(self):
        from validators import validate_cedula
        assert validate_cedula("12345") is False

    def test_validate_cedula_non_numeric(self):
        from validators import validate_cedula
        assert validate_cedula("abcdef") is False

    def test_validate_placa_valid_formats(self):
        from validators import validate_placa
        assert validate_placa("ABC123") is True
        assert validate_placa("AB123C") is True
        assert validate_placa("ABC1234") is True

    def test_validate_placa_invalid(self):
        from validators import validate_placa
        assert validate_placa("12345") is False
        assert validate_placa("ABC") is False

    def test_validate_phone_valid(self):
        from validators import validate_phone
        assert validate_phone("3001234567") is True
        assert validate_phone("") is True

    def test_validate_phone_invalid(self):
        from validators import validate_phone
        assert validate_phone("123") is False

    def test_validate_unidad(self):
        from validators import validate_unidad
        assert validate_unidad("301") is True
        assert validate_unidad("") is False

    def test_validate_required(self):
        from validators import validate_required
        assert validate_required("ok", "campo") == (True, "")
        assert validate_required("", "campo") == (False, "campo es obligatorio")


class TestDatabase:
    def test_create_tables(self, temp_conn):
        from database import create_tables
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        nombres = [r[0] for r in temp_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "usuarios" in nombres
        assert "residentes" in nombres
        assert "parqueaderos" in nombres
        assert "accesos" in nombres

    def test_create_indexes(self, temp_conn):
        from database import create_tables, create_indexes
        create_tables(temp_conn.cursor())
        create_indexes(temp_conn.cursor())
        temp_conn.commit()
        nombres = [r[0] for r in temp_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
        assert any("cedula" in n for n in nombres)
        assert any("placa" in n for n in nombres)

    def test_seed_parqueaderos(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        count = temp_conn.execute("SELECT COUNT(*) FROM parqueaderos").fetchone()[0]
        assert count == 20

    def test_insert_default_users(self, temp_conn):
        from database import create_tables, insert_default_users
        from auth import hash_password
        create_tables(temp_conn.cursor())
        insert_default_users(temp_conn.cursor(), hash_password)
        temp_conn.commit()
        users = temp_conn.execute("SELECT usuario, rol FROM usuarios ORDER BY usuario").fetchall()
        assert len(users) == 2
        assert users[0]["usuario"] == "admin"


class TestModels:
    def test_crear_usuario(self, temp_conn):
        from database import create_tables
        from models import crear_usuario
        from auth import hash_password
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        ok, msg = crear_usuario("testuser", hash_password("pass123!"), "operador", conn=temp_conn)
        assert ok is True
        row = temp_conn.execute("SELECT usuario FROM usuarios WHERE usuario='testuser'").fetchone()
        assert row["usuario"] == "testuser"
        cerrar_conn(temp_conn)

    def test_crear_usuario_duplicado(self, temp_conn):
        from database import create_tables
        from models import crear_usuario
        from auth import hash_password
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        crear_usuario("user1", hash_password("p"), "operador", conn=temp_conn)
        ok, msg = crear_usuario("user1", hash_password("p2"), "admin", conn=temp_conn)
        assert ok is False
        cerrar_conn(temp_conn)

    def test_verificar_usuario(self, temp_conn):
        from database import create_tables, insert_default_users
        from models import verificar_usuario
        from auth import hash_password, verify_password
        create_tables(temp_conn.cursor())
        insert_default_users(temp_conn.cursor(), hash_password)
        temp_conn.commit()
        user = verificar_usuario("admin", "admin123", verify_password, conn=temp_conn)
        assert user is not None and user["usuario"] == "admin"
        assert verificar_usuario("admin", "wrong", verify_password, conn=temp_conn) is None
        cerrar_conn(temp_conn)

    def test_crear_residente(self, temp_conn):
        from database import create_tables
        from models import crear_residente
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        ok, msg = crear_residente("301", "Juan Perez", "3001112222", "juan@mail.com", "ABC123", conn=temp_conn)
        assert ok is True
        row = temp_conn.execute("SELECT nombre, unidad FROM residentes WHERE placa='ABC123'").fetchone()
        assert row["nombre"] == "Juan Perez"
        assert row["unidad"] == "301"
        cerrar_conn(temp_conn)

    def test_crear_residente_placa_duplicada(self, temp_conn):
        from database import create_tables
        from models import crear_residente
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        crear_residente("301", "Juan", "3000000", "j@mail.com", "ABC123", conn=temp_conn)
        ok, msg = crear_residente("302", "Pedro", "3000001", "p@mail.com", "ABC123", conn=temp_conn)
        assert ok is False
        cerrar_conn(temp_conn)

    def test_registrar_entrada_visitante(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        ok, msg = registrar_entrada_visitante("Carlos Lopez", "CC1234567890", "DEF456", "301", "admin", conn=temp_conn)
        assert ok is True
        row = temp_conn.execute("SELECT nombre FROM accesos WHERE tipo='visitante' AND salida IS NULL").fetchone()
        assert row["nombre"] == "Carlos Lopez"
        cerrar_conn(temp_conn)

    def test_registrar_entrada_visitante_duplicado(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Carlos", "CC123", "ABC123", "301", "admin", conn=temp_conn)
        ok, msg = registrar_entrada_visitante("Carlos", "CC123", "ABC124", "301", "admin", conn=temp_conn)
        assert ok is False
        cerrar_conn(temp_conn)

    def test_registrar_salida_visitante(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        from models import registrar_entrada_visitante, registrar_salida_visitante
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Ana", "CC999", "V01", "301", "admin", conn=temp_conn)
        ok, msg = registrar_salida_visitante("CC999", "V01", "admin", conn=temp_conn)
        assert ok is True
        row = temp_conn.execute("SELECT salida FROM accesos WHERE cedula='CC999'").fetchone()
        assert row["salida"] is not None
        cerrar_conn(temp_conn)

    def test_obtener_metricas(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        from models import obtener_metricas, registrar_entrada_visitante
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Visitante1", "CC001", None, "301", "admin", conn=temp_conn)
        m = obtener_metricas(conn=temp_conn)
        assert "entradas_hoy" in m
        assert "dentro" in m
        assert m["dentro"] >= 1
        cerrar_conn(temp_conn)

    def test_asignar_parqueadero(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        from models import asignar_parqueadero
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        ok, msg = asignar_parqueadero("V01", "XYZ789", "admin", conn=temp_conn)
        assert ok is True
        estado = temp_conn.execute("SELECT estado, placa FROM parqueaderos WHERE numero='V01'").fetchone()
        assert estado["estado"] == "ocupado"
        assert estado["placa"] == "XYZ789"
        cerrar_conn(temp_conn)

    def test_liberar_parqueadero(self, temp_conn):
        from database import create_tables, seed_parqueaderos, insert_default_users
        from auth import hash_password
        from models import asignar_parqueadero, liberar_parqueadero
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        insert_default_users(temp_conn.cursor(), hash_password)
        temp_conn.commit()
        asignar_parqueadero("V01", "XYZ789", "admin", conn=temp_conn)
        liberar_parqueadero("V01", conn=temp_conn)
        estado = temp_conn.execute("SELECT estado FROM parqueaderos WHERE numero='V01'").fetchone()
        assert estado["estado"] == "libre"
        cerrar_conn(temp_conn)

    def test_eliminar_residente(self, temp_conn):
        from database import create_tables
        from models import crear_residente, eliminar_residente
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        crear_residente("301", "Juan", "300000", "j@mail.com", "ABC123", conn=temp_conn)
        eliminar_residente(1, conn=temp_conn)
        row = temp_conn.execute("SELECT activo FROM residentes WHERE id=1").fetchone()
        assert row["activo"] == 0
        cerrar_conn(temp_conn)

    def test_editar_residente(self, temp_conn):
        from database import create_tables
        from models import crear_residente, editar_residente
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        crear_residente("301", "Juan", "300000", "j@mail.com", "ABC123", conn=temp_conn)
        ok, msg = editar_residente(1, "302", "Juan Modificado", "300001", "nuevo@mail.com", "DEF456", conn=temp_conn)
        assert ok is True
        row = temp_conn.execute("SELECT nombre, unidad FROM residentes WHERE id=1").fetchone()
        assert row["nombre"] == "Juan Modificado"
        cerrar_conn(temp_conn)

    def test_obtener_historial(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante, obtener_historial
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Carlos", "CC100", "ABC123", "301", "admin", conn=temp_conn)
        h = obtener_historial(conn=temp_conn)
        assert len(h) >= 1
        assert h[0]["nombre"] == "Carlos"
        cerrar_conn(temp_conn)

    def test_obtener_historial_filtrado(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante, obtener_historial
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Carlos", "CC100", "ABC123", "301", "admin", conn=temp_conn)
        assert len(obtener_historial(conn=temp_conn)) >= 1
        assert len(obtener_historial(tipo="visitante", conn=temp_conn)) >= 1
        assert len(obtener_historial(tipo="residente", conn=temp_conn)) == 0
        cerrar_conn(temp_conn)

    def test_registrar_incidente(self, temp_conn):
        from database import create_tables
        from models import registrar_incidente, obtener_incidentes
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_incidente("Prueba", "alto", "admin", conn=temp_conn)
        inc = obtener_incidentes(conn=temp_conn)
        assert len(inc) == 1 and inc[0]["nivel"] == "alto"
        cerrar_conn(temp_conn)

    def test_obtener_visitantes_activos(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante, obtener_visitantes_activos
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Carlos", "CC100", "ABC123", "301", "admin", conn=temp_conn)
        activos = obtener_visitantes_activos(conn=temp_conn)
        assert len(activos) >= 1 and activos[0]["nombre"] == "Carlos"
        cerrar_conn(temp_conn)

    def test_obtener_parqueaderos_resumen(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        from models import obtener_parqueaderos_resumen
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        r = obtener_parqueaderos_resumen(conn=temp_conn)
        assert r["libres_residente"] == 10
        assert r["libres_visitante"] == 10
        cerrar_conn(temp_conn)

    def test_obtener_parqueaderos_por_tipo(self, temp_conn):
        from database import create_tables, seed_parqueaderos
        from models import obtener_parqueaderos_por_tipo
        create_tables(temp_conn.cursor())
        seed_parqueaderos(temp_conn.cursor())
        temp_conn.commit()
        assert len(obtener_parqueaderos_por_tipo("residente", conn=temp_conn)) == 10
        assert len(obtener_parqueaderos_por_tipo("visitante", conn=temp_conn)) == 10
        cerrar_conn(temp_conn)

    def test_editar_acceso(self, temp_conn):
        from database import create_tables
        from models import registrar_entrada_visitante, editar_acceso
        create_tables(temp_conn.cursor())
        temp_conn.commit()
        registrar_entrada_visitante("Carlos", "CC100", "ABC123", "301", "admin", conn=temp_conn)
        ok, msg = editar_acceso(1, "Carlos Mod", "CC100", "ABC123", "admin", conn=temp_conn)
        assert ok is True
        assert temp_conn.execute("SELECT nombre FROM accesos WHERE id=1").fetchone()["nombre"] == "Carlos Mod"
        cerrar_conn(temp_conn)


class TestQRManager:
    def test_get_qr_path(self):
        from qr_manager import get_qr_path
        assert "qr_ABC123.png" in get_qr_path("ABC123")

    def test_listar_qrs(self):
        from qr_manager import listar_qrs
        assert isinstance(listar_qrs(), list)


class TestBackup:
    def test_get_backups_list(self):
        from backup import get_backups_list
        assert isinstance(get_backups_list(), list)

    def test_crear_backup_estructura(self):
        from backup import crear_backup
        ok, msg = crear_backup()
        assert isinstance(ok, bool) and isinstance(msg, str)


class TestReportGenerator:
    def test_generar_csv_estructura(self):
        import os
        from report_generator import generar_csv
        ok, ruta = generar_csv("2020-01-01", "2026-12-31", "Todos")
        assert isinstance(ok, bool) and isinstance(ruta, str)
        if ok and os.path.exists(ruta):
            os.remove(ruta)

    def test_generar_pdf_estructura(self):
        import os
        from report_generator import generar_pdf
        ok, ruta = generar_pdf("2020-01-01", "2026-12-31", "Todos", "tester")
        assert isinstance(ok, bool) and isinstance(ruta, str)
        if ok and os.path.exists(ruta):
            os.remove(ruta)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])