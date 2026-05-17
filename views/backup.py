"""
Backup view for ResiControl.

Handles backup creation and restoration.
"""

import customtkinter as ctk
import os

from views.base import BaseView
from config import COLORES, BACKUP_DIR
from backup import crear_backup, restaurar_backup, get_backups_list
from qr_manager import abrir_archivo as abrir_archivo_qr


class BackupView(BaseView):
    """View for backup management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        """Create the backup view."""
        self.label_seccion(self, "Respaldos de Base de Datos")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=40, pady=12)

        self._crear_botones(card)
        self._crear_lista()

    def _crear_botones(self, parent):
        """Create backup action buttons."""
        frame_btn = ctk.CTkFrame(parent, fg_color="transparent")
        frame_btn.pack(pady=16, padx=20, fill="x")

        self.boton(
            frame_btn,
            "Crear Backup Manual",
            self._crear_manual,
            color=COLORES["verde"],
            width=240,
        ).pack(side="left", padx=8)

        self.boton(
            frame_btn,
            "Abrir Carpeta",
            lambda: abrir_archivo_qr(BACKUP_DIR),
            width=180,
        ).pack(side="left", padx=8)

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            info_frame,
            text="Backups automaticos diarios a las 00:00",
            font=("Segoe UI", 12),
            text_color=COLORES["texto_3"],
        ).pack(side="left")

    def _crear_lista(self):
        """Create the backup list."""
        ctk.CTkLabel(
            self,
            text="Backups disponibles",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=44, pady=(16, 4))

        lista = ctk.CTkScrollableFrame(
            self, fg_color=COLORES["tarjeta"], corner_radius=12, height=300
        )
        lista.pack(fill="both", padx=40, pady=(0, 24), expand=True)

        backups = get_backups_list()

        if not backups:
            ctk.CTkLabel(
                lista,
                text="No hay backups disponibles",
                font=("Segoe UI", 14),
                text_color=COLORES["texto_3"],
            ).pack(pady=20)
        else:
            for i, bp in enumerate(backups):
                bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
                f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
                f.pack(fill="x")

                nombre = os.path.basename(bp)
                ctk.CTkLabel(
                    f,
                    text=nombre,
                    font=("Segoe UI", 12),
                    text_color=COLORES["texto_2"],
                ).pack(side="left", expand=True, padx=12, pady=8)

                ctk.CTkButton(
                    f,
                    text="Restaurar",
                    width=100,
                    height=28,
                    fg_color=COLORES["amarillo"],
                    hover_color="#ca8a04",
                    font=("Segoe UI", 11),
                    corner_radius=6,
                    command=lambda p=bp: self._restaurar(p),
                ).pack(side="left", padx=8, pady=4)

    def _crear_manual(self):
        """Handle manual backup creation."""
        exito, msg = crear_backup()
        self.notificar("ok" if exito else "error", "Backup", msg)
        if exito:
            self._recargar()

    def _restaurar(self, backup_path: str):
        """Handle backup restoration."""
        from CTkMessagebox import CTkMessagebox

        res = CTkMessagebox(
            title="Confirmar",
            message=f"¿Restaurar desde:\n{os.path.basename(backup_path)}?\n\n"
            "Se creara un respaldo previo automaticamente.",
            icon="warning",
            option_1="Si, restaurar",
            option_2="Cancelar",
        )

        if res.get() == "Si, restaurar":
            exito, msg = restaurar_backup(backup_path)
            self.notificar("ok" if exito else "error", "Restaurar", msg)
            if exito:
                self._recargar()

    def _recargar(self):
        """Reload the backup view."""
        self.app._ir_backups()