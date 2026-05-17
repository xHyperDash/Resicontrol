#!/usr/bin/env python3
"""
ResiControl - Main application window.

This module contains the main ResiControl class that manages
the application window and integrates all view modules.
"""

import customtkinter as ctk
import sqlite3

CAMARA_DISPONIBLE = False
try:
    import cv2
    CAMARA_DISPONIBLE = True
except ImportError:
    pass

from config import COLORES, DB_PATH
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
from database import (
    create_tables,
    create_indexes,
    add_audit_columns,
    seed_parqueaderos,
    insert_default_users,
)
from backup import iniciar_scheduler
from logger import logger


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class ResiControl(ctk.CTk):
    """Main application window for ResiControl."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ResiControl - Gestión de Seguridad Residencial")
        self.geometry("1300x820")
        self.configure(fg_color=COLORES["fondo"])

        self.current_user: str | None = None
        self.rol: str | None = None
        self.current_page: str | None = None
        self.current_view: ctk.CTkFrame | None = None

        self.cap: "cv2.VideoCapture | None" = None  # type: ignore[attr-defined]
        self.scanning: bool = False
        self.video_label: ctk.CTkLabel | None = None

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

    def _limpiar(self) -> None:
        self._detener_camara()
        for w in self.winfo_children():
            w.destroy()

    def _detener_camara(self) -> None:
        self.scanning = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _on_close(self) -> None:
        self._detener_camara()
        self.conn.close()
        self.destroy()

    def mostrar_login(self) -> None:
        """Display the login screen."""
        self._limpiar()

        frame = ctk.CTkFrame(
            self,
            width=460,
            corner_radius=20,
            fg_color=COLORES["panel"],
            border_width=1,
            border_color=COLORES["borde"],
        )
        frame.pack(expand=True, fill="both", padx=420, pady=40)

        ctk.CTkLabel(
            frame,
            text="ResiControl",
            font=("Helvetica", 38, "bold"),
            text_color="#00aaff",
        ).pack(pady=(32, 4))
        ctk.CTkLabel(
            frame,
            text="Gestión de Seguridad Residencial",
            font=("Segoe UI", 14),
            text_color=COLORES["texto_3"],
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Usuario",
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=40, pady=(28, 4))
        self.user_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Ingrese su usuario",
            fg_color="#111827",
            border_color=COLORES["borde_hover"],
            corner_radius=8,
            height=42,
            font=("Segoe UI", 13),
            width=360,
        )
        self.user_entry.pack()

        ctk.CTkLabel(
            frame,
            text="Contraseña",
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=40, pady=(16, 4))
        self.pwd_entry = ctk.CTkEntry(
            frame,
            placeholder_text="********",
            fg_color="#111827",
            border_color=COLORES["borde_hover"],
            corner_radius=8,
            height=42,
            font=("Segoe UI", 13),
            width=360,
            show="*",
        )
        self.pwd_entry.pack()

        self._fortaleza_lbl = ctk.CTkLabel(
            frame, text="", font=("Segoe UI", 11), text_color=COLORES["texto_3"]
        )
        self._fortaleza_lbl.pack(anchor="w", padx=40)
        self.pwd_entry.bind("<KeyRelease>", self._mostrar_fortaleza)

        ctk.CTkButton(
            frame,
            text="Iniciar Sesión",
            command=self.login,
            fg_color=COLORES["azul"],
            hover_color=COLORES["azul_hover"],
            corner_radius=10,
            height=46,
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff",
            width=360,
        ).pack(pady=28)

        self.error_lbl = ctk.CTkLabel(
            frame, text="", text_color=COLORES["rojo"], font=("Segoe UI", 13)
        )
        self.error_lbl.pack()

        self.user_entry.bind("<Return>", lambda _: self.login())
        self.pwd_entry.bind("<Return>", lambda _: self.login())
        self.user_entry.focus_set()

    def _mostrar_fortaleza(self, event=None) -> None:
        pwd = self.pwd_entry.get()
        if not pwd:
            self._fortaleza_lbl.configure(text="")
            return
        ok, msg = validate_password_strength(pwd)
        color = COLORES["verde"] if ok else COLORES["rojo"]
        icono = "OK" if ok else "!"
        self._fortaleza_lbl.configure(text=f"{icono} {msg}", text_color=color)

    def login(self) -> None:
        usuario = self.user_entry.get().strip()
        pwd = self.pwd_entry.get().strip()

        if not usuario or not pwd:
            self.error_lbl.configure(text="Complete todos los campos")
            return

        bloqueado, restante = check_lockout(usuario)
        if bloqueado:
            self.error_lbl.configure(text=f"Cuenta bloqueada. Intente en {restante}s")
            return

        from models import verificar_usuario

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

    def _migrar_hash_si_es_necesario(self, usuario: str, pwd_plano: str) -> None:
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

    def mostrar_dashboard(self) -> None:
        """Display the main dashboard with sidebar."""
        self._limpiar()

        from views.navigation import get_menu_items, create_sidebar_menu

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORES["panel"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="ResiControl",
            font=("Helvetica", 24, "bold"),
            text_color="#00aaff",
        ).pack(pady=(32, 4), padx=20)
        rol_text = self.rol.upper() if self.rol else "USUARIO"
        ctk.CTkLabel(
            self.sidebar,
            text=rol_text,
            font=("Segoe UI", 11),
            text_color=COLORES["texto_3"],
        ).pack()
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORES["borde"]).pack(
            fill="x", pady=16, padx=20
        )

        self.sidebar_menu = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent"
        )
        self.sidebar_menu.pack(fill="both", expand=True)

        menu = get_menu_items(self.rol or "operador")
        self.menu_btns = create_sidebar_menu(self, self.sidebar_menu, menu)

        self.crear_contenido()
        self._ir_inicio()

    def crear_contenido(self) -> None:
        """Create the main content area."""
        self.contenido = ctk.CTkFrame(self, fg_color="#0f172a")
        self.contenido.pack(side="right", fill="both", expand=True)

    def _cambiar_pagina(self, nombre: str, accion) -> None:
        """Change the current page."""
        self._detener_camara()

        if self.current_view is not None:
            try:
                self.current_view.destroy()
            except:
                pass
            self.current_view = None

        for t, btn in self.menu_btns.items():
            es_peligro = t == "Cerrar Sesión"
            btn.configure(
                fg_color=(
                    COLORES["rojo"]
                    if es_peligro
                    else "#1e293b"
                    if t == nombre
                    else (COLORES["rojo"] if es_peligro else "transparent")
                )
            )

        self.current_page = nombre
        accion()

    def _ir_inicio(self) -> None:
        """Show dashboard view."""
        from views.dashboard import DashboardView
        self.current_view = DashboardView(self.contenido, self)

    def _ir_visitantes(self) -> None:
        """Show visitors view."""
        from views.visitors import VisitorsView
        self.current_view = VisitorsView(self.contenido, self)

    def _ir_residentes(self) -> None:
        """Show residents view."""
        from views.residents import ResidentsView
        self.current_view = ResidentsView(self.contenido, self)

    def _ir_parqueaderos(self) -> None:
        """Show parking view."""
        from views.parking import ParkingView
        self.current_view = ParkingView(self.contenido, self)

    def _ir_historial(self) -> None:
        """Show history view."""
        from views.history import HistoryView
        self.current_view = HistoryView(self.contenido, self)

    def _ir_incidentes(self) -> None:
        """Show incidents view."""
        from views.incidents import IncidentsView
        self.current_view = IncidentsView(self.contenido, self)

    def _ir_reportes(self) -> None:
        """Show reports view."""
        from views.reports import ReportsView
        self.current_view = ReportsView(self.contenido, self)

    def _ir_usuarios(self) -> None:
        """Show users view (admin only)."""
        from views.users import UsersView
        self.current_view = UsersView(self.contenido, self)

    def _ir_backups(self) -> None:
        """Show backups view."""
        from views.backup import BackupView
        self.current_view = BackupView(self.contenido, self)

    def _ir_qr(self) -> None:
        """Show QR scanner view."""
        from views.qr_scanner import QRScannerView
        self.current_view = QRScannerView(self.contenido, self)




if __name__ == "__main__":
    app = ResiControl()
    app.mainloop()