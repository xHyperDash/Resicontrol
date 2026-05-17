"""
History view for ResiControl.

Displays access history with filtering and CSV export.
"""

import customtkinter as ctk
from datetime import datetime

from views.base import BaseView
from config import COLORES
from models import obtener_historial
from report_generator import generar_csv
from qr_manager import abrir_archivo as abrir_archivo_qr


class HistoryView(BaseView):
    """View for access history."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        """Create the history view."""
        self.label_seccion(self, "Historial de Accesos")
        filtros = ctk.CTkFrame(self, fg_color="transparent")
        filtros.pack(fill="x", padx=40, pady=8)

        self._hist_busq = self.entrada(filtros, placeholder="Buscar por nombre, cédula o placa...", width=340)
        self._hist_busq.pack(side="left", padx=(0, 10))

        self._hist_tipo = ctk.CTkComboBox(filtros, values=["Todos", "residente", "visitante"], width=160)
        self._hist_tipo.pack(side="left", padx=(0, 10))

        self.boton(filtros, "Filtrar", self._filtrar, width=120).pack(side="left")
        self.boton(
            filtros, "CSV", self._exportar_csv, width=100, color="#6b7280"
        ).pack(side="left", padx=(10, 0))

    def _crear_tabla(self):
        """Create the history table."""
        self._hist_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORES["tarjeta"], corner_radius=12, height=480
        )
        self._hist_frame.pack(fill="both", padx=40, pady=12, expand=True)
        self._renderizar()

    def _renderizar(self, busq: str = "", tipo: str = "Todos"):
        """Render the history table."""
        for w in self._hist_frame.winfo_children():
            w.destroy()

        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador", "Acciones"]
        fila_h = ctk.CTkFrame(self._hist_frame, fg_color="#1e3a5f", corner_radius=0)
        fila_h.pack(fill="x")

        for h in encabezados:
            ctk.CTkLabel(
                fila_h,
                text=h,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORES["texto_3"],
            ).pack(side="left", expand=True, padx=6, pady=8)

        registros = obtener_historial(busq, tipo)

        for i, row in enumerate(registros):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._hist_frame, fg_color=bg, corner_radius=0)
            f.pack(fill="x")

            valores_visibles = [
                row.get("tipo", ""),
                row.get("nombre", ""),
                row.get("cedula", ""),
                row.get("placa", ""),
                row.get("entrada", ""),
                row.get("salida", ""),
                row.get("operador", ""),
            ]

            for val in valores_visibles:
                texto = str(val) if val is not None else "Activo"
                ctk.CTkLabel(
                    f,
                    text=texto,
                    font=("Segoe UI", 12),
                    text_color=COLORES["texto_2"],
                    wraplength=150,
                ).pack(side="left", expand=True, padx=6, pady=6)

            if row.get("salida") is None:
                ctk.CTkButton(
                    f,
                    text="Edit",
                    width=36,
                    height=28,
                    corner_radius=6,
                    fg_color=COLORES["amarillo"],
                    hover_color="#ca8a04",
                    font=("Segoe UI", 12),
                    command=lambda r=row: self._editar_dialog(r),
                ).pack(side="left", padx=4, pady=4)

    def _filtrar(self):
        """Apply filters to the history."""
        self._renderizar(self._hist_busq.get().strip(), self._hist_tipo.get())

    def _exportar_csv(self):
        """Export history to CSV."""
        busq = self._hist_busq.get().strip()
        fecha_ini = busq if busq else "2020-01-01"
        fecha_fin = busq if busq else datetime.now().strftime("%Y-%m-%d")
        ok, ruta = generar_csv(fecha_ini, fecha_fin, self._hist_tipo.get())
        if ok:
            abrir_archivo_qr(ruta)
        self.notificar("ok" if ok else "error", "Exportar CSV", ruta)

    def _editar_dialog(self, datos: dict):
        """Show dialog to edit history entry."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Registro")
        dialog.geometry("400x280")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Editar registro activo", font=("Segoe UI", 16, "bold")).pack(
            pady=(16, 8)
        )

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")

        lbls = [
            ("Nombre:", "nombre", datos.get("nombre", "")),
            ("Cédula:", "cedula", datos.get("cedula", "")),
            ("Placa:", "placa", datos.get("placa", "") or ""),
        ]

        ents = {}
        for i, (label, key, val) in enumerate(lbls):
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).grid(
                row=i, column=0, sticky="w", pady=6
            )
            e = self.entrada(frame, placeholder=label, width=250)
            e.grid(row=i, column=1, pady=6, padx=(8, 0))
            e.insert(0, str(val))
            ents[key] = e

        def guardar():
            from models import editar_acceso

            nombre = ents["nombre"].get().strip()
            cedula = ents["cedula"].get().strip()
            placa = ents["placa"].get().strip().upper()
            if not nombre or not cedula:
                self.notificar("error", "Error", "Nombre y cédula son obligatorios")
                return
            exito, msg = editar_acceso(datos["id"], nombre, cedula, placa, self.app.current_user)
            self.notificar("ok" if exito else "error", "Editar", msg)
            if exito:
                dialog.destroy()
                self.app._ir_historial()

        self.boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=16)