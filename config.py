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
LOCKOUT_TIME = 300
BCRYPT_ROUNDS = 12

# ─── Colores del tema visual ──────────────────────────────────────────────────
COLORES = {
    "fondo":            "#0a0e17",
    "panel":            "#111827",
    "tarjeta":          "#1e293b",
    "borde":            "#334155",
    "borde_hover":      "#4b5563",
    "azul":             "#3b82f6",
    "azul_hover":       "#2563eb",
    "verde":            "#10b981",
    "verde_hover":      "#059669",
    "rojo":             "#ef4444",
    "rojo_hover":       "#b91c1c",
    "amarillo":         "#eab308",
    "gris":             "#6b7280",
    "texto":            "#f1f5f9",
    "texto_2":          "#d1d5db",
    "texto_3":          "#9ca3af",
    "acento":           "#00aaff",
    "fondo_contenido":  "#0f172a",
    "tabla_header":     "#1e3a5f",
    "verde_brillante":  "#22c55e",
    "boton_texto":      "#ffffff",
    "hover_amarillo":   "#ca8a04",
    "hover_generico":   "#1e40af",
    "parking_hover":    "#1e3a5f",
    "sidebar_hover":    "#1f2937",
    "azul_oscuro":      "#1d4ed8",
}

# ─── Fuentes del tema visual ─────────────────────────────────────────────────
FONT: dict = {}
FONT["logo_grande"]    = ("Helvetica", 38, "bold")
FONT["logo_sidebar"]   = ("Helvetica", 24, "bold")
FONT["seccion"]        = ("Segoe UI", 26, "bold")
FONT["bienvenida"]     = ("Segoe UI", 22, "bold")
FONT["dialogo_titulo"] = ("Segoe UI", 16, "bold")
FONT["indicador"]      = ("Segoe UI", 16)
FONT["subtitulo"]      = ("Segoe UI", 15, "bold")
FONT["titulo_seccion"] = ("Segoe UI", 14, "bold")
FONT["cuerpo"]         = ("Segoe UI", 14)
FONT["boton"]          = ("Segoe UI", 13, "bold")
FONT["cuerpo_pequeno"] = ("Segoe UI", 13)
FONT["tabla_cabecera"] = ("Segoe UI", 12, "bold")
FONT["tabla_dato"]     = ("Segoe UI", 12)
FONT["pequeno_bold"]   = ("Segoe UI", 11, "bold")
FONT["pequeno"]        = ("Segoe UI", 11)
FONT["checkbox"]       = ("Segoe UI", 12)
FONT["tarjeta_titulo"] = ("Segoe UI", 12, "bold")
FONT["tarjeta_valor"]  = ("Segoe UI", 30, "bold")

# ─── Dimensiones comunes ──────────────────────────────────────────────────────
SIDEBAR_ANCHO = 260
ENTRADA_ANCHO = 360
ENTRADA_ALTURA = 42
BOTON_ALTURA = 46
BOTON_PEQUENO_ALTURA = 28
BOTON_PEQUENO_ANCHO = 36
BOTON_SECUNDARIO_ANCHO = 220
FORMULARIO_ENTRADA_ANCHO = 420
BUSQUEDA_ENTRADA_ANCHO = 340
DIALOGO_ENTRADA_ANCHO = 280
PARKING_BOTON_ANCHO = 72
PARKING_BOTON_ALTURA = 56
PARKING_COLUMNAS = 10
TABLA_SCROLL_ALTURA = 280
LISTA_USUARIOS_ALTURA = 240
LISTA_BACKUPS_ALTURA = 300
LISTA_VISITANTES_ALTURA = 200
TABLA_HISTORIAL_ALTURA = 480
TEXTO_INCIDENTE_ALTURA = 120
CABECERA_ALTURA = 70
SECCION_RAPIDA_ALTURA = 108
TAB_BOTON_ALTURA = 40
SEPARADOR_ALTURA = 1
ACCION_BOTON_ANCHO = 80

# ─── Radios de esquinas ───────────────────────────────────────────────────────
RADIO_TARJETA = 14
RADIO_BOTON = 10
RADIO_ENTRADA = 8
RADIO_PANEL = 12
RADIO_BOTON_PEQUENO = 6
RADIO_LOGIN = 20

# ─── Espaciados comunes ───────────────────────────────────────────────────────
PAD_CARD_X = 40
PAD_CARD_Y = 12
PAD_FORM_X = 40
PAD_FORM_Y = 20
PAD_SECTION_LABEL_X = 44
PAD_LIST_BOTTOM = (0, 24)
PAD_BUTTON_ROW_Y = 16
PAD_BUTTON_GAP_X = 12
PAD_TABLA_X = 40
PAD_CELDA_X = 6
PAD_CELDA_Y = 6
PAD_CABECERA_X = 6
PAD_CABECERA_Y = 8

# ─── Bordes ────────────────────────────────────────────────────────────────────
BORDE_TARJETA = 1
