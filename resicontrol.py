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

from config import COLORES, TOTAL_PARQUEADEROS, QR_DIR, BCRYPT_ROUNDS, DB_PATH
from auth import (
    hash_password,
    verify_password,
    needs_rehash,
    check_lockout,
    record_failed_attempt,
    reset_failed_attempts,
    get_failed_attempts,
    validate_password_strength,
)
from validators import (
    validate_email,
    validate_cedula,
    validate_placa,
    validate_phone,
    validate_unidad,
    validate_required,
)
from database import (
    create_tables,
    create_indexes,
    add_audit_columns,
    seed_parqueaderos,
    insert_default_users,
)
from models import (
    crear_usuario,
    verificar_usuario,
    obtener_usuarios,
    eliminar_usuario,
    crear_residente,
    obtener_residentes,
    obtener_residente,
    editar_residente,
    eliminar_residente,
    registrar_entrada_visitante,
    registrar_salida_visitante,
    registrar_entrada_residente,
    obtener_visitantes_activos,
    obtener_historial,
    editar_acceso,
    obtener_parqueaderos_resumen,
    obtener_parqueaderos_por_tipo,
    obtener_parqueaderos_libres_visitante,
    asignar_parqueadero,
    liberar_parqueadero,
    registrar_incidente,
    obtener_incidentes,
    obtener_metricas,
)
from backup import crear_backup, restaurar_backup, get_backups_list, iniciar_scheduler
from qr_manager import (
    generar_qr,
    escanear_qr,
    buscar_residente_por_placa,
    get_qr_path,
    abrir_archivo as abrir_archivo_qr,
)
from report_generator import generar_pdf, generar_csv
from logger import logger


# ── Intentar importar librerías opcionales ────────────────────────────────────
try:
    import qrcode as qrcode_lib
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


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════


class ResiControl(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ResiControl — Gestión de Seguridad Residencial")
        self.geometry("1300x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORES["fondo"])

        self.current_user: str | None = None
        self.rol: str | None = None
        self.current_page: str | None = None

        self.cap = None
        self.scanning = False
        self.video_label = None

        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        create_tables(self.cursor)
        create_indexes(self.cursor)
        add_audit_columns(self.cursor)
        self.conn.commit()
        seed_parqueaderos(self.cursor)
        self.conn.commit()
        insert_default_users(self.cursor, hash_password)
        self.conn.commit()

        iniciar_scheduler()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.mostrar_login()

    def _limpiar(self):
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
            parent, text=texto, font=("Segoe UI", 26, "bold"), text_color=COLORES["texto"]
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
            parent,
            text=texto,
            command=comando,
            fg_color=color,
            hover_color=hover,
            corner_radius=10,
            height=46,
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

        frame = ctk.CTkFrame(
            self, corner_radius=20, fg_color=COLORES["panel"],
            border_width=1, border_color=COLORES["borde"],
        )
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        ctk.CTkLabel(frame, text="ResiControl", font=("Helvetica", 38, "bold"),
                      text_color="#00aaff").pack(pady=(32, 4))
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

        self._fortaleza_lbl = ctk.CTkLabel(
            frame, text="", font=("Segoe UI", 11), text_color=COLORES["texto_3"]
        )
        self._fortaleza_lbl.pack(anchor="w", padx=40)
        self.pwd_entry.bind("<KeyRelease>", self._mostrar_fortaleza)

        self._boton(frame, "Iniciar Sesión", self.login, width=360).pack(pady=28)

        self.error_lbl = ctk.CTkLabel(
            frame, text="", text_color=COLORES["rojo"], font=("Segoe UI", 13)
        )
        self.error_lbl.pack()

        self.user_entry.bind("<Return>", lambda _: self.login())
        self.pwd_entry.bind("<Return>", lambda _: self.login())
        self.user_entry.focus_set()

    def _mostrar_fortaleza(self, event=None):
        pwd = self.pwd_entry.get()
        if not pwd:
            self._fortaleza_lbl.configure(text="")
            return
        ok, msg = validate_password_strength(pwd)
        color = COLORES["verde"] if ok else COLORES["rojo"]
        icono = "✓" if ok else "⚠"
        self._fortaleza_lbl.configure(text=f"{icono} {msg}", text_color=color)

    def login(self):
        usuario = self.user_entry.get().strip()
        pwd = self.pwd_entry.get().strip()

        if not usuario or not pwd:
            self.error_lbl.configure(text="Complete todos los campos")
            return

        bloqueado, restante = check_lockout(usuario)
        if bloqueado:
            self.error_lbl.configure(text=f"Cuenta bloqueada. Intente en {restante}s")
            return

        user_data = verificar_usuario(usuario, pwd, verify_password)

        if user_data:
            self.current_user = usuario
            self.rol = user_data["rol"]
            reset_failed_attempts(usuario)
            self._migrar_hash_si_es_necesario(usuario, pwd)
            logger.info(f"Login exitoso: {usuario} (rol={self.rol})")
            self.mostrar_dashboard()
        else:
            record_failed_attempt(usuario)
            intentos = get_failed_attempts(usuario)
            restantes = 5 - intentos
            if restantes > 0:
                self.error_lbl.configure(
                    text=f"Usuario o contraseña incorrectos ({restantes} intentos restantes)"
                )
            else:
                self.error_lbl.configure(text="Cuenta bloqueada temporalmente")

    def _migrar_hash_si_es_necesario(self, usuario: str, pwd_plano: str):
        row = self.conn.execute(
            "SELECT password FROM usuarios WHERE usuario=?", (usuario,)
        ).fetchone()
        if row and needs_rehash(row["password"]):
            nuevo_hash = hash_password(pwd_plano)
            self.conn.execute(
                "UPDATE usuarios SET password=? WHERE usuario=?", (nuevo_hash, usuario)
            )
            self.conn.commit()
            logger.info(f"Hash migrado a bcrypt: {usuario}")

    # ── DASHBOARD ─────────────────────────────────────────────────────────────

    def mostrar_dashboard(self):
        self._limpiar()
        self.geometry("1300x820")
        self.resizable(True, True)

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORES["panel"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="ResiControl", font=("Helvetica", 24, "bold"),
                      text_color="#00aaff").pack(pady=(32, 4), padx=20)
        ctk.CTkLabel(self.sidebar, text=f"{self.rol.upper()}", font=("Segoe UI", 11),
                      text_color=COLORES["texto_3"]).pack()
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORES["borde"]).pack(fill="x", pady=16, padx=20)

        menu = [
            ("Inicio", "🏠", self._ir_inicio),
            ("Visitantes", "🚪", self._ir_visitantes),
            ("Residentes", "👤", self._ir_residentes),
            ("Parqueaderos", "🚗", self._ir_parqueaderos),
            ("Historial", "📜", self._ir_historial),
            ("Incidentes", "⚠️", self._ir_incidentes),
            ("Reportes PDF", "📄", self._ir_reportes),
        ]
        if self.rol == "admin":
            menu.append(("Usuarios", "🔑", self._ir_usuarios))
            menu.append(("Borrar datos", "🗑️", self._ir_borrar))
        if CAMARA_DISPONIBLE:
            menu.insert(3, ("Escaneo QR", "🔍", self._ir_qr))
        menu.append(("Respaldos", "💾", self._ir_backups))
        menu.append(("Cerrar Sesión", "↩", self.mostrar_login))

        self.menu_btns: dict[str, ctk.CTkButton] = {}
        for texto, icono, cmd in menu:
            es_peligro = texto in ("Cerrar Sesión", "Borrar datos")
            fg = COLORES["rojo"] if es_peligro else "transparent"
            hover = COLORES["rojo_hover"] if es_peligro else "#1f2937"
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icono}  {texto}", fg_color=fg, hover_color=hover,
                anchor="w", height=52, corner_radius=0, font=("Segoe UI", 13),
                text_color=COLORES["texto_2"],
                command=lambda t=texto, c=cmd: self._cambiar_pagina(t, c),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.menu_btns[texto] = btn

        self.contenido = ctk.CTkScrollableFrame(self, fg_color="#0f172a")
        self.contenido.pack(side="right", fill="both", expand=True)
        self._ir_inicio()

    def _cambiar_pagina(self, nombre: str, accion):
        self._detener_camara()
        for t, btn in self.menu_btns.items():
            es_peligro = t in ("Cerrar Sesión", "Borrar datos")
            btn.configure(fg_color=(COLORES["rojo"] if es_peligro else "#1e293b")
                          if t == nombre else (COLORES["rojo"] if es_peligro else "transparent"))
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
        cab = ctk.CTkFrame(self.contenido, fg_color="#1e293b", height=70, corner_radius=0)
        cab.pack(fill="x")
        ctk.CTkLabel(cab, text=f"Bienvenido, {self.current_user.upper()}",
                      font=("Segoe UI", 22, "bold"), text_color="#00aaff").pack(pady=18)
        self._renderizar_metricas()

        sec = self._tarjeta(self.contenido)
        sec.pack(fill="x", padx=32, pady=(0, 24))
        sec.pack_propagate(False)
        sec.configure(height=108)
        ctk.CTkLabel(sec, text="Accesos rápidos", font=("Segoe UI", 13, "bold"),
                      text_color=COLORES["texto_3"]).pack(anchor="w", padx=20, pady=(8, 4))
        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(padx=16)
        for etiqueta, color, cmd in [
            ("🚪 Visitantes", COLORES["azul"], self._ir_visitantes),
            ("👤 Residentes", "#2563eb", self._ir_residentes),
            ("🚗 Parqueaderos", COLORES["verde"], self._ir_parqueaderos),
            ("📜 Historial", COLORES["amarillo"], self._ir_historial),
            ("📄 Reporte", "#1d4ed8", self._ir_reportes),
        ]:
            ctk.CTkButton(fila, text=etiqueta, width=160, height=44, corner_radius=10,
                          fg_color=color, hover_color="#1e40af", font=("Segoe UI", 12, "bold"),
                          text_color="#fff", command=cmd).pack(side="left", padx=8)

    def _renderizar_metricas(self):
        if hasattr(self, "_metricas_frame"):
            self._metricas_frame.destroy()
        self._metricas_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        self._metricas_frame.pack(fill="x", padx=32, pady=(24, 16))
        m = obtener_metricas()
        datos = [
            ("Entradas hoy", str(m["entradas_hoy"]), "↑", "#22c55e"),
            ("Residentes", str(m["residentes"]), "👥", COLORES["azul"]),
            ("Parqueaderos oc.", "🚗 " + str(m["ocupados"]), "🚗", COLORES["amarillo"]),
            ("Dentro ahora", str(m["dentro"]), "🔴", COLORES["rojo"]),
        ]
        for titulo, valor, icono, color in datos:
            card = ctk.CTkFrame(self._metricas_frame, fg_color=COLORES["tarjeta"],
                                 corner_radius=14, border_width=1, border_color=COLORES["borde"])
            card.pack(side="left", expand=True, padx=10, fill="both")
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 4))
            ctk.CTkLabel(top, text=titulo, font=("Segoe UI", 12, "bold"),
                         text_color=COLORES["texto_3"]).pack(side="left")
            ctk.CTkLabel(top, text=icono, font=("Segoe UI", 16), text_color=color).pack(side="right")
            ctk.CTkLabel(card, text=valor, font=("Segoe UI", 30, "bold"),
                         text_color=COLORES["texto"]).pack(pady=(4, 14))
        if self.current_page == "Inicio":
            self.after(10000, self._renderizar_metricas)

    # ── VISITANTES ─────────────────────────────────────────────────────────────

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
            ("Cédula *", "Ej: 1234567890", False),
            ("Placa (opcional)", "Ej: ABC123", False),
            ("Invitado por (unidad) *", "Ej: 301", False),
        ]
        self._vis_entradas: dict[str, ctk.CTkEntry] = {}
        for i, (label, hint, oculto) in enumerate(campos):
            ctk.CTkLabel(form, text=label, font=("Segoe UI", 13),
                          text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0, 16), pady=8)
            e = self._entrada(form, placeholder=hint, width=420, show="*" if oculto else "")
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._vis_entradas[label] = e

        self._vis_consent = ctk.CTkCheckBox(
            card, text="Autorizo el tratamiento de datos personales (Ley 1581/2012)",
            font=("Segoe UI", 12), text_color=COLORES["texto_2"])
        self._vis_consent.pack(pady=12)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=16)
        self._boton(fila, "✅  Registrar Entrada", self._registrar_entrada_vis, width=220).pack(side="left", padx=12)
        self._boton(fila, "🚪  Registrar Salida", self._registrar_salida_vis,
                     color=COLORES["rojo"], hover=COLORES["rojo_hover"], width=220).pack(side="left", padx=12)

        ctk.CTkLabel(self.contenido, text="Visitantes actualmente dentro",
                      font=("Segoe UI", 15, "bold"), text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(8, 4))
        self._tabla_visitantes_activos()

    def _tabla_visitantes_activos(self):
        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"], corner_radius=12, height=200)
        lista.pack(fill="x", padx=40, pady=(0, 24))
        encabezados = ["Nombre", "Cédula", "Placa", "Unidad", "Entrada", "Operador", "Acciones"]
        fila_h = ctk.CTkFrame(lista, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                          text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=8, pady=8)
        for i, fila_data in enumerate(obtener_visitantes_activos()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for key in ["nombre", "cedula", "placa", "unidad", "entrada", "operador"]:
                ctk.CTkLabel(f, text=str(fila_data.get(key, "—") or "—"), font=("Segoe UI", 12),
                              text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=8, pady=6)
            ctk.CTkButton(f, text="✏️", width=36, height=28, corner_radius=6,
                          fg_color=COLORES["amarillo"], hover_color="#ca8a04", font=("Segoe UI", 12),
                          command=lambda d=fila_data: self._editar_vis_dialog(d)).pack(side="left", padx=4, pady=4)

    def _editar_vis_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Visitante")
        dialog.geometry("420x340")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="Editar datos del visitante", font=("Segoe UI", 16, "bold"),
                      text_color=COLORES["texto"]).pack(pady=(16, 8))
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")
        lbl_nombre = ctk.CTkLabel(frame, text="Nombre:", font=("Segoe UI", 12))
        lbl_nombre.grid(row=0, column=0, sticky="w", pady=6)
        ent_nombre = self._entrada(frame, placeholder="Nombre", width=280)
        ent_nombre.grid(row=0, column=1, pady=6, padx=(8, 0))
        ent_nombre.insert(0, str(datos.get("nombre", "") or ""))
        lbl_cedula = ctk.CTkLabel(frame, text="Cédula:", font=("Segoe UI", 12))
        lbl_cedula.grid(row=1, column=0, sticky="w", pady=6)
        ent_cedula = self._entrada(frame, placeholder="Cédula", width=280)
        ent_cedula.grid(row=1, column=1, pady=6, padx=(8, 0))
        ent_cedula.insert(0, str(datos.get("cedula", "") or ""))
        lbl_placa = ctk.CTkLabel(frame, text="Placa:", font=("Segoe UI", 12))
        lbl_placa.grid(row=2, column=0, sticky="w", pady=6)
        ent_placa = self._entrada(frame, placeholder="Placa", width=280)
        ent_placa.grid(row=2, column=1, pady=6, padx=(8, 0))
        ent_placa.insert(0, str(datos.get("placa", "") or ""))

        def guardar():
            nombre = ent_nombre.get().strip()
            cedula = ent_cedula.get().strip()
            placa = ent_placa.get().strip()
            if not nombre or not cedula:
                CTkMessagebox(title="Error", message="Nombre y cédula son obligatorios", icon="cancel")
                return
            acc_id = datos.get("id")
            if acc_id is None:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT id FROM accesos WHERE cedula=? AND salida IS NULL AND tipo='visitante'",
                    (cedula,)).fetchone()
                conn.close()
                acc_id = row["id"] if row else 0
            exito, msg = editar_acceso(acc_id, nombre, cedula, placa, self.current_user)
            self._notificar("ok" if exito else "error", "Editar Visitante", msg)
            if exito:
                dialog.destroy()
                self._ir_visitantes()

        self._boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=16)

    def _registrar_entrada_vis(self):
        if not self._vis_consent.get():
            self._notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return
        nombre = self._vis_entradas["Nombre completo *"].get().strip()
        cedula = self._vis_entradas["Cédula *"].get().strip()
        placa = self._vis_entradas["Placa (opcional)"].get().strip().upper()
        unidad = self._vis_entradas["Invitado por (unidad) *"].get().strip()
        if not validate_required(nombre, "Nombre")[0]:
            self._notificar("error", "Error", "Nombre es obligatorio")
            return
        if not validate_cedula(cedula):
            self._notificar("error", "Error", "Cédula inválida o vacía")
            return
        if not validate_unidad(unidad)[0]:
            self._notificar("error", "Error", "Unidad es obligatoria")
            return
        if placa and not validate_placa(placa):
            self._notificar("error", "Error", "Formato de placa inválido (ej: ABC123)")
            return
        exito, msg = registrar_entrada_visitante(nombre, cedula, placa, unidad, self.current_user)
        self._notificar("ok" if exito else "error", "Registro", msg)
        if exito:
            self._ir_visitantes()

    def _registrar_salida_vis(self):
        cedula = self._vis_entradas["Cédula *"].get().strip()
        placa = self._vis_entradas["Placa (opcional)"].get().strip().upper()
        if not cedula and not placa:
            self._notificar("aviso", "Atención", "Ingrese cédula o placa para registrar salida")
            return
        exito, msg = registrar_salida_visitante(cedula, placa, self.current_user)
        self._notificar("ok" if exito else "aviso", "Salida", msg)
        if exito:
            self._ir_visitantes()

    # ── RESIDENTES ──────────────────────────────────────────────────────────────

    def _ir_residentes(self):
        self._limpiar_contenido()
        self.current_page = "Residentes"
        self._label_seccion(self.contenido, "Gestión de Residentes")
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
            b = ctk.CTkButton(tab_frame, text=nombre, width=200, height=40, corner_radius=8,
                               font=("Segoe UI", 13), fg_color=COLORES["tarjeta"],
                               hover_color=COLORES["borde"], command=lambda k=clave: cambiar_tab(k))
            b.pack(side="left", padx=6)
            tab_btns[clave] = b
        cambiar_tab("nuevo")

    def _form_nuevo_residente(self):
        card = self._tarjeta(self._tab_content)
        card.pack(fill="x", padx=40, pady=12)
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")
        campos = [("Unidad *", "Ej: 301"), ("Nombre completo *", "Ej: María López"),
                  ("Teléfono", "Ej: 3001234567"), ("Email", "Ej: maria@correo.com"), ("Placa *", "Ej: XYZ789")]
        self._res_entradas: dict[str, ctk.CTkEntry] = {}
        for i, (label, hint) in enumerate(campos):
            ctk.CTkLabel(form, text=label, font=("Segoe UI", 13),
                          text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0, 16), pady=8)
            e = self._entrada(form, placeholder=hint, width=420)
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._res_entradas[label] = e
        self._res_consent = ctk.CTkCheckBox(
            card, text="Autorizo tratamiento de datos (Ley 1581/2012)",
            font=("Segoe UI", 12), text_color=COLORES["texto_2"])
        self._res_consent.pack(pady=12)
        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=16)
        self._boton(fila, "👤  Registrar Residente", self._registrar_residente,
                     color=COLORES["verde"], hover=COLORES["verde_hover"], width=240).pack(side="left", padx=12)
        if QR_DISPONIBLE:
            self._boton(fila, "🔲  Generar QR", self._generar_qr,
                         color=COLORES["amarillo"], hover="#ca8a04", width=180).pack(side="left", padx=12)

    def _validar_residente(self, unidad, nombre, placa, email, telefono):
        if not validate_unidad(unidad)[0]:
            return False, "Unidad es obligatoria"
        if not validate_required(nombre, "Nombre")[0]:
            return False, "Nombre es obligatorio"
        if not validate_placa(placa):
            return False, "Formato de placa inválido (ej: ABC123)"
        if email and not validate_email(email):
            return False, "Formato de email inválido"
        if telefono and not validate_phone(telefono):
            return False, "Formato de teléfono inválido (7-10 dígitos)"
        return True, ""

    def _registrar_residente(self):
        if not self._res_consent.get():
            self._notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return
        unidad = self._res_entradas["Unidad *"].get().strip()
        nombre = self._res_entradas["Nombre completo *"].get().strip()
        placa = self._res_entradas["Placa *"].get().strip().upper()
        tel = self._res_entradas["Teléfono"].get().strip()
        email = self._res_entradas["Email"].get().strip()
        ok, msg = self._validar_residente(unidad, nombre, placa, email, tel)
        if not ok:
            self._notificar("error", "Error de validación", msg)
            return
        exito, msg = crear_residente(unidad, nombre, tel, email, placa)
        self._notificar("ok" if exito else "error", "Registro", msg)
        if exito:
            self._ir_residentes()

    def _generar_qr(self):
        if not QR_DISPONIBLE:
            self._notificar("error", "No disponible", "Librería qrcode no instalada")
            return
        placa = self._res_entradas["Placa *"].get().strip().upper()
        if not placa:
            self._notificar("error", "Error", "Ingrese la placa primero")
            return
        ok, msg = generar_qr(placa)
        self._notificar("ok" if ok else "error", "QR" if ok else "Error", msg)

    def _lista_residentes(self):
        card = self._tarjeta(self._tab_content)
        card.pack(fill="both", padx=40, pady=12, expand=True)
        buscador_frame = ctk.CTkFrame(card, fg_color="transparent")
        buscador_frame.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(buscador_frame, text="Buscar:", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).pack(side="left", padx=(0, 10))
        self._busq_res = self._entrada(buscador_frame, placeholder="Nombre, unidad o placa…", width=360)
        self._busq_res.pack(side="left")
        self._boton(buscador_frame, "🔍 Buscar", self._buscar_residentes, width=120).pack(side="left", padx=10)
        self._tabla_res = ctk.CTkScrollableFrame(card, fg_color="#111827", corner_radius=8)
        self._tabla_res.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._renderizar_tabla_residentes()

    def _renderizar_tabla_residentes(self, filtro=""):
        for w in self._tabla_res.winfo_children():
            w.destroy()
        encabezados = ["ID", "Unidad", "Nombre", "Teléfono", "Email", "Placa", "QR", "Acciones"]
        fila_h = ctk.CTkFrame(self._tabla_res, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                          text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=6, pady=8)
        for i, row in enumerate(obtener_residentes(filtro)):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._tabla_res, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for key in ["id", "unidad", "nombre", "telefono", "email", "placa"]:
                val = row.get(key)
                texto = str(val or "—")
                if key == "telefono" and val:
                    texto = f"📱 {texto}"
                ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12),
                              text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=6, pady=6)
            qr_path = row.get("qr_code") or ""
            qr_texto = "📷 Sí" if qr_path and os.path.exists(qr_path) else "—"
            ctk.CTkLabel(f, text=qr_texto, font=("Segoe UI", 12),
                          text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=6, pady=6)
            frame_acc = ctk.CTkFrame(f, fg_color="transparent")
            frame_acc.pack(side="left", padx=4)
            rid = row["id"]
            ctk.CTkButton(frame_acc, text="✏️", width=36, height=28, corner_radius=6,
                          fg_color=COLORES["azul"], hover_color=COLORES["azul_hover"], font=("Segoe UI", 12),
                          command=lambda r=row: self._editar_residente_dialog(r)).pack(side="left", padx=2)
            ctk.CTkButton(frame_acc, text="🗑", width=36, height=28, corner_radius=6,
                          fg_color=COLORES["rojo"], hover_color=COLORES["rojo_hover"], font=("Segoe UI", 12),
                          command=lambda i=rid: self._eliminar_residente(i)).pack(side="left", padx=2)

    def _editar_residente_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Residente")
        dialog.geometry("450x400")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=f"Editar: {datos.get('nombre', '')}",
                      font=("Segoe UI", 16, "bold"), text_color=COLORES["texto"]).pack(pady=(16, 8))
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")
        campos_def = [("Unidad *", "unidad", datos.get("unidad", "")),
                       ("Nombre *", "nombre", datos.get("nombre", "")),
                       ("Teléfono", "telefono", datos.get("telefono", "") or ""),
                       ("Email", "email", datos.get("email", "") or ""),
                       ("Placa *", "placa", datos.get("placa", ""))]
        entradas = {}
        for i, (label, key, val_actual) in enumerate(campos_def):
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).grid(row=i, column=0, sticky="w", pady=6)
            e = self._entrada(frame, placeholder=label, width=280)
            e.grid(row=i, column=1, pady=6, padx=(8, 0))
            e.insert(0, str(val_actual))
            entradas[key] = (e, label)

        def guardar():
            unidad = entradas["unidad"][0].get().strip()
            nombre = entradas["nombre"][0].get().strip()
            telefono = entradas["telefono"][0].get().strip()
            email = entradas["email"][0].get().strip()
            placa = entradas["placa"][0].get().strip().upper()
            ok, msg = self._validar_residente(unidad, nombre, placa, email, telefono)
            if not ok:
                self._notificar("error", "Validación", msg)
                return
            exito, msg = editar_residente(datos["id"], unidad, nombre, telefono, email, placa)
            self._notificar("ok" if exito else "error", "Editar Residente", msg)
            if exito:
                dialog.destroy()
                self._ir_residentes()

        self._boton(dialog, "Guardar Cambios", guardar, color=COLORES["verde"]).pack(pady=16)

    def _buscar_residentes(self):
        self._renderizar_tabla_residentes(self._busq_res.get().strip())

    def _eliminar_residente(self, rid: int):
        res = CTkMessagebox(title="Confirmar", message="¿Eliminar este residente?",
                             icon="warning", option_1="Sí, eliminar", option_2="Cancelar")
        if res.get() == "Sí, eliminar":
            eliminar_residente(rid)
            self._renderizar_tabla_residentes()

    # ── PARQUEADEROS ────────────────────────────────────────────────────────────

    def _ir_parqueaderos(self):
        self._limpiar_contenido()
        self.current_page = "Parqueaderos"
        self._label_seccion(self.contenido, "Parqueaderos")
        self._renderizar_parqueaderos()

    def _renderizar_parqueaderos(self):
        res = obtener_parqueaderos_resumen()
        res_frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        res_frame.pack(fill="x", padx=40, pady=(0, 16))
        for titulo, valor, color in [
            ("Residentes libres", str(res["libres_residente"]), "#22c55e"),
            ("Visitantes libres", str(res["libres_visitante"]), COLORES["azul"]),
            ("Ocupados", str(res["ocupados"]), COLORES["rojo"])]:
            c = ctk.CTkFrame(res_frame, fg_color=COLORES["tarjeta"], corner_radius=12,
                              border_width=1, border_color=COLORES["borde"])
            c.pack(side="left", expand=True, padx=10, fill="both")
            ctk.CTkLabel(c, text=titulo, font=("Segoe UI", 12), text_color=COLORES["texto_3"]
                         ).pack(pady=(12, 2))
            ctk.CTkLabel(c, text=valor, font=("Segoe UI", 28, "bold"), text_color=color
                         ).pack(pady=(0, 12))
        ctk.CTkLabel(self.contenido, text="Residentes", font=("Segoe UI", 14, "bold"),
                      text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(8, 4))
        self._grid_parqueaderos("residente")
        ctk.CTkLabel(self.contenido, text="Visitantes", font=("Segoe UI", 14, "bold"),
                      text_color=COLORES["texto_3"]).pack(anchor="w", padx=44, pady=(16, 4))
        self._grid_parqueaderos("visitante")
        sec = self._tarjeta(self.contenido)
        sec.pack(fill="x", padx=40, pady=16)
        ctk.CTkLabel(sec, text="Asignar parqueadero a visitante",
                      font=("Segoe UI", 14, "bold"), text_color=COLORES["texto"]
                      ).pack(anchor="w", padx=20, pady=(14, 6))
        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 16))
        self._park_placa = self._entrada(fila, placeholder="Placa del vehículo", width=220)
        self._park_placa.pack(side="left", padx=(0, 12))
        self._park_numero = ctk.CTkComboBox(
            fila, width=160, values=obtener_parqueaderos_libres_visitante())
        self._park_numero.pack(side="left", padx=(0, 12))
        self._boton(fila, "Asignar", self._asignar_parqueadero, width=140).pack(side="left")

    def _grid_parqueaderos(self, tipo: str):
        filas = obtener_parqueaderos_por_tipo(tipo)
        grid = ctk.CTkFrame(self.contenido, fg_color="transparent")
        grid.pack(padx=44, pady=4, fill="x")
        cols = 10
        for idx, row in enumerate(filas):
            col = idx % cols
            fila_idx = idx // cols
            color = "#22c55e" if row["estado"] == "libre" else COLORES["rojo"]
            texto = row["numero"]
            btn = ctk.CTkButton(grid, text=texto, width=72, height=56, corner_radius=10,
                                 fg_color=color, hover_color="#1e3a5f", font=("Segoe UI", 12, "bold"),
                                 text_color="#fff",
                                 command=lambda p=row["numero"], s=row["estado"], pl=row["placa"]:
                                 self._accion_parqueadero(p, s, pl))
            btn.grid(row=fila_idx, column=col, padx=5, pady=5)

    def _accion_parqueadero(self, numero: str, estado: str, placa: str | None):
        if estado == "ocupado":
            msg = f"Parqueadero {numero}\nPlaca: {placa or '—'}\n\n¿Liberar?"
            res = CTkMessagebox(title="Parqueadero ocupado", message=msg, icon="warning",
                                 option_1="Liberar", option_2="Cancelar")
            if res.get() == "Liberar":
                liberar_parqueadero(numero)
                self._ir_parqueaderos()
        else:
            self._notificar("info", "Parqueadero libre", f"{numero} está disponible")

    def _asignar_parqueadero(self):
        placa = self._park_placa.get().strip().upper()
        numero = self._park_numero.get().strip()
        if not placa or not numero or numero == "Sin espacio":
            self._notificar("error", "Error", "Ingrese placa y seleccione un parqueadero")
            return
        if not validate_placa(placa):
            self._notificar("error", "Error", "Formato de placa inválido")
            return
        exito, msg = asignar_parqueadero(numero, placa, self.current_user)
        self._notificar("ok" if exito else "aviso", "Asignación", msg)
        if exito:
            self._ir_parqueaderos()

    # ── HISTORIAL ───────────────────────────────────────────────────────────────

    def _ir_historial(self):
        self._limpiar_contenido()
        self.current_page = "Historial"
        self._label_seccion(self.contenido, "Historial de Accesos")
        filtros = ctk.CTkFrame(self.contenido, fg_color="transparent")
        filtros.pack(fill="x", padx=40, pady=8)
        self._hist_busq = self._entrada(
            filtros, placeholder="Buscar por nombre, cédula o placa…", width=340)
        self._hist_busq.pack(side="left", padx=(0, 10))
        self._hist_tipo = ctk.CTkComboBox(
            filtros, values=["Todos", "residente", "visitante"], width=160)
        self._hist_tipo.pack(side="left", padx=(0, 10))
        self._boton(filtros, "🔍 Filtrar", self._filtrar_historial, width=120).pack(side="left")
        self._boton(filtros, "📥 CSV", self._exportar_csv, width=100,
                     color="#6b7280").pack(side="left", padx=(10, 0))
        self._hist_frame = ctk.CTkScrollableFrame(
            self.contenido, fg_color=COLORES["tarjeta"], corner_radius=12, height=480)
        self._hist_frame.pack(fill="both", padx=40, pady=12, expand=True)
        self._renderizar_historial()

    def _renderizar_historial(self, busq="", tipo="Todos"):
        for w in self._hist_frame.winfo_children():
            w.destroy()
        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador", "Acciones"]
        fila_h = ctk.CTkFrame(self._hist_frame, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                          text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=6, pady=8)
        registros = obtener_historial(busq, tipo)
        for i, row in enumerate(registros):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._hist_frame, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            valores_visibles = [
                row.get("tipo", ""), row.get("nombre", ""), row.get("cedula", ""),
                row.get("placa", ""), row.get("entrada", ""), row.get("salida", ""),
                row.get("operador", "")]
            for val in valores_visibles:
                texto = str(val) if val is not None else "🟢 Activo"
                ctk.CTkLabel(f, text=texto, font=("Segoe UI", 12),
                             text_color=COLORES["texto_2"], wraplength=150
                             ).pack(side="left", expand=True, padx=6, pady=6)
            if row.get("salida") is None:
                ctk.CTkButton(f, text="✏️", width=36, height=28, corner_radius=6,
                              fg_color=COLORES["amarillo"], hover_color="#ca8a04",
                              font=("Segoe UI", 12),
                              command=lambda r=row: self._editar_historial_dialog(r)
                              ).pack(side="left", padx=4, pady=4)

    def _editar_historial_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Registro")
        dialog.geometry("400x280")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="Editar registro activo",
                      font=("Segoe UI", 16, "bold")).pack(pady=(16, 8))
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")
        lbls = [("Nombre:", "nombre", datos.get("nombre", "")),
                 ("Cédula:", "cedula", datos.get("cedula", "")),
                 ("Placa:", "placa", datos.get("placa", "") or "")]
        ents = {}
        for i, (label, key, val) in enumerate(lbls):
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).grid(
                row=i, column=0, sticky="w", pady=6)
            e = self._entrada(frame, placeholder=label, width=250)
            e.grid(row=i, column=1, pady=6, padx=(8, 0))
            e.insert(0, str(val))
            ents[key] = e

        def guardar():
            nombre = ents["nombre"].get().strip()
            cedula = ents["cedula"].get().strip()
            placa = ents["placa"].get().strip().upper()
            if not nombre or not cedula:
                self._notificar("error", "Error", "Nombre y cédula son obligatorios")
                return
            exito, msg = editar_acceso(
                datos["id"], nombre, cedula, placa, self.current_user)
            self._notificar("ok" if exito else "error", "Editar", msg)
            if exito:
                dialog.destroy()
                self._ir_historial()

        self._boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=16)

    def _filtrar_historial(self):
        self._renderizar_historial(
            self._hist_busq.get().strip(), self._hist_tipo.get())

    def _exportar_csv(self):
        busq = self._hist_busq.get().strip()
        fecha_ini = busq if busq else "2020-01-01"
        fecha_fin = busq if busq else datetime.now().strftime("%Y-%m-%d")
        ok, ruta = generar_csv(fecha_ini, fecha_fin, self._hist_tipo.get())
        if ok:
            abrir_archivo_qr(ruta)
        self._notificar("ok" if ok else "error", "Exportar CSV", ruta)

    # ── INCIDENTES ──────────────────────────────────────────────────────────────

    def _ir_incidentes(self):
        self._limpiar_contenido()
        self.current_page = "Incidentes"
        self._label_seccion(self.contenido, "Registro de Incidentes")
        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)
        ctk.CTkLabel(card, text="Descripción del incidente *",
                      font=("Segoe UI", 13), text_color=COLORES["texto_2"]
                      ).pack(anchor="w", padx=20, pady=(16, 4))
        self._inc_desc = ctk.CTkTextbox(card, height=120, font=("Segoe UI", 13),
                                         fg_color="#111827", corner_radius=8)
        self._inc_desc.pack(fill="x", padx=20)
        ctk.CTkLabel(card, text="Nivel de alerta", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).pack(anchor="w", padx=20, pady=(12, 4))
        self._inc_nivel = ctk.CTkComboBox(card, values=["bajo", "medio", "alto"], width=200)
        self._inc_nivel.pack(anchor="w", padx=20, pady=(0, 16))
        self._boton(card, "⚠️  Registrar Incidente", self._registrar_incidente,
                     color=COLORES["amarillo"], hover="#ca8a04").pack(pady=12)
        ctk.CTkLabel(self.contenido, text="Incidentes recientes",
                      font=("Segoe UI", 14, "bold"), text_color=COLORES["texto_3"]
                      ).pack(anchor="w", padx=44, pady=(16, 4))
        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                        corner_radius=12, height=280)
        lista.pack(fill="x", padx=40, pady=(0, 24))
        colores_nivel = {"bajo": "#22c55e", "medio": COLORES["amarillo"], "alto": COLORES["rojo"]}
        for i, row in enumerate(obtener_incidentes()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=2)
            color = colores_nivel.get(row["nivel"], COLORES["texto_3"])
            ctk.CTkLabel(f, text=f"[{row['nivel'].upper()}]", font=("Segoe UI", 11, "bold"),
                          text_color=color, width=70).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(f, text=row["descripcion"], font=("Segoe UI", 12),
                          text_color=COLORES["texto_2"], wraplength=500, justify="left"
                          ).pack(side="left", expand=True)
            ctk.CTkLabel(f, text=f"{row['operador']} — {row['fecha']}",
                          font=("Segoe UI", 11), text_color=COLORES["texto_3"]
                          ).pack(side="right", padx=12)

    def _registrar_incidente(self):
        desc = self._inc_desc.get("1.0", "end").strip()
        nivel = self._inc_nivel.get()
        if not validate_required(desc, "Descripción")[0]:
            self._notificar("error", "Error", "La descripción es obligatoria")
            return
        registrar_incidente(desc, nivel, self.current_user)
        self._notificar("ok", "Éxito", "Incidente registrado correctamente")
        self._ir_incidentes()

    # ── ESCANEO QR ──────────────────────────────────────────────────────────────

    def _ir_qr(self):
        if not CAMARA_DISPONIBLE:
            self._notificar("error", "No disponible", "cv2 y pyzbar no están instalados")
            return
        self._limpiar_contenido()
        self.current_page = "Escaneo QR"
        self._label_seccion(self.contenido, "Escaneo de Placa QR")
        card = self._tarjeta(self.contenido)
        card.pack(fill="both", padx=40, pady=12, expand=True)
        self.video_label = ctk.CTkLabel(
            card, text="Presiona 'Iniciar' para activar la cámara")
        self.video_label.pack(pady=20)
        self._boton(card, "▶  Iniciar escaneo", self._iniciar_escaneo, width=220).pack(pady=8)
        self._boton(card, "⏹  Detener", self._detener_camara,
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
        placa = escanear_qr(frame)
        if placa:
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
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM residentes WHERE placa=? AND activo=1", (placa,)).fetchone()
        conn.close()
        if row:
            info = (f"Unidad: {row['unidad']}\nNombre: {row['nombre']}\n"
                    f"Teléfono: {row['telefono'] or '—'}\nPlaca: {row['placa']}")
            self._notificar("info", "Residente encontrado", info)
        else:
            self._notificar("aviso", "No registrado",
                            f"Placa {placa} no encontrada en residentes activos")

    # ── REPORTES PDF ─────────────────────────────────────────────────────────────

    def _ir_reportes(self):
        self._limpiar_contenido()
        self.current_page = "Reportes PDF"
        self._label_seccion(self.contenido, "Generación de Reportes")
        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)
        opciones = ctk.CTkFrame(card, fg_color="transparent")
        opciones.pack(pady=20, padx=30, fill="x")
        ctk.CTkLabel(opciones, text="Fecha inicio:", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).grid(row=0, column=0, sticky="e", padx=(0, 12), pady=8)
        self._rep_fecha_ini = self._entrada(opciones, placeholder="YYYY-MM-DD", width=200)
        self._rep_fecha_ini.grid(row=0, column=1, sticky="w")
        self._rep_fecha_ini.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkLabel(opciones, text="Fecha fin:", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).grid(row=1, column=0, sticky="e", padx=(0, 12), pady=8)
        self._rep_fecha_fin = self._entrada(opciones, placeholder="YYYY-MM-DD", width=200)
        self._rep_fecha_fin.grid(row=1, column=1, sticky="w")
        self._rep_fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkLabel(opciones, text="Tipo:", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).grid(row=2, column=0, sticky="e", padx=(0, 12), pady=8)
        self._rep_tipo = ctk.CTkComboBox(opciones, values=["Todos", "residente", "visitante"], width=200)
        self._rep_tipo.grid(row=2, column=1, sticky="w")
        self._boton(card, "📄  Generar PDF", self._generar_pdf,
                     color="#1d4ed8", hover="#1e40af", width=260).pack(pady=20)

    def _generar_pdf(self):
        fecha_ini = self._rep_fecha_ini.get().strip()
        fecha_fin = self._rep_fecha_fin.get().strip()
        tipo = self._rep_tipo.get()
        try:
            datetime.strptime(fecha_ini, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            self._notificar("error", "Fecha inválida", "Use el formato YYYY-MM-DD")
            return
        exito, msg = generar_pdf(fecha_ini, fecha_fin, tipo, self.current_user)
        if exito:
            abrir_archivo_qr(msg)
        self._notificar("ok" if exito else "error", "Reporte", msg)

    # ── GESTIÓN DE USUARIOS (solo admin) ────────────────────────────────────────

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
                          text_color=COLORES["texto_2"]).grid(row=i, column=0, sticky="e", padx=(0, 16), pady=8)
            mostrar = "*" if "Contraseña" in lbl else ""
            e = self._entrada(form, placeholder=hint, width=320, show=mostrar)
            e.grid(row=i, column=1, sticky="w")
            self._usr_ent[lbl] = e
        self._usr_ent["Contraseña *"].bind("<KeyRelease>", self._mostrar_fortaleza_usr)
        self._fortaleza_usr_lbl = ctk.CTkLabel(
            form, text="", font=("Segoe UI", 11), text_color=COLORES["texto_3"])
        self._fortaleza_usr_lbl.grid(row=2, column=1, sticky="w", padx=(0, 16))
        ctk.CTkLabel(form, text="Rol *", font=("Segoe UI", 13),
                      text_color=COLORES["texto_2"]).grid(row=3, column=0, sticky="e", padx=(0, 16), pady=8)
        self._usr_rol = ctk.CTkComboBox(form, values=["admin", "operador", "residente"], width=320)
        self._usr_rol.grid(row=3, column=1, sticky="w", padx=(0, 16))
        self._boton(card, "➕  Crear Usuario", self._crear_usuario, width=220).pack(pady=12)
        ctk.CTkLabel(self.contenido, text="Usuarios existentes",
                      font=("Segoe UI", 14, "bold"), text_color=COLORES["texto_3"]
                      ).pack(anchor="w", padx=44, pady=(16, 4))
        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                        corner_radius=12, height=240)
        lista.pack(fill="x", padx=40, pady=(0, 24))
        fila_h = ctk.CTkFrame(lista, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")
        for h in ["ID", "Usuario", "Rol", "Acciones"]:
            ctk.CTkLabel(fila_h, text=h, font=("Segoe UI", 12, "bold"),
                          text_color=COLORES["texto_3"]).pack(side="left", expand=True, padx=8, pady=8)
        for i, row in enumerate(obtener_usuarios()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x")
            for val in [row["id"], row["usuario"], row["rol"]]:
                ctk.CTkLabel(f, text=str(val), font=("Segoe UI", 12),
                              text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=8, pady=6)
            if row["usuario"] != "admin":
                ctk.CTkButton(f, text="Eliminar", width=80, height=28,
                               fg_color=COLORES["rojo"], hover_color=COLORES["rojo_hover"],
                               font=("Segoe UI", 11), corner_radius=6,
                               command=lambda uid=row["id"]: self._eliminar_usuario(uid)
                               ).pack(side="left", padx=8)

    def _mostrar_fortaleza_usr(self, event=None):
        pwd = self._usr_ent["Contraseña *"].get()
        if not pwd:
            self._fortaleza_usr_lbl.configure(text="")
            return
        ok, msg = validate_password_strength(pwd)
        color = COLORES["verde"] if ok else COLORES["rojo"]
        icono = "✓" if ok else "⚠"
        self._fortaleza_usr_lbl.configure(text=f"{icono} {msg}", text_color=color)

    def _crear_usuario(self):
        usuario = self._usr_ent["Usuario *"].get().strip()
        pwd = self._usr_ent["Contraseña *"].get().strip()
        rol = self._usr_rol.get()
        if not usuario or not pwd:
            self._notificar("error", "Error", "Usuario y contraseña son obligatorios")
            return
        ok, msg = validate_password_strength(pwd)
        if not ok:
            self._notificar("error", "Contraseña débil", msg)
            return
        nuevo_hash = hash_password(pwd)
        if crear_usuario(usuario, nuevo_hash, rol):
            self._notificar("ok", "Éxito", f"Usuario '{usuario}' creado con rol {rol}")
            self._ir_usuarios()
        else:
            self._notificar("error", "Error", f"Usuario '{usuario}' ya existe")

    def _eliminar_usuario(self, uid: int):
        res = CTkMessagebox(title="Confirmar", message="¿Eliminar este usuario?",
                             icon="warning", option_1="Sí", option_2="Cancelar")
        if res.get() == "Sí":
            eliminar_usuario(uid)
            self._ir_usuarios()

    # ── RESPALDOS ────────────────────────────────────────────────────────────────

    def _ir_backups(self):
        self._limpiar_contenido()
        self.current_page = "Respaldos"
        self._label_seccion(self.contenido, "Respaldos de Base de Datos")
        card = self._tarjeta(self.contenido)
        card.pack(fill="x", padx=40, pady=12)
        frame_btn = ctk.CTkFrame(card, fg_color="transparent")
        frame_btn.pack(pady=16, padx=20, fill="x")
        self._boton(frame_btn, "💾 Crear Backup Manual", self._crear_backup_manual,
                     color=COLORES["verde"], width=240).pack(side="left", padx=8)
        self._boton(frame_btn, "🗂 Abrir Carpeta",
                     lambda: abrir_archivo_qr(BACKUP_DIR), width=180).pack(side="left", padx=8)
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(info_frame, text="ℹ️ Backups automáticos diarios a las 00:00",
                      font=("Segoe UI", 12), text_color=COLORES["texto_3"]).pack(side="left")
        ctk.CTkLabel(self.contenido, text="Backups disponibles",
                      font=("Segoe UI", 14, "bold"), text_color=COLORES["texto_3"]
                      ).pack(anchor="w", padx=44, pady=(16, 4))
        lista = ctk.CTkScrollableFrame(self.contenido, fg_color=COLORES["tarjeta"],
                                        corner_radius=12, height=300)
        lista.pack(fill="both", padx=40, pady=(0, 24), expand=True)
        backups = get_backups_list()
        if not backups:
            ctk.CTkLabel(lista, text="No hay backups disponibles",
                          font=("Segoe UI", 14), text_color=COLORES["texto_3"]
                          ).pack(pady=20)
        else:
            for i, bp in enumerate(backups):
                bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
                f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
                f.pack(fill="x")
                nombre = os.path.basename(bp)
                ctk.CTkLabel(f, text=nombre, font=("Segoe UI", 12),
                              text_color=COLORES["texto_2"]).pack(side="left", expand=True, padx=12, pady=8)
                ctk.CTkButton(f, text="Restaurar", width=100, height=28,
                               fg_color=COLORES["amarillo"], hover_color="#ca8a04",
                               font=("Segoe UI", 11), corner_radius=6,
                               command=lambda p=bp: self._restaurar_backup(p)
                               ).pack(side="left", padx=8, pady=4)

    def _crear_backup_manual(self):
        exito, msg = crear_backup()
        self._notificar("ok" if exito else "error", "Backup", msg)
        if exito:
            self._ir_backups()

    def _restaurar_backup(self, backup_path):
        res = CTkMessagebox(
            title="Confirmar",
            message=f"¿Restaurar desde:\n{os.path.basename(backup_path)}?\n\n"
            "Se creará un respaldo previo automáticamente.",
            icon="warning", option_1="Sí, restaurar", option_2="Cancelar")
        if res.get() == "Sí, restaurar":
            exito, msg = restaurar_backup(backup_path)
            self._notificar("ok" if exito else "error", "Restaurar", msg)
            if exito:
                self._ir_backups()


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ResiControl()
    app.mainloop()