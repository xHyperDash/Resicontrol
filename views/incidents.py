"""
Incidents view for ResiControl.

Handles incident logging and display.
"""

import customtkinter as ctk

from views.base import BaseView
from config import COLORES
from validators import validate_required
from models import registrar_incidente, obtener_incidentes


class IncidentsView(BaseView):
    """View for incident management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        """Create the incidents view."""
        self.label_seccion(self, "Registro de Incidentes")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=40, pady=12)

        ctk.CTkLabel(
            card,
            text="Descripción del incidente *",
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self._inc_desc = ctk.CTkTextbox(
            card, height=120, font=("Segoe UI", 13), fg_color="#111827", corner_radius=8
        )
        self._inc_desc.pack(fill="x", padx=20)

        ctk.CTkLabel(
            card,
            text="Nivel de alerta",
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=20, pady=(12, 4))

        self._inc_nivel = ctk.CTkComboBox(card, values=["bajo", "medio", "alto"], width=200)
        self._inc_nivel.pack(anchor="w", padx=20, pady=(0, 16))

        self.boton(
            card,
            "Registrar Incidente",
            self._registrar,
            color=COLORES["amarillo"],
            hover="#ca8a04",
        ).pack(pady=12)

    def _crear_lista(self):
        """Create the incidents list display."""
        ctk.CTkLabel(
            self,
            text="Incidentes recientes",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=44, pady=(16, 4))

        lista = ctk.CTkScrollableFrame(
            self, fg_color=COLORES["tarjeta"], corner_radius=12, height=280
        )
        lista.pack(fill="x", padx=40, pady=(0, 24))

        colores_nivel = {
            "bajo": "#22c55e",
            "medio": COLORES["amarillo"],
            "alto": COLORES["rojo"],
        }

        for i, row in enumerate(obtener_incidentes()):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=2)

            color = colores_nivel.get(row["nivel"], COLORES["texto_3"])

            ctk.CTkLabel(
                f,
                text=f"[{row['nivel'].upper()}]",
                font=("Segoe UI", 11, "bold"),
                text_color=color,
                width=70,
            ).pack(side="left", padx=8, pady=6)

            ctk.CTkLabel(
                f,
                text=row["descripcion"],
                font=("Segoe UI", 12),
                text_color=COLORES["texto_2"],
                wraplength=500,
                justify="left",
            ).pack(side="left", expand=True)

            ctk.CTkLabel(
                f,
                text=f"{row['operador']} — {row['fecha']}",
                font=("Segoe UI", 11),
                text_color=COLORES["texto_3"],
            ).pack(side="right", padx=12)

    def _registrar(self):
        """Handle incident registration."""
        desc = self._inc_desc.get("1.0", "end").strip()
        nivel = self._inc_nivel.get()

        if not validate_required(desc, "Descripción")[0]:
            self.notificar("error", "Error", "La descripción es obligatoria")
            return

        registrar_incidente(desc, nivel, self.app.current_user)
        self.notificar("ok", "Éxito", "Incidente registrado correctamente")
        self.app._ir_incidentes()