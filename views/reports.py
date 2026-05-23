import customtkinter as ctk
from datetime import datetime

from views.base import BaseView
from config import COLORES, FONT
from config import PAD_CARD_X, PAD_CARD_Y, PAD_FORM_X, PAD_FORM_Y
from report_generator import generar_pdf
from qr_manager import abrir_archivo as abrir_archivo_qr


class ReportsView(BaseView):
    """View for PDF report generation."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        self.label_seccion(self, "Generación de Reportes")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        self._crear_formulario(card)

    def _crear_formulario(self, parent):
        opciones = ctk.CTkFrame(parent, fg_color="transparent")
        opciones.pack(pady=PAD_FORM_Y, padx=40, fill="x")

        # Vertical stacked form layout
        ctk.CTkLabel(
            opciones,
            text="Fecha inicio:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=0, column=0, sticky="w", pady=(8, 2))

        self._rep_fecha_ini = self.entrada(opciones, placeholder="YYYY-MM-DD", width=220)
        self._rep_fecha_ini.grid(row=1, column=0, sticky="w", pady=(0, 8))
        self._rep_fecha_ini.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(
            opciones,
            text="Fecha fin:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=2, column=0, sticky="w", pady=(8, 2))

        self._rep_fecha_fin = self.entrada(opciones, placeholder="YYYY-MM-DD", width=220)
        self._rep_fecha_fin.grid(row=3, column=0, sticky="w", pady=(0, 8))
        self._rep_fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkLabel(
            opciones,
            text="Tipo de accesos:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=4, column=0, sticky="w", pady=(8, 2))

        self._rep_tipo = ctk.CTkComboBox(
            opciones,
            values=["Todos", "residente", "visitante"],
            width=220,
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._rep_tipo.grid(row=5, column=0, sticky="w", pady=(0, 16))

        self.boton(
            parent,
            "Generar PDF",
            self._generar_pdf,
            color=COLORES["azul_oscuro"],
            hover=COLORES["azul_hover"],
            width=260,
        ).pack(pady=PAD_FORM_Y)

    def _generar_pdf(self):
        fecha_ini = self._rep_fecha_ini.get().strip()
        fecha_fin = self._rep_fecha_fin.get().strip()
        tipo = self._rep_tipo.get()

        try:
            datetime.strptime(fecha_ini, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            self.notificar("error", "Fecha inválida", "Use el formato YYYY-MM-DD")
            return

        exito, msg = generar_pdf(fecha_ini, fecha_fin, tipo, self.app.current_user)
        if exito:
            abrir_archivo_qr(msg)
        self.notificar("ok" if exito else "error", "Reporte", msg)
