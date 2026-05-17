"""
Dashboard view for ResiControl.

Displays metrics and quick access buttons for the main features.
"""

import customtkinter as ctk
from views.base import BaseView
from config import COLORES
from models import obtener_metricas


class DashboardView(BaseView):
    """Dashboard view showing metrics and quick actions."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        """Create the dashboard layout."""
        self._crear_header()
        self._crear_metricas()
        self._crear_accesos_rapidos()

    def _crear_header(self):
        """Create the welcome header."""
        header = ctk.CTkFrame(self, fg_color="#1e293b", height=70, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"Bienvenido, {self.app.current_user.upper()}",
            font=("Segoe UI", 22, "bold"),
            text_color="#00aaff",
        ).pack(pady=18)

    def _crear_metricas(self):
        """Create the metrics cards."""
        self.metricas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metricas_frame.pack(fill="x", padx=32, pady=(24, 16))

        m = obtener_metricas()
        datos = [
            ("Entradas hoy", str(m["entradas_hoy"]), "#22c55e"),
            ("Residentes", str(m["residentes"]), COLORES["azul"]),
            ("Parqueaderos oc.", str(m["ocupados"]), COLORES["amarillo"]),
            ("Dentro ahora", str(m["dentro"]), COLORES["rojo"]),
        ]

        for titulo, valor, color in datos:
            self._crear_tarjeta_metrica(titulo, valor, color)

        if self.app.current_page == "Inicio":
            self.after(10000, self._actualizar_metricas)

    def _crear_tarjeta_metrica(self, titulo: str, valor: str, color: str):
        """Create a single metric card."""
        card = ctk.CTkFrame(
            self.metricas_frame,
            fg_color=COLORES["tarjeta"],
            corner_radius=14,
            border_width=1,
            border_color=COLORES["borde"],
        )
        card.pack(side="left", expand=True, padx=10, fill="both")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            top, text=titulo, font=("Segoe UI", 12, "bold"), text_color=COLORES["texto_3"]
        ).pack(side="left")
        ctk.CTkLabel(
            top, text="*", font=("Segoe UI", 16), text_color=color
        ).pack(side="right")
        ctk.CTkLabel(
            card, text=valor, font=("Segoe UI", 30, "bold"), text_color=COLORES["texto"]
        ).pack(pady=(4, 14))

    def _actualizar_metricas(self):
        """Refresh the metrics display."""
        if hasattr(self, "metricas_frame"):
            self.metricas_frame.destroy()
        self._crear_metricas()

    def _crear_accesos_rapidos(self):
        """Create quick access buttons."""
        sec = self.tarjeta(self)
        sec.pack(fill="x", padx=32, pady=(0, 24))
        sec.pack_propagate(False)
        sec.configure(height=108)

        ctk.CTkLabel(
            sec,
            text="Accesos rápidos",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=20, pady=(8, 4))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(padx=16)

        botones = [
            ("Visitantes", COLORES["azul"], self.app._ir_visitantes),
            ("Residentes", "#2563eb", self.app._ir_residentes),
            ("Parqueaderos", COLORES["verde"], self.app._ir_parqueaderos),
            ("Historial", COLORES["amarillo"], self.app._ir_historial),
            ("Reporte", "#1d4ed8", self.app._ir_reportes),
        ]

        for texto, color, cmd in botones:
            ctk.CTkButton(
                fila,
                text=texto,
                width=160,
                height=44,
                corner_radius=10,
                fg_color=color,
                hover_color="#1e40af",
                font=("Segoe UI", 12, "bold"),
                text_color="#fff",
                command=cmd,
            ).pack(side="left", padx=8)