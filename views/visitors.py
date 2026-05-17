"""
Visitors view for ResiControl.

Handles visitor registration, entry/exit tracking, and editing.
"""

import customtkinter as ctk
import sqlite3

from views.base import BaseView
from config import COLORES, DB_PATH
from validators import (
    validate_required,
    validate_cedula,
    validate_unidad,
    validate_placa,
)
from models import (
    registrar_entrada_visitante,
    registrar_salida_visitante,
    obtener_visitantes_activos,
    editar_acceso,
)


class VisitorsView(BaseView):
    """View for visitor registration and management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._entradas: dict[str, ctk.CTkEntry] = {}
        self._crear_vista()

    def _crear_vista(self):
        """Create the visitors management interface."""
        self.label_seccion(self, "Registro de Visitantes")
        card = self.tarjeta(self)
        card.pack(fill="both", padx=40, pady=12, expand=True)

        self._crear_formulario(card)
        self._crear_tabla_activos()

    def _crear_formulario(self, parent):
        """Create the visitor registration form."""
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")

        campos = [
            ("Nombre completo *", "Ej: Carlos Perez", False),
            ("Cédula *", "Ej: 1234567890", False),
            ("Placa (opcional)", "Ej: ABC123", False),
            ("Invitado por (unidad) *", "Ej: 301", False),
        ]

        for i, (label, hint, oculto) in enumerate(campos):
            ctk.CTkLabel(
                form,
                text=label,
                font=("Segoe UI", 13),
                text_color=COLORES["texto_2"],
            ).grid(row=i, column=0, sticky="e", padx=(0, 16), pady=8)
            e = self.entrada(form, placeholder=hint, width=420, show="*" if oculto else "")
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._entradas[label] = e

        self._consent = ctk.CTkCheckBox(
            parent,
            text="Autorizo el tratamiento de datos personales (Ley 1581/2012)",
            font=("Segoe UI", 12),
            text_color=COLORES["texto_2"],
        )
        self._consent.pack(pady=12)

        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(pady=16)

        self.boton(fila, "Registrar Entrada", self._registrar_entrada, width=220).pack(
            side="left", padx=12
        )
        self.boton(
            fila,
            "Registrar Salida",
            self._registrar_salida,
            color=COLORES["rojo"],
            hover=COLORES["rojo_hover"],
            width=220,
        ).pack(side="left", padx=12)

    def _crear_tabla_activos(self):
        """Create the table of active visitors."""
        ctk.CTkLabel(
            self,
            text="Visitantes actualmente dentro",
            font=("Segoe UI", 15, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=44, pady=(8, 4))

        lista = ctk.CTkScrollableFrame(
            self, fg_color=COLORES["tarjeta"], corner_radius=12, height=200
        )
        lista.pack(fill="x", padx=40, pady=(0, 24))

        encabezados = ["Nombre", "Cédula", "Placa", "Unidad", "Entrada", "Operador", "Acciones"]
        self._crear_header_tabla(lista, encabezados)

        for i, fila_data in enumerate(obtener_visitantes_activos()):
            self._crear_fila_tabla(lista, fila_data, i)

    def _crear_header_tabla(self, parent, columnas):
        header = ctk.CTkFrame(parent, fg_color="#1e3a5f", corner_radius=0)
        header.pack(fill="x")
        for h in columnas:
            ctk.CTkLabel(
                header,
                text=h,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORES["texto_3"],
            ).pack(side="left", expand=True, padx=8, pady=8)

    def _crear_fila_tabla(self, parent, datos, indice):
        bg = "#111827" if indice % 2 == 0 else COLORES["tarjeta"]
        f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0)
        f.pack(fill="x")

        for key in ["nombre", "cedula", "placa", "unidad", "entrada", "operador"]:
            ctk.CTkLabel(
                f,
                text=str(datos.get(key, "—") or "—"),
                font=("Segoe UI", 12),
                text_color=COLORES["texto_2"],
            ).pack(side="left", expand=True, padx=8, pady=6)

        ctk.CTkButton(
            f,
            text="Edit",
            width=36,
            height=28,
            corner_radius=6,
            fg_color=COLORES["amarillo"],
            hover_color="#ca8a04",
            font=("Segoe UI", 12),
            command=lambda d=datos: self._editar_dialog(d),
        ).pack(side="left", padx=4, pady=4)

    def _registrar_entrada(self):
        """Handle visitor entry registration."""
        if not self._consent.get():
            self.notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return

        nombre = self._entradas["Nombre completo *"].get().strip()
        cedula = self._entradas["Cédula *"].get().strip()
        placa = self._entradas["Placa (opcional)"].get().strip().upper()
        unidad = self._entradas["Invitado por (unidad) *"].get().strip()

        if not validate_required(nombre, "Nombre")[0]:
            self.notificar("error", "Error", "Nombre es obligatorio")
            return
        if not validate_cedula(cedula):
            self.notificar("error", "Error", "Cédula inválida o vacía")
            return
        if not validate_unidad(unidad)[0]:
            self.notificar("error", "Error", "Unidad es obligatoria")
            return
        if placa and not validate_placa(placa):
            self.notificar("error", "Error", "Formato de placa inválido (ej: ABC123)")
            return

        exito, msg = registrar_entrada_visitante(nombre, cedula, placa, unidad, self.app.current_user)
        self.notificar("ok" if exito else "error", "Registro", msg)
        if exito:
            self._recargar()

    def _registrar_salida(self):
        """Handle visitor exit registration."""
        cedula = self._entradas["Cédula *"].get().strip()
        placa = self._entradas["Placa (opcional)"].get().strip().upper()

        if not cedula and not placa:
            self.notificar("aviso", "Atención", "Ingrese cédula o placa para registrar salida")
            return

        exito, msg = registrar_salida_visitante(cedula, placa, self.app.current_user)
        self.notificar("ok" if exito else "aviso", "Salida", msg)
        if exito:
            self._recargar()

    def _editar_dialog(self, datos: dict):
        """Show dialog to edit visitor data."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Visitante")
        dialog.geometry("420x340")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Editar datos del visitante",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(16, 8))

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")

        campos = [
            ("Nombre:", "nombre", datos.get("nombre", "")),
            ("Cédula:", "cedula", datos.get("cedula", "")),
            ("Placa:", "placa", datos.get("placa", "") or ""),
        ]

        entradas = {}
        for i, (label, key, val) in enumerate(campos):
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).grid(
                row=i, column=0, sticky="w", pady=6
            )
            e = self.entrada(frame, placeholder=label, width=280)
            e.grid(row=i, column=1, pady=6, padx=(8, 0))
            e.insert(0, str(val))
            entradas[key] = e

        def guardar():
            nombre = entradas["nombre"].get().strip()
            cedula = entradas["cedula"].get().strip()
            placa = entradas["placa"].get().strip().upper()
            if not nombre or not cedula:
                self.notificar("error", "Error", "Nombre y cédula son obligatorios")
                return
            acc_id = datos.get("id")
            if acc_id is None:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT id FROM accesos WHERE cedula=? AND salida IS NULL AND tipo='visitante'",
                    (cedula,),
                ).fetchone()
                conn.close()
                acc_id = row["id"] if row else 0
            exito, msg = editar_acceso(acc_id, nombre, cedula, placa, self.app.current_user)
            self.notificar("ok" if exito else "error", "Editar Visitante", msg)
            if exito:
                dialog.destroy()
                self._recargar()

        self.boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=16)

    def _recargar(self):
        """Reload the visitors view."""
        self.app._ir_visitantes()