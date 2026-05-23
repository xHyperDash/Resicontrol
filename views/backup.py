import customtkinter as ctk
import os

from views.base import BaseView
from config import COLORES, FONT, BACKUP_DIR
from config import LISTA_BACKUPS_ALTURA, ACCION_BOTON_ANCHO, BOTON_PEQUENO_ALTURA
from config import RADIO_PANEL, RADIO_BOTON_PEQUENO, PAD_CARD_X, PAD_CARD_Y, PAD_SECTION_LABEL_X, PAD_LIST_BOTTOM
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
        self.label_seccion(self, "Respaldos de Base de Datos")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        self._crear_botones(card)
        self._crear_lista()

    def _crear_botones(self, parent):
        frame_btn = ctk.CTkFrame(parent, fg_color="transparent")
        frame_btn.pack(pady=PAD_CARD_Y, padx=20, fill="x")

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
            text="Backups automáticos diarios a las 00:00",
            font=FONT["checkbox"],
            text_color=COLORES["texto_3"],
        ).pack(side="left")

    def _crear_lista(self):
        ctk.CTkLabel(
            self,
            text="Backups disponibles",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=PAD_SECTION_LABEL_X, pady=(16, 4))

        # Thin scrollbar configuration
        lista = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_PANEL,
            height=LISTA_BACKUPS_ALTURA,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        lista.pack(fill="both", padx=PAD_CARD_X, pady=PAD_LIST_BOTTOM, expand=True)

        backups = get_backups_list()

        if not backups:
            ctk.CTkLabel(
                lista,
                text="No hay backups disponibles",
                font=FONT["cuerpo"],
                text_color=COLORES["texto_3"],
            ).pack(pady=20)
        else:
            for i, bp in enumerate(backups):
                bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
                hover_bg = COLORES["borde"]
                f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=6)
                f.pack(fill="x", pady=2, padx=4)

                nombre = os.path.basename(bp)
                ctk.CTkLabel(
                    f,
                    text=nombre,
                    font=FONT["tabla_dato"],
                    text_color=COLORES["texto_2"],
                ).pack(side="left", expand=True, padx=12, pady=8)

                ctk.CTkButton(
                    f,
                    text="Restaurar",
                    width=ACCION_BOTON_ANCHO + 14,
                    height=BOTON_PEQUENO_ALTURA,
                    fg_color=COLORES["amarillo"],
                    hover_color=COLORES["hover_amarillo"],
                    font=FONT["pequeno"],
                    corner_radius=RADIO_BOTON_PEQUENO,
                    command=lambda p=bp: self._restaurar(p),
                ).pack(side="left", padx=8, pady=4)

                # High fidelity row hover binders
                def make_hover(row_frame, normal, hover):
                    def enter(e):
                        if row_frame.winfo_exists():
                            row_frame.configure(fg_color=hover)
                    def leave(e):
                        if row_frame.winfo_exists():
                            row_frame.configure(fg_color=normal)
                    row_frame.bind("<Enter>", enter)
                    row_frame.bind("<Leave>", leave)
                    for child in row_frame.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            child.bind("<Enter>", enter)
                            child.bind("<Leave>", leave)

                make_hover(f, bg, hover_bg)

    def _crear_manual(self):
        exito, msg = crear_backup()
        self.notificar("ok" if exito else "error", "Backup", msg)
        if exito:
            self._recargar()

    def _restaurar(self, backup_path: str):
        from CTkMessagebox import CTkMessagebox

        res = CTkMessagebox(
            title="Confirmar",
            message=f"¿Restaurar desde:\n{os.path.basename(backup_path)}?\n\n"
            "Se creará un respaldo previo automáticamente.",
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
        self.app._cambiar_pagina("Respaldos", self.app._ir_backups)
