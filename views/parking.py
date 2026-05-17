"""
Parking view for ResiControl.

Handles parking lot visualization and management.
"""

import customtkinter as ctk

from views.base import BaseView
from config import COLORES
from validators import validate_placa
from models import (
    obtener_parqueaderos_resumen,
    obtener_parqueaderos_por_tipo,
    obtener_parqueaderos_libres_visitante,
    asignar_parqueadero,
    liberar_parqueadero,
)


class ParkingView(BaseView):
    """View for parking lot management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        """Create the parking management interface."""
        self.label_seccion(self, "Parqueaderos")
        self._renderizar_resumen()
        self._renderizar_grids()
        self._crear_asignacion()

    def _renderizar_resumen(self):
        """Render summary cards."""
        res = obtener_parqueaderos_resumen()
        res_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_frame.pack(fill="x", padx=40, pady=(0, 16))

        for titulo, valor, color in [
            ("Residentes libres", str(res["libres_residente"]), "#22c55e"),
            ("Visitantes libres", str(res["libres_visitante"]), COLORES["azul"]),
            ("Ocupados", str(res["ocupados"]), COLORES["rojo"]),
        ]:
            c = ctk.CTkFrame(
                res_frame,
                fg_color=COLORES["tarjeta"],
                corner_radius=12,
                border_width=1,
                border_color=COLORES["borde"],
            )
            c.pack(side="left", expand=True, padx=10, fill="both")
            ctk.CTkLabel(
                c, text=titulo, font=("Segoe UI", 12), text_color=COLORES["texto_3"]
            ).pack(pady=(12, 2))
            ctk.CTkLabel(
                c, text=valor, font=("Segoe UI", 28, "bold"), text_color=color
            ).pack(pady=(0, 12))

    def _renderizar_grids(self):
        """Render parking grids for residents and visitors."""
        ctk.CTkLabel(
            self,
            text="Residentes",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=44, pady=(8, 4))
        self._grid_parqueaderos("residente")

        ctk.CTkLabel(
            self,
            text="Visitantes",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=44, pady=(16, 4))
        self._grid_parqueaderos("visitante")

    def _grid_parqueaderos(self, tipo: str):
        """Render a grid of parking spots."""
        filas = obtener_parqueaderos_por_tipo(tipo)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=44, pady=4, fill="x")
        cols = 10

        for idx, row in enumerate(filas):
            col = idx % cols
            fila_idx = idx // cols
            color = "#22c55e" if row["estado"] == "libre" else COLORES["rojo"]
            texto = row["numero"]

            btn = ctk.CTkButton(
                grid,
                text=texto,
                width=72,
                height=56,
                corner_radius=10,
                fg_color=color,
                hover_color="#1e3a5f",
                font=("Segoe UI", 12, "bold"),
                text_color="#fff",
                command=lambda p=row["numero"], s=row["estado"], pl=row["placa"]: self._accion(p, s, pl),
            )
            btn.grid(row=fila_idx, column=col, padx=5, pady=5)

    def _accion(self, numero: str, estado: str, placa: str | None):
        """Handle parking spot click."""
        from CTkMessagebox import CTkMessagebox

        if estado == "ocupado":
            msg = f"Parqueadero {numero}\nPlaca: {placa or '—'}\n\n¿Liberar?"
            res = CTkMessagebox(
                title="Parqueadero ocupado", message=msg, icon="warning", option_1="Liberar", option_2="Cancelar"
            )
            if res.get() == "Liberar":
                liberar_parqueadero(numero)
                self.app._ir_parqueaderos()
        else:
            self.notificar("info", "Parqueadero libre", f"{numero} está disponible")

    def _crear_asignacion(self):
        """Create manual parking assignment form."""
        sec = self.tarjeta(self)
        sec.pack(fill="x", padx=40, pady=16)
        ctk.CTkLabel(
            sec,
            text="Asignar parqueadero a visitante",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 16))

        self._park_placa = self.entrada(fila, placeholder="Placa del vehículo", width=220)
        self._park_placa.pack(side="left", padx=(0, 12))

        self._park_numero = ctk.CTkComboBox(fila, width=160, values=obtener_parqueaderos_libres_visitante())
        self._park_numero.pack(side="left", padx=(0, 12))

        self.boton(fila, "Asignar", self._asignar, width=140).pack(side="left")

    def _asignar(self):
        """Handle parking assignment."""
        placa = self._park_placa.get().strip().upper()
        numero = self._park_numero.get().strip()

        if not placa or not numero or numero == "Sin espacio":
            self.notificar("error", "Error", "Ingrese placa y seleccione un parqueadero")
            return

        if not validate_placa(placa):
            self.notificar("error", "Error", "Formato de placa inválido")
            return

        exito, msg = asignar_parqueadero(numero, placa, self.app.current_user)
        self.notificar("ok" if exito else "aviso", "Asignación", msg)
        if exito:
            self.app._ir_parqueaderos()