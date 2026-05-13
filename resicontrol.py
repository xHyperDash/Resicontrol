import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import sys
import hashlib

# ── Intentar importar librerías opcionales ────────────────────────────────────
try:
    import qrcode
    from PIL import Image, ImageTk
    QR_DISPONIBLE = True
except ImportError:
    QR_DISPONIBLE = False

try:
    import pyzbar.pyzbar as pyzbar
    import cv2
    CAMARA_DISPONIBLE = True
except ImportError:
    CAMARA_DISPONIBLE = False

# ── Tema visual ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLORES = {
    "fondo":       "#0a0e17",
    "panel":       "#111827",
    "tarjeta":     "#1e293b",
    "borde":       "#334155",
    "borde_hover": "#4b5563",
    "azul":        "#3b82f6",
    "azul_hover":  "#2563eb",
    "verde":       "#10b981",
    "verde_hover": "#059669",
    "rojo":        "#ef4444",
    "rojo_hover":  "#b91c1c",
    "amarillo":    "#eab308",
    "gris":        "#6b7280",
    "texto":       "#f1f5f9",
    "texto_2":     "#d1d5db",
    "texto_3":     "#9ca3af",
}

TOTAL_PARQUEADEROS = 20

# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Convierte la contraseña en hash SHA-256 para no guardarla en texto plano."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_path() -> str:
    """Devuelve la ruta correcta de la BD tanto en .py como en .exe empaquetado."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    return os.path.join(base, "resicontrol.db")


def abrir_archivo(ruta: str):
    """Abre un archivo con la aplicación predeterminada del sistema operativo."""
    try:
        if sys.platform == "win32":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            os.system(f'open "{ruta}"')
        else:
            os.system(f'xdg-open "{ruta}"')
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class ResiControl(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ResiControl — Gestión de Seguridad Residencial")
        self.geometry("1300x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORES["fondo"])

        # Estado de sesión
        self.current_user: str | None = None
        self.rol: str | None = None
        self.current_page: str | None = None

        # Cámara
        self.cap = None
        self.scanning = False
        self.video_label = None

        # Base de datos
        self.conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")   # mejor rendimiento
        self.conn.row_factory = sqlite3.Row            # acceso por nombre de columna
        self.cursor = self.conn.cursor()

        self._crear_tablas()
        self._insertar_usuarios_default()

        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.mostrar_login()

    # ── Base de datos ─────────────────────────────────────────────────────────

    def _crear_tablas(self):
        self.cursor.executescript("""
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
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo        TEXT    NOT NULL CHECK(tipo IN ('residente','visitante')),
                nombre      TEXT,
                cedula      TEXT,
                placa       TEXT,
                invitado_por TEXT,
                entrada     TEXT    NOT NULL,
                salida      TEXT,
                operador    TEXT,
                parqueadero TEXT
            );

            CREATE TABLE IF NOT EXISTS incidentes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT    NOT NULL,
                nivel       TEXT    NOT NULL DEFAULT 'bajo' CHECK(nivel IN ('bajo','medio','alto')),
                operador    TEXT,
                fecha       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );
        """)
        self.conn.commit()
        self._seed_parqueaderos()

    def _seed_parqueaderos(self):
        """Crea los parqueaderos si la tabla está vacía."""
        self.cursor.execute("SELECT COUNT(*) FROM parqueaderos")
        if self.cursor.fetchone()[0] == 0:
            datos = []
            for i in range(1, 11):
                datos.append((f"R{i:02d}", "residente"))
            for i in range(1, 11):
                datos.append((f"V{i:02d}", "visitante"))
            self.cursor.executemany(
                "INSERT INTO parqueaderos (numero, tipo) VALUES (?,?)", datos
            )
            self.conn.commit()

    def _insertar_usuarios_default(self):
        """Inserta admin y portero con contraseñas hasheadas si no existen."""
        defaults = [
            ("admin",   "admin123", "admin"),
            ("portero", "1234",     "operador"),
        ]
        for usuario, pwd, rol in defaults:
            try:
                self.cursor.execute(
                    "INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,?)",
                    (usuario, hash_password(pwd), rol),
                )
                self.conn.commit()
            except sqlite3.IntegrityError:
                pass

    # ── Utilidades UI ─────────────────────────────────────────────────────────

    def _limpiar(self):
        """Destruye todos los widgets de la ventana."""
        self._detener_camara()
        for w in self.winfo_children():
            w.destroy()

    def _detener_camara(self):
        self.scanning = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _on_close(self):
        self._detener_camara()
        self.conn.close()
        self.destroy()

    def _label_seccion(self, parent, texto: str):
        ctk.CTkLabel(
            parent, text=texto,
            font=("Segoe UI", 26, "bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(24, 8))

    def _tarjeta(self, parent, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            fg_color=COLORES["tarjeta"],
            corner_radius=14,
            border_width=1,
            border_color=COLORES["borde"],
            **kwargs,
        )

    def _boton(self, parent, texto, comando, color=None, hover=None, **kwargs):
        color = color or COLORES["azul"]
        hover = hover or COLORES["azul_hover"]
        return ctk.CTkButton(
            parent, text=texto, command=comando,
            fg_color=color, hover_color=hover,
            corner_radius=10, height=46,
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff",
            **kwargs,
        )

    def _entrada(self, parent, placeholder="", **kwargs) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color="#111827",
            border_color=COLORES["borde_hover"],
            corner_radius=8,
            height=42,
            font=("Segoe UI", 13),
            **kwargs,
        )

    def _notificar(self, tipo: str, titulo: str, mensaje: str):
        iconos = {"ok": "check", "error": "cancel", "aviso": "warning", "info": "info"}
        CTkMessagebox(title=titulo, message=mensaje, icon=iconos.get(tipo, "info"))

    # ── LOGIN ─────────────────────────────────────────────────────────────────

    def mostrar_login(self):
        self._limpiar()
        self.geometry("480x560")
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, corner_radius=20, fg_color=COLORES["panel"],
                             border_width=1, border_color=COLORES["borde"])
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        ctk.CTkLabel(frame, text="ResiControl",
                     font=("Helvetica", 38, "bold"), text_color="#00aaff").pack(pady=(32, 4))
        ctk.CTkLabel(frame, text="Gestión de Seguridad Residencial",
                     font=("Segoe UI", 14), text_color=COLORES["texto_3"]).pack()

        ctk.CTkLabel(frame, text="Usuario", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).pack(anchor="w", padx=40, pady=(28, 4))
        self.user_entry = self._entrada(frame, placeholder="Ingrese su usuario", width=360)
        self.user_entry.pack()

        ctk.CTkLabel(frame, text="Contraseña", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).pack(anchor="w", padx=40, pady=(16, 4))
        self.pwd_entry = self._entrada(frame, placeholder="••••••••", width=360, show="*")
        self.pwd_entry.pack()

        self._boton(frame, "Iniciar Sesión", self.login, width=360).pack(pady=28)

        self.error_lbl = ctk.CTkLabel(frame, text="",
                                      text_color=COLORES["rojo"], font=("Segoe UI", 13))
        self.error_lbl.pack()

        self.user_entry.bind("<Return>", lambda _: self.login())
        self.pwd_entry.bind("<Return>", lambda _: self.login())
        self.user_entry.focus_set()

    def login(self):
        usuario = self.user_entry.get().strip()
        pwd     = self.pwd_entry.get().strip()

        if not usuario or not pwd:
            self.error_lbl.configure(text="Complete todos los campos")
            return

        self.cursor.execute(
            "SELECT rol FROM usuarios WHERE usuario=? AND password=?",
            (usuario, hash_password(pwd)),
        )
        fila = self.cursor.fetchone()

        if fila:
            self.current_user = usuario
            self.rol = fila["rol"]
            self.mostrar_dashboard()
        else:
            self.error_lbl.configure(text="Usuario o contraseña incorrectos")

    # ── DASHBOARD ────────────────────────────────────────────────────────────

    def mostrar_dashboard(self):
        self._limpiar()
        self.geometry("1300x820")
        self.resizable(True, True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORES["panel"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="ResiControl",
                     font=("Helvetica", 24, "bold"), text_color="#00aaff").pack(pady=(32, 4), padx=20)
        ctk.CTkLabel(self.sidebar, text=f"{self.rol.upper()}",
                     font=("Segoe UI", 11), text_color=COLORES["texto_3"]).pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=16, padx=20)

        menu = [
            ("Inicio",                 "🏠",  self._ir_inicio),
            ("Visitantes",             "🚪",  self._ir_visitantes),
            ("Residentes",             "👤",  self._ir_residentes),
            ("Parqueaderos",           "🚗",  self._ir_parqueaderos),
            ("Historial",              "📜",  self._ir_historial),
            ("Incidentes",             "⚠️",  self._ir_incidentes),
            ("Reportes PDF",           "📄",  self._ir_reportes),
        ]
        if self.rol == "admin":
            menu.append(("Usuarios",   "🔑",  self._ir_usuarios))
            menu.append(("Borrar datos","🗑️", self._ir_borrar))

        if CAMARA_DISPONIBLE:
            menu.insert(3, ("Escaneo QR", "🔍", self._ir_qr))

        menu.append(("Cerrar Sesión", "↩", self.mostrar_login))

        self.menu_btns: dict[str, ctk.CTkButton] = {}
        for texto, icono, cmd in menu:
            es_peligro = texto in ("Cerrar Sesión", "Borrar datos")
            fg    = COLORES["rojo"]  if es_peligro else "transparent"
            hover = COLORES["rojo_hover"] if es_peligro else "#1f2937"
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icono}  {texto}",
                fg_color=fg, hover_color=hover,
                anchor="w", height=52, corner_radius=0,
                font=("Segoe UI", 13), text_color=COLORES["texto_2"],
                command=lambda t=texto, c=cmd: self._cambiar_pagina(t, c),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.menu_btns[texto] = btn

        # Contenido principal scrolleable
        self.contenido = ctk.CTkScrollableFrame(self, fg_color="#0f172a")
        self.contenido.pack(side="right", fill="both", expand=True)

        self._ir_inicio()

    def _cambiar_pagina(self, nombre: str, accion):
        self._detener_camara()
        for t, btn in self.menu_btns.items():
            es_peligro = t in ("Cerrar Sesión", "Borrar datos")
            btn.configure(fg_color=(COLORES["rojo"] if es_peligro else "#1e293b")
                          if t == nombre
                          else (COLORES["rojo"] if es_peligro else "transparent"))
        self.current_page = nombre
        for w in self.contenido.winfo_children():
            w.destroy()
        accion()

    def _limpiar_contenido(self):
        for w in self.contenido.winfo_children():
            w.destroy()

    # ── INICIO ────────────────────────────────────────────────────────────────

    def _ir_inicio(self):
        self._limpiar_contenido()
        self.current_page = "Inicio"

        # Cabecera
        cab = ctk.CTkFrame(self.contenido, fg_color="#1e293b", height=70, corner_radius=0)
        cab.pack(fill="x")
        ctk.CTkLabel(cab, text=f"Bienvenido, {self.current_user.upper()}",
                     font=("Segoe UI", 22, "bold"), text_color="#00aaff").pack(pady=18)

        # Métricas
        self._renderizar_metricas()

        # Accesos rápidos — altura fija para que no se muevan con el scroll
        sec = self._tarjeta(self.contenido)
        sec.pack(fill="x", padx=32, pady=(0, 24))
        sec.pack_propagate(False)
        sec.configure(height=108)

        ctk.CTkLabel(sec, text="Accesos rápidos",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLORES["texto_3"]).pack(anchor="w", padx=20, pady=(8, 4))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(padx=16)

        for etiqueta, color, cmd in [
            ("🚪 Visitantes",   COLORES["azul"],    self._ir_visitantes),
            ("👤 Residentes",   "#2563eb",           self._ir_residentes),
            ("🚗 Parqueaderos", COLORES["verde"],    self._ir_parqueaderos),
            ("📜 Historial",    COLORES["amarillo"], self._ir_historial),
            ("📄 Reporte",      "#1d4ed8",           self._ir_reportes),
        ]:
            ctk.CTkButton(
                fila, text=etiqueta, width=160, height=44,
                corner_radius=10, fg_color=color, hover_color="#1e40af",
                font=("Segoe UI", 12, "bold"), text_color="#fff",
                command=cmd,
            ).pack(side="left", padx=8)

    def _renderizar_metricas(self):
        # Limpia métricas anteriores si existen
        if hasattr(self, "_metricas_frame"):
            self._metricas_frame.destroy()

        self._metricas_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._metricas_frame.pack(fill="x", padx=32, pady=(24, 16))

        hoy = datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute("SELECT COUNT(*) FROM accesos WHERE entrada LIKE ?", (f"{hoy}%",))
        entradas = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM residentes WHERE activo=1")
        residentes = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='ocupado'")
        ocupados = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM accesos WHERE salida IS NULL")
        dentro = self.cursor.fetchone()[0]

        datos = [
            ("Entradas hoy",    str(entradas),  "↑",  "#22c55e"),
            ("Residentes",      str(residentes),"👥",  COLORES["azul"]),
            ("Parqueaderos oc.","🚗 " + str(ocupados), "🚗", COLORES["amarillo"]),
            ("Dentro ahora",    str(dentro),    "🔴",  COLORES["rojo"]),
        ]

        for titulo, valor, icono, color in datos:
            card = ctk.CTkFrame(self._metricas_frame, fg_color=COLORES["tarjeta"],
                                corner_radius=14, border_width=1, border_color=COLORES["borde"])
            card.pack(side="left", expand=True, padx=10, fill="both")

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 4))
            ctk.CTkLabel(top, text=titulo, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left")
            ctk.CTkLabel(top, text=icono, font=("Segoe UI", 16),
                         text_color=color).pack(side="right")

            ctk.CTkLabel(card, text=valor, font=("Segoe UI", 30, "bold"),
                         text_color=COLORES["texto"]).pack(pady=(4, 14))

        # Auto-actualizar cada 10 s si sigue en Inicio
        if self.current_page == "Inicio":
            self.after(10000, self._renderizar_metricas)

    # ── VISITANTES ────────────────────────────────────────────────────────────

    def _ir_visitantes(self):
        self._limpiar_contenido()
        self.current_page = "Visitantes"
        self._label_seccion(self.contenido, "Registro de Visitantes")

        card = self._tarjeta(self.contenido)
        card.pack(fill="both", padx=40, pady=12, expand=True)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")

        campos = [
            ("Nombre completo *", "Ej: Carlos Pérez", False),
            ("Cédula *",          "Ej: 1234567890",   False),
            ("Placa (opcional)",  "Ej: ABC123",        False),
            ("Invitado por (unidad) *", "Ej: 301",     False),
        ]
        self._vis_entradas: dict[str, ctk.CTkEntry] = {}
        for i, (label, hint, oculto) in enumerate(campos):
            ctk.CTkLabel(form, text=label, font=("Segoe UI", 13),
                         text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0,16), pady=8)
            e = self._entrada(form, placeholder=hint, width=420, show="*" if oculto else "")
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._vis_entradas[label] = e

        self._vis_consent = ctk.CTkCheckBox(
            card, text="Autorizo el tratamiento de datos personales (Ley 1581/2012)",
            font=("Segoe UI", 12), text_color=COLORES["texto_2"],
        )
        self._vis_consent.pack(pady=12)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=16)
        self._boton(fila, "✅  Registrar Entrada", self._registrar_entrada_vis,
                    width=220).pack(side="left", padx=12)
        self._boton(fila, "🚪  Registrar Salida", self._registrar_salida_vis,
                    color=COLORES["rojo"], hover=COLORES["rojo_hover"], width=220).pack(side="left", padx=12)

        # Tabla de visitantes activos
        ctk.CTkLabel(self.contenido, text="Visitantes actualmente dentro",
                     font=("Segoe UI", 15, "bold"), text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(8, 4))
        self._tabla_visitantes_activos()

    def _tabla_visitantes_activos(self):
        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                       corner_radius=12, height=200)
        lista.pack(fill="x", padx=40, pady=(0, 24))

        encabezados = ["Nombre", "Cédula", "Placa", "Unidad", "Entrada", "Operador"]
        fila_h = ctk.CTkFrame(lista, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=8, pady=8)

        self.cursor.execute("""
            SELECT nombre, cedula, placa, invitado_por, entrada, operador
            FROM accesos WHERE salida IS NULL AND tipo='visitante'
            ORDER BY entrada DESC LIMIT 30
        """)
        for i, fila in enumerate(self.cursor.fetchall()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for val in fila:
                ctk.CTkLabel(f, text=str(val or "—"), font=("Segoe UI", 12),
                             text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=8, pady=6)

    def _registrar_entrada_vis(self):
        if not self._vis_consent.get():
            self._notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return

        nombre   = self._vis_entradas["Nombre completo *"].get().strip()
        cedula   = self._vis_entradas["Cédula *"].get().strip()
        placa    = self._vis_entradas["Placa (opcional)"].get().strip().upper()
        unidad   = self._vis_entradas["Invitado por (unidad) *"].get().strip()

        if not nombre or not cedula or not unidad:
            self._notificar("error", "Error", "Nombre, Cédula y Unidad son obligatorios")
            return

        # Verificar si ya está dentro
        self.cursor.execute(
            "SELECT id FROM accesos WHERE cedula=? AND salida IS NULL AND tipo='visitante'",
            (cedula,)
        )
        if self.cursor.fetchone():
            self._notificar("aviso", "Ya registrado", "Este visitante ya tiene una entrada activa sin salida")
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO accesos (tipo,nombre,cedula,placa,invitado_por,entrada,operador) VALUES (?,?,?,?,?,?,?)",
            ("visitante", nombre, cedula, placa or None, unidad, ahora, self.current_user),
        )
        self.conn.commit()
        self._notificar("ok", "Éxito", f"Entrada registrada para {nombre}")
        self._ir_visitantes()

    def _registrar_salida_vis(self):
        cedula = self._vis_entradas["Cédula *"].get().strip()
        placa  = self._vis_entradas["Placa (opcional)"].get().strip().upper()

        if not cedula and not placa:
            self._notificar("aviso", "Atención", "Ingrese cédula o placa para registrar salida")
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            UPDATE accesos SET salida=?
            WHERE (cedula=? OR placa=?) AND salida IS NULL AND tipo='visitante'
        """, (ahora, cedula or None, placa or None))

        if self.cursor.rowcount > 0:
            self.conn.commit()
            # Liberar parqueadero si tenía uno
            if placa:
                self.cursor.execute(
                    "UPDATE parqueaderos SET estado='libre', placa=NULL, desde=NULL WHERE placa=?",
                    (placa,)
                )
                self.conn.commit()
            self._notificar("ok", "Éxito", "Salida registrada correctamente")
            self._ir_visitantes()
        else:
            self._notificar("aviso", "No encontrado", "No hay entrada activa para esta cédula/placa")

    # ── RESIDENTES ────────────────────────────────────────────────────────────

    def _ir_residentes(self):
        self._limpiar_contenido()
        self.current_page = "Residentes"
        self._label_seccion(self.contenido, "Gestión de Residentes")

        # Tabs simples
        tab_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        tab_frame.pack(fill="x", padx=40, pady=4)

        self._tab_content = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._tab_content.pack(fill="both", expand=True)

        def cambiar_tab(tab):
            for w in self._tab_content.winfo_children():
                w.destroy()
            if tab == "nuevo":
                self._form_nuevo_residente()
            else:
                self._lista_residentes()
            for t, b in tab_btns.items():
                b.configure(fg_color=COLORES["azul"] if t == tab else COLORES["tarjeta"])

        tab_btns = {}
        for nombre, clave in [("Nuevo residente", "nuevo"), ("Ver residentes", "lista")]:
            b = ctk.CTkButton(tab_frame, text=nombre, width=200, height=40,
                              corner_radius=8, font=("Segoe UI", 13),
                              fg_color=COLORES["tarjeta"], hover_color=COLORES["borde"],
                              command=lambda k=clave: cambiar_tab(k))
            b.pack(side="left", padx=6)
            tab_btns[clave] = b

        cambiar_tab("nuevo")

    def _form_nuevo_residente(self):
        card = self._tarjeta(self._tab_content)
        card.pack(fill="x", padx=40, pady=12)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")

        campos = [
            ("Unidad *",        "Ej: 301"),
            ("Nombre completo *","Ej: María López"),
            ("Teléfono",        "Ej: 3001234567"),
            ("Email",           "Ej: maria@correo.com"),
            ("Placa *",         "Ej: XYZ789"),
        ]
        self._res_entradas: dict[str, ctk.CTkEntry] = {}
        for i, (label, hint) in enumerate(campos):
            ctk.CTkLabel(form, text=label, font=("Segoe UI", 13),
                         text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0,16), pady=8)
            e = self._entrada(form, placeholder=hint, width=420)
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._res_entradas[label] = e

        self._res_consent = ctk.CTkCheckBox(
            card, text="Autorizo tratamiento de datos (Ley 1581/2012)",
            font=("Segoe UI", 12), text_color=COLORES["texto_2"],
        )
        self._res_consent.pack(pady=12)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=16)
        self._boton(fila, "👤  Registrar Residente", self._registrar_residente,
                    color=COLORES["verde"], hover=COLORES["verde_hover"], width=240).pack(side="left", padx=12)
        if QR_DISPONIBLE:
            self._boton(fila, "🔲  Generar QR", self._generar_qr,
                        color=COLORES["amarillo"], hover="#ca8a04", width=180).pack(side="left", padx=12)

    def _registrar_residente(self):
        if not self._res_consent.get():
            self._notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return

        unidad = self._res_entradas["Unidad *"].get().strip()
        nombre = self._res_entradas["Nombre completo *"].get().strip()
        placa  = self._res_entradas["Placa *"].get().strip().upper()
        tel    = self._res_entradas["Teléfono"].get().strip()
        email  = self._res_entradas["Email"].get().strip()

        if not unidad or not nombre or not placa:
            self._notificar("error", "Error", "Unidad, Nombre y Placa son obligatorios")
            return

        try:
            self.cursor.execute(
                "INSERT INTO residentes (unidad,nombre,telefono,email,placa) VALUES (?,?,?,?,?)",
                (unidad, nombre, tel or None, email or None, placa),
            )
            self.conn.commit()
            self._notificar("ok", "Éxito", f"Residente {nombre} registrado correctamente")
            self._ir_residentes()
        except sqlite3.IntegrityError:
            self._notificar("error", "Error", f"La placa {placa} ya está registrada")

    def _generar_qr(self):
        if not QR_DISPONIBLE:
            return
        placa = self._res_entradas["Placa *"].get().strip().upper()
        if not placa:
            self._notificar("error", "Error", "Ingrese la placa primero")
            return
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(placa)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        ruta = f"qr_{placa}.png"
        img.save(ruta)
        self.cursor.execute("UPDATE residentes SET qr_code=? WHERE placa=?", (ruta, placa))
        self.conn.commit()
        self._notificar("ok", "QR generado", f"Guardado en: {ruta}")

    def _lista_residentes(self):
        card = self._tarjeta(self._tab_content)
        card.pack(fill="both", padx=40, pady=12, expand=True)

        # Buscador
        buscador_frame = ctk.CTkFrame(card, fg_color="transparent")
        buscador_frame.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(buscador_frame, text="Buscar:", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).pack(side="left", padx=(0, 10))
        self._busq_res = self._entrada(buscador_frame, placeholder="Nombre, unidad o placa…", width=360)
        self._busq_res.pack(side="left")
        self._boton(buscador_frame, "🔍 Buscar", self._buscar_residentes,
                    width=120).pack(side="left", padx=10)

        # Tabla
        self._tabla_res = ctk.CTkScrollableFrame(card, fg_color="#111827", corner_radius=8)
        self._tabla_res.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._renderizar_tabla_residentes()

    def _renderizar_tabla_residentes(self, filtro=""):
        for w in self._tabla_res.winfo_children():
            w.destroy()

        encabezados = ["ID", "Unidad", "Nombre", "Teléfono", "Email", "Placa", "Acciones"]
        fila_h = ctk.CTkFrame(self._tabla_res, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=6, pady=8)

        query = """
            SELECT id, unidad, nombre, telefono, email, placa
            FROM residentes WHERE activo=1
        """
        params = []
        if filtro:
            query += " AND (nombre LIKE ? OR unidad LIKE ? OR placa LIKE ?)"
            params = [f"%{filtro}%"] * 3
        query += " ORDER BY nombre"

        self.cursor.execute(query, params)
        for i, row in enumerate(self.cursor.fetchall()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._tabla_res, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for val in row:
                ctk.CTkLabel(f, text=str(val or "—"), font=("Segoe UI", 12),
                             text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=6, pady=6)
            rid = row["id"]
            ctk.CTkButton(f, text="Eliminar", width=80, height=28,
                          fg_color=COLORES["rojo"], hover_color=COLORES["rojo_hover"],
                          font=("Segoe UI", 11), corner_radius=6,
                          command=lambda i=rid: self._eliminar_residente(i)).pack(side="left", padx=8)

    def _buscar_residentes(self):
        self._renderizar_tabla_residentes(self._busq_res.get().strip())

    def _eliminar_residente(self, rid: int):
        res = CTkMessagebox(title="Confirmar", message="¿Eliminar este residente?",
                            icon="warning", option_1="Sí, eliminar", option_2="Cancelar")
        if res.get() == "Sí, eliminar":
            self.cursor.execute("UPDATE residentes SET activo=0 WHERE id=?", (rid,))
            self.conn.commit()
            self._renderizar_tabla_residentes()

    # ── PARQUEADEROS ──────────────────────────────────────────────────────────

    def _ir_parqueaderos(self):
        self._limpiar_contenido()
        self.current_page = "Parqueaderos"
        self._label_seccion(self.contenido, "Parqueaderos")
        self._renderizar_parqueaderos()

    def _renderizar_parqueaderos(self):
        # Resumen
        self.cursor.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='libre' AND tipo='residente'")
        libres_r = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='libre' AND tipo='visitante'")
        libres_v = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM parqueaderos WHERE estado='ocupado'")
        ocupados = self.cursor.fetchone()[0]

        res_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        res_frame.pack(fill="x", padx=40, pady=(0, 16))

        for titulo, valor, color in [
            ("Residentes libres", str(libres_r), "#22c55e"),
            ("Visitantes libres", str(libres_v), COLORES["azul"]),
            ("Ocupados",          str(ocupados), COLORES["rojo"]),
        ]:
            c = ctk.CTkFrame(res_frame, fg_color=COLORES["tarjeta"], corner_radius=12,
                             border_width=1, border_color=COLORES["borde"])
            c.pack(side="left", expand=True, padx=10, fill="both")
            ctk.CTkLabel(c, text=titulo, font=("Segoe UI", 12), text_color=COLORES["texto_3"]).pack(pady=(12, 2))
            ctk.CTkLabel(c, text=valor, font=("Segoe UI", 28, "bold"), text_color=color).pack(pady=(0, 12))

        # Grid visual
        ctk.CTkLabel(self.contenido, text="Residentes", font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(8, 4))
        self._grid_parqueaderos("residente")

        ctk.CTkLabel(self.contenido, text="Visitantes", font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(16, 4))
        self._grid_parqueaderos("visitante")

        # Asignación manual
        sec = self._tarjeta(self.contenido)
        sec.pack(fill="x", padx=40, pady=16)
        ctk.CTkLabel(sec, text="Asignar parqueadero a visitante",
                     font=("Segoe UI", 14, "bold"), text_color=COLORES["texto"]).pack(anchor="w", padx=20, pady=(14, 6))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 16))

        self._park_placa = self._entrada(fila, placeholder="Placa del vehículo", width=220)
        self._park_placa.pack(side="left", padx=(0, 12))

        self._park_numero = ctk.CTkComboBox(fila, width=160,
                                            values=self._parqueaderos_libres_visitante())
        self._park_numero.pack(side="left", padx=(0, 12))

        self._boton(fila, "Asignar", self._asignar_parqueadero, width=140).pack(side="left")

    def _parqueaderos_libres_visitante(self) -> list[str]:
        self.cursor.execute("SELECT numero FROM parqueaderos WHERE tipo='visitante' AND estado='libre'")
        return [r["numero"] for r in self.cursor.fetchall()] or ["Sin espacio"]

    def _grid_parqueaderos(self, tipo: str):
        self.cursor.execute(
            "SELECT numero, estado, placa FROM parqueaderos WHERE tipo=? ORDER BY numero", (tipo,)
        )
        filas = self.cursor.fetchall()

        grid = ctk.CTkFrame(self.contenido, fg_color="transparent")
        grid.pack(padx=44, pady=4, fill="x")

        cols = 10
        for idx, row in enumerate(filas):
            col = idx % cols
            fila_idx = idx // cols
            color = "#22c55e" if row["estado"] == "libre" else COLORES["rojo"]
            texto = row["numero"]
            tooltip = row["placa"] or ""
            btn = ctk.CTkButton(
                grid, text=texto, width=72, height=56,
                corner_radius=10, fg_color=color, hover_color="#1e3a5f",
                font=("Segoe UI", 12, "bold"), text_color="#fff",
                command=lambda p=row["numero"], s=row["estado"], pl=row["placa"]:
                    self._accion_parqueadero(p, s, pl),
            )
            btn.grid(row=fila_idx, column=col, padx=5, pady=5)

    def _accion_parqueadero(self, numero: str, estado: str, placa: str | None):
        if estado == "ocupado":
            msg = f"Parqueadero {numero}\nPlaca: {placa or '—'}\n\n¿Liberar?"
            res = CTkMessagebox(title="Parqueadero ocupado", message=msg,
                                icon="warning", option_1="Liberar", option_2="Cancelar")
            if res.get() == "Liberar":
                self.cursor.execute(
                    "UPDATE parqueaderos SET estado='libre', placa=NULL, desde=NULL WHERE numero=?",
                    (numero,)
                )
                self.conn.commit()
                self._ir_parqueaderos()
        else:
            self._notificar("info", "Parqueadero libre", f"{numero} está disponible")

    def _asignar_parqueadero(self):
        placa   = self._park_placa.get().strip().upper()
        numero  = self._park_numero.get().strip()

        if not placa or not numero or numero == "Sin espacio":
            self._notificar("error", "Error", "Ingrese placa y seleccione un parqueadero")
            return

        self.cursor.execute("SELECT estado FROM parqueaderos WHERE numero=?", (numero,))
        row = self.cursor.fetchone()
        if not row or row["estado"] == "ocupado":
            self._notificar("aviso", "No disponible", "Ese parqueadero ya está ocupado")
            return

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "UPDATE parqueaderos SET estado='ocupado', placa=?, desde=? WHERE numero=?",
            (placa, ahora, numero),
        )
        self.conn.commit()
        self._notificar("ok", "Asignado", f"Parqueadero {numero} asignado a {placa}")
        self._ir_parqueaderos()

    # ── HISTORIAL ─────────────────────────────────────────────────────────────

    def _ir_historial(self):
        self._limpiar_contenido()
        self.current_page = "Historial"
        self._label_seccion(self.contenido, "Historial de Accesos")

        filtros = ctk.CTkFrame(self.contenido, fg_color="transparent")
        filtros.pack(fill="x", padx=40, pady=8)

        self._hist_busq = self._entrada(filtros, placeholder="Buscar por nombre, cédula o placa…", width=340)
        self._hist_busq.pack(side="left", padx=(0, 10))

        self._hist_tipo = ctk.CTkComboBox(filtros, values=["Todos", "residente", "visitante"], width=160)
        self._hist_tipo.pack(side="left", padx=(0, 10))

        self._boton(filtros, "🔍 Filtrar", self._filtrar_historial, width=120).pack(side="left")

        self._hist_frame = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                                   corner_radius=12, height=480)
        self._hist_frame.pack(fill="both", padx=40, pady=12, expand=True)
        self._renderizar_historial()

    def _renderizar_historial(self, busq="", tipo="Todos"):
        for w in self._hist_frame.winfo_children():
            w.destroy()

        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador"]
        fila_h = ctk.CTkFrame(self._hist_frame, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=6, pady=8)

        query = "SELECT tipo, nombre, cedula, placa, entrada, salida, operador FROM accesos WHERE 1=1"
        params: list = []
        if busq:
            query += " AND (nombre LIKE ? OR cedula LIKE ? OR placa LIKE ?)"
            params += [f"%{busq}%"] * 3
        if tipo != "Todos":
            query += " AND tipo=?"
            params.append(tipo)
        query += " ORDER BY entrada DESC LIMIT 100"

        self.cursor.execute(query, params)
        for i, row in enumerate(self.cursor.fetchall()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._hist_frame, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for val in row:
                texto = str(val or "—")
                if val is None and "salida" in encabezados:
                    texto = "🟢 Activo" if list(row).index(val) == 5 else "—"
                ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12),
                             text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=6, pady=6)

    def _filtrar_historial(self):
        self._renderizar_historial(
            self._hist_busq.get().strip(),
            self._hist_tipo.get(),
        )

    # ── INCIDENTES ────────────────────────────────────────────────────────────

    def _ir_incidentes(self):
        self._limpiar_contenido()
        self.current_page = "Incidentes"
        self._label_seccion(self.contenido, "Registro de Incidentes")

        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)

        ctk.CTkLabel(card, text="Descripción del incidente *", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).pack(anchor="w", padx=20, pady=(16, 4))
        self._inc_desc = ctk.CTkTextbox(card, height=120, font=("Segoe UI", 13),
                                        fg_color="#111827", corner_radius=8)
        self._inc_desc.pack(fill="x", padx=20)

        ctk.CTkLabel(card, text="Nivel de alerta", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).pack(anchor="w", padx=20, pady=(12, 4))
        self._inc_nivel = ctk.CTkComboBox(card, values=["bajo", "medio", "alto"], width=200)
        self._inc_nivel.pack(anchor="w", padx=20, pady=(0, 16))

        self._boton(card, "⚠️  Registrar Incidente", self._registrar_incidente,
                    color=COLORES["amarillo"], hover="#ca8a04").pack(pady=12)

        # Lista
        ctk.CTkLabel(self.contenido, text="Incidentes recientes", font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(16, 4))

        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                       corner_radius=12, height=280)
        lista.pack(fill="x", padx=40, pady=(0, 24))

        self.cursor.execute(
            "SELECT nivel, descripcion, operador, fecha FROM incidentes ORDER BY fecha DESC LIMIT 30"
        )
        colores_nivel = {"bajo": "#22c55e", "medio": COLORES["amarillo"], "alto": COLORES["rojo"]}
        for i, row in enumerate(self.cursor.fetchall()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=2)
            color = colores_nivel.get(row["nivel"], COLORES["texto_3"])
            ctk.CTkLabel(f, text=f"[{row['nivel'].upper()}]", font=("Segoe UI", 11, "bold"),
                         text_color=color, width=70).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(f, text=row["descripcion"], font=("Segoe UI", 12),
                         text_color=COLORES["texto_2"], wraplength=500, justify="left").pack(side="left", expand=True)
            ctk.CTkLabel(f, text=f"{row['operador']} — {row['fecha']}", font=("Segoe UI", 11),
                         text_color=COLORES["texto_3"]).pack(side="right", padx=12)

    def _registrar_incidente(self):
        desc  = self._inc_desc.get("1.0", "end").strip()
        nivel = self._inc_nivel.get()

        if not desc:
            self._notificar("error", "Error", "La descripción es obligatoria")
            return

        self.cursor.execute(
            "INSERT INTO incidentes (descripcion, nivel, operador) VALUES (?,?,?)",
            (desc, nivel, self.current_user),
        )
        self.conn.commit()
        self._notificar("ok", "Éxito", "Incidente registrado correctamente")
        self._ir_incidentes()

    # ── ESCANEO QR ────────────────────────────────────────────────────────────

    def _ir_qr(self):
        if not CAMARA_DISPONIBLE:
            self._notificar("error", "No disponible", "cv2 y pyzbar no están instalados")
            return
        self._limpiar_contenido()
        self.current_page = "Escaneo QR"
        self._label_seccion(self.contenido, "Escaneo de Placa QR")

        card = self._tarjeta(self.contenido)
        card.pack(fill="both", padx=40, pady=12, expand=True)

        self.video_label = ctk.CTkLabel(card, text="Presiona 'Iniciar' para activar la cámara")
        self.video_label.pack(pady=20)

        self._boton(card, "▶  Iniciar escaneo", self._iniciar_escaneo, width=220).pack(pady=8)
        self._boton(card, "⏹  Detener",         self._detener_camara,
                    color=COLORES["rojo"], hover=COLORES["rojo_hover"], width=220).pack(pady=8)

        self.info_qr = ctk.CTkLabel(card, text="", font=("Segoe UI", 14),
                                    text_color=COLORES["texto_2"])
        self.info_qr.pack(pady=12)

    def _iniciar_escaneo(self):
        self.scanning = True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self._notificar("error", "Error", "No se pudo abrir la cámara")
            self.scanning = False
            return
        self._leer_frame()

    def _leer_frame(self):
        if not self.scanning or not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.after(30, self._leer_frame)
            return

        decoded = pyzbar.decode(frame)
        if decoded:
            placa = decoded[0].data.decode("utf-8").strip().upper()
            self._detener_camara()
            self._mostrar_info_residente_qr(placa)
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((640, 400))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 400))
        self.video_label.configure(image=ctk_img, text="")
        self.video_label.image = ctk_img
        self.after(15, self._leer_frame)

    def _mostrar_info_residente_qr(self, placa: str):
        self.cursor.execute("SELECT * FROM residentes WHERE placa=? AND activo=1", (placa,))
        row = self.cursor.fetchone()
        if row:
            info = (f"Unidad: {row['unidad']}\nNombre: {row['nombre']}\n"
                    f"Teléfono: {row['telefono'] or '—'}\nPlaca: {row['placa']}")
            self._notificar("info", "Residente encontrado", info)
        else:
            self._notificar("aviso", "No registrado", f"Placa {placa} no encontrada en residentes activos")

    # ── REPORTES PDF ──────────────────────────────────────────────────────────

    def _ir_reportes(self):
        self._limpiar_contenido()
        self.current_page = "Reportes PDF"
        self._label_seccion(self.contenido, "Generación de Reportes")

        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)

        opciones = ctk.CTkFrame(card, fg_color="transparent")
        opciones.pack(pady=20, padx=30, fill="x")

        ctk.CTkLabel(opciones, text="Fecha inicio:", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).grid(row=0, column=0, sticky="e", padx=(0,12), pady=8)
        self._rep_fecha_ini = self._entrada(opciones, placeholder="YYYY-MM-DD", width=200)
        self._rep_fecha_ini.grid(row=0, column=1, sticky="w")
        self._rep_fecha_ini.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(opciones, text="Fecha fin:", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).grid(row=1, column=0, sticky="e", padx=(0,12), pady=8)
        self._rep_fecha_fin = self._entrada(opciones, placeholder="YYYY-MM-DD", width=200)
        self._rep_fecha_fin.grid(row=1, column=1, sticky="w")
        self._rep_fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(opciones, text="Tipo:", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).grid(row=2, column=0, sticky="e", padx=(0,12), pady=8)
        self._rep_tipo = ctk.CTkComboBox(opciones, values=["Todos", "residente", "visitante"], width=200)
        self._rep_tipo.grid(row=2, column=1, sticky="w")

        self._boton(card, "📄  Generar PDF", self._generar_pdf,
                    color="#1d4ed8", hover="#1e40af", width=260).pack(pady=20)

    def _generar_pdf(self):
        fecha_ini = self._rep_fecha_ini.get().strip()
        fecha_fin = self._rep_fecha_fin.get().strip()
        tipo      = self._rep_tipo.get()

        try:
            datetime.strptime(fecha_ini, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            self._notificar("error", "Fecha inválida", "Use el formato YYYY-MM-DD")
            return

        nombre_pdf = f"reporte_{fecha_ini}_a_{fecha_fin}.pdf"
        doc = SimpleDocTemplate(nombre_pdf, pagesize=letter,
                                leftMargin=36, rightMargin=36,
                                topMargin=48, bottomMargin=36)
        estilos = getSampleStyleSheet()
        elementos = []

        titulo = Paragraph(
            f"<b>ResiControl — Reporte de Accesos</b><br/>{fecha_ini} al {fecha_fin}",
            estilos["Title"],
        )
        elementos.append(titulo)
        elementos.append(Spacer(1, 16))
        elementos.append(Paragraph(f"Generado por: {self.current_user}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                   estilos["Normal"]))
        elementos.append(Spacer(1, 20))

        query = """
            SELECT tipo, nombre, cedula, placa, entrada, salida, operador
            FROM accesos
            WHERE DATE(entrada) BETWEEN ? AND ?
        """
        params: list = [fecha_ini, fecha_fin]
        if tipo != "Todos":
            query += " AND tipo=?"
            params.append(tipo)
        query += " ORDER BY entrada DESC"

        self.cursor.execute(query, params)
        filas = self.cursor.fetchall()

        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador"]
        datos_tabla = [encabezados]
        for row in filas:
            datos_tabla.append([str(v or "—") for v in row])

        tabla = Table(datos_tabla, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("FONTSIZE",   (0, 1), (-1, -1), 8),
            ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING",    (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla)

        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph(f"Total de registros: {len(filas)}", estilos["Normal"]))

        doc.build(elementos)
        abrir_archivo(nombre_pdf)
        self._notificar("ok", "PDF generado", f"Archivo: {nombre_pdf}\n{len(filas)} registros")

    # ── GESTIÓN DE USUARIOS (solo admin) ──────────────────────────────────────

    def _ir_usuarios(self):
        if self.rol != "admin":
            return
        self._limpiar_contenido()
        self.current_page = "Usuarios"
        self._label_seccion(self.contenido, "Gestión de Usuarios")

        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")

        campos_usr = [("Usuario *", "Nuevo usuario"), ("Contraseña *", "Contraseña")]
        self._usr_ent: dict[str, ctk.CTkEntry] = {}
        for i, (lbl, hint) in enumerate(campos_usr):
            ctk.CTkLabel(form, text=lbl, font=("Segoe UI", 13),
                         text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0,16), pady=8)
            e = self._entrada(form, placeholder=hint, width=320,
                              show="*" if "aseña" in lbl else "")
            e.grid(row=i, column=1, sticky="w")
            self._usr_ent[lbl] = e

        ctk.CTkLabel(form, text="Rol *", font=("Segoe UI", 13),
                     text_color=COLORES["texto_2"]).grid(row=2, column=0, sticky="e", padx=(0,16), pady=8)
        self._usr_rol = ctk.CTkComboBox(form, values=["admin", "operador", "residente"], width=320)
        self._usr_rol.grid(row=2, column=1, sticky="w")

        self._boton(card, "➕  Crear Usuario", self._crear_usuario, width=220).pack(pady=12)

        # Lista
        ctk.CTkLabel(self.contenido, text="Usuarios existentes", font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(16, 4))

        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                       corner_radius=12, height=240)
        lista.pack(fill="x", padx=40, pady=(0, 24))

        fila_h = ctk.CTkFrame(lista, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in ["ID", "Usuario", "Rol", "Acciones"]:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=8, pady=8)

        self.cursor.execute("SELECT id, usuario, rol FROM usuarios ORDER BY usuario")
        for i, row in enumerate(self.cursor.fetchall()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for val in [row["id"], row["usuario"], row["rol"]]:
                ctk.CTkLabel(f, text=str(val), font=("Segoe UI", 12),
                             text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=8, pady=6)
            uid = row["id"]
            if row["usuario"] != "admin":
                ctk.CTkButton(f, text="Eliminar", width=80, height=28,
                              fg_color=COLORES["rojo"], hover_color=COLORES["rojo_hover"],
                              font=("Segoe UI", 11), corner_radius=6,
                              command=lambda i=uid: self._eliminar_usuario(i)).pack(side="left", padx=8)

    def _crear_usuario(self):
        usuario = self._usr_ent["Usuario *"].get().strip()
        pwd     = self._usr_ent["Contraseña *"].get().strip()
        rol     = self._usr_rol.get()

        if not usuario or not pwd:
            self._notificar("error", "Error", "Usuario y contraseña son obligatorios")
            return
        if len(pwd) < 4:
            self._notificar("error", "Contraseña débil", "La contraseña debe tener al menos 4 caracteres")
            return

        try:
            self.cursor.execute(
                "INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,?)",
                (usuario, hash_password(pwd), rol),
            )
            self.conn.commit()
            self._notificar("ok", "Éxito", f"Usuario '{usuario}' creado con rol {rol}")
            self._ir_usuarios()
        except sqlite3.IntegrityError:
            self._notificar("error", "Error", f"El usuario '{usuario}' ya existe")

    def _eliminar_usuario(self, uid: int):
        res = CTkMessagebox(title="Confirmar", message="¿Eliminar este usuario?",
                            icon="warning", option_1="Sí", option_2="Cancelar")
        if res.get() == "Sí":
            self.cursor.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            self.conn.commit()
            self._ir_usuarios()

    # ── BORRAR DATOS (admin) ──────────────────────────────────────────────────

    def _ir_borrar(self):
        if self.rol != "admin":
            return
        self._limpiar_contenido()
        self._label_seccion(self.contenido, "Borrar Datos de Prueba")

        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=80, pady=24)

        ctk.CTkLabel(card,
                     text="Esta acción eliminará TODOS los accesos, residentes e incidentes.\n"
                          "Los usuarios y los parqueaderos NO se borran.\n\n¿Estás seguro?",
                     font=("Segoe UI", 15), text_color=COLORES["texto_2"], justify="center").pack(pady=30)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=20)
        self._boton(fila, "🗑  SÍ, BORRAR TODO", self._ejecutar_borrado,
                    color=COLORES["rojo"], hover=COLORES["rojo_hover"], width=260).pack(side="left", padx=20)
        self._boton(fila, "Cancelar", self._ir_inicio,
                    color=COLORES["gris"], hover="#4b5563", width=180).pack(side="left", padx=20)

    def _ejecutar_borrado(self):
        self.cursor.executescript("""
            DELETE FROM accesos;
            DELETE FROM residentes;
            DELETE FROM incidentes;
            UPDATE parqueaderos SET estado='libre', placa=NULL, desde=NULL;
        """)
        self.conn.commit()
        self._notificar("ok", "Listo", "Datos borrados correctamente")
        self._ir_inicio()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ResiControl()
    app.mainloop()