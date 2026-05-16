import bcrypt
import hashlib
import time
from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_TIME
from logger import logger

# Almacen de intentos fallidos (para app de escritorio single-user es aceptable)
_failed_attempts = {}


# ─── Hashing ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Genera un hash bcrypt con sal automática."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica una contraseña contra su hash.
    Soporta migración transparente desde SHA-256 (64 hex chars).
    """
    if _is_sha256_hash(hashed):
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verificando contraseña: {e}")
        return False


def needs_rehash(hashed: str) -> bool:
    """Indica si el hash necesita re-hasheo (SHA-256 legacy → bcrypt)."""
    return _is_sha256_hash(hashed)


def _is_sha256_hash(value: str) -> bool:
    """Detecta si un string es un hash SHA-256 (64 hex chars)."""
    return (
        len(value) == 64
        and all(c in "0123456789abcdef" for c in value.lower())
    )


# ─── Bloqueo por intentos fallidos ────────────────────────────────────────────

def check_lockout(username: str) -> tuple[bool, int]:
    """
    Verifica si un usuario está bloqueado.
    Retorna (bloqueado: bool, segundos_restantes: int).
    """
    if username in _failed_attempts:
        attempts, lockout_start = _failed_attempts[username]
        if attempts >= MAX_LOGIN_ATTEMPTS:
            elapsed = time.time() - lockout_start
            remaining = max(0, LOCKOUT_TIME - int(elapsed))
            if remaining > 0:
                return True, remaining
            # Tiempo de bloqueo expirado → resetear
            del _failed_attempts[username]
    return False, 0


def record_failed_attempt(username: str):
    """Registra un intento fallido. Bloquea si alcanza el máximo."""
    if username in _failed_attempts:
        attempts, _ = _failed_attempts[username]
        attempts += 1
        if attempts >= MAX_LOGIN_ATTEMPTS:
            _failed_attempts[username] = (attempts, time.time())
            logger.warning(f"Usuario '{username}' bloqueado por {LOCKOUT_TIME}s")
        else:
            _failed_attempts[username] = (attempts, 0)
    else:
        _failed_attempts[username] = (1, 0)


def reset_failed_attempts(username: str):
    """Resetea los intentos fallidos tras login exitoso."""
    _failed_attempts.pop(username, None)


def get_failed_attempts(username: str) -> int:
    """Retorna el numero de intentos fallidos actuales."""
    if username in _failed_attempts:
        return _failed_attempts[username][0]
    return 0


# ─── Validación de fortaleza ──────────────────────────────────────────────────

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla requisitos mínimos.
    Retorna (válido: bool, mensaje_error: str).
    """
    errors = []
    if len(password) < 8:
        errors.append("Minimo 8 caracteres")
    if not any(c.isupper() for c in password):
        errors.append("Al menos una mayuscula")
    if not any(c.islower() for c in password):
        errors.append("Al menos una minuscula")
    if not any(c.isdigit() for c in password):
        errors.append("Al menos un numero")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
        errors.append("Al menos un caracter especial (!@#$%...)")

    if errors:
        return False, " | ".join(errors)
    return True, ""