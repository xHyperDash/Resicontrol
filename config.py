import os
import sys

# ─── Rutas base (funciona en .py y en .exe empaquetado) ───────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ─── Archivos ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(BASE_DIR, "resicontrol.db")

# ─── Carpetas ─────────────────────────────────────────────────────────────────
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
QR_DIR     = os.path.join(BASE_DIR, "qrs")
LOG_DIR    = os.path.join(BASE_DIR, "logs")
LOG_FILE   = os.path.join(LOG_DIR, "app.log")

for directory in [BACKUP_DIR, QR_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# ─── Parqueaderos ─────────────────────────────────────────────────────────────
TOTAL_PARQUEADEROS = 20

# ─── Seguridad ────────────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 minutos en segundos

# Bcrypt: rondas de hashing (12 = buen balance seguridad/rendimiento)
BCRYPT_ROUNDS = 12

# ─── Colores del tema visual ──────────────────────────────────────────────────
COLORES = {
    "fondo":        "#0a0e17",
    "panel":        "#111827",
    "tarjeta":      "#1e293b",
    "borde":        "#334155",
    "borde_hover":  "#4b5563",
    "azul":         "#3b82f6",
    "azul_hover":   "#2563eb",
    "verde":        "#10b981",
    "verde_hover":  "#059669",
    "rojo":         "#ef4444",
    "rojo_hover":   "#b91c1c",
    "amarillo":     "#eab308",
    "gris":         "#6b7280",
    "texto":        "#f1f5f9",
    "texto_2":      "#d1d5db",
    "texto_3":      "#9ca3af",
}