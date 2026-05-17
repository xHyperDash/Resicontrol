"""
Residents view for ResiControl.

Handles resident registration, listing, editing, and QR generation.
"""

import customtkinter as ctk
import os

from views.base import BaseView
from config import COLORES
from validators import (
    validate_email,
    validate_placa,
    validate_phone,
    validate_unidad,
    validate_required,
)
from models import (
    crear_residente,
    obtener_residentes,
    editar_residente,
    eliminar_residente,
)

QR_DISPONIBLE = False
try:
    import qrcode as qrcode_lib
    from PIL import Image, ImageTk
    from qr_manager import generar_qr
    QR_DISPONIBLE = True
except ImportError:
    pass


class ResidentsView(BaseView):
    """View for resident management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._entradas: dict[str, ctk.CTkEntry] = {}
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._crear_vista()

    def _crear_vista(self):
        """Create the residents management interface."""
        self.label_seccion(self, "Gestión de Residentes")
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=40, pady=4)
        self._tab_content = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_content.pack(fill="both", expand=True)

        self._crear_tabs(tab_frame)
        self._mostrar_formulario()

    def _crear_tabs(self, parent):
        """Create tab buttons for switching views."""

        def cambiar_tab(tab):
            for w in self._tab_content.winfo_children():
                w.destroy()
            if tab == "nuevo":
                self._mostrar_formulario()
            else:
                self._mostrar_lista()
            for t, b in self._tab_btns.items():
                b.configure(fg_color=COLORES["azul"] if t == tab else COLORES["tarjeta"])

        for nombre, clave in [("Nuevo residente", "nuevo"), ("Ver residentes", "lista")]:
            b = ctk.CTkButton(
                parent,
                text=nombre,
                width=200,
                height=40,
                corner_radius=8,
                font=("Segoe UI", 13),
                fg_color=COLORES["tarjeta"],
                hover_color=COLORES["borde"],
                command=lambda k=clave: cambiar_tab(k),
            )
            b.pack(side="left", padx=6)
            self._tab_btns[clave] = b

    def _mostrar_formulario(self):
        """Show the new resident form."""
        card = self.tarjeta(self._tab_content)
        card.pack(fill="x", padx=40, pady=12)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")

        campos = [
            ("Unidad *", "Ej: 301"),
            ("Nombre completo *", "Ej: Maria Lopez"),
            ("Teléfono", "Ej: 3001234567"),
            ("Email", "Ej: maria@correo.com"),
            ("Placa *", "Ej: XYZ789"),
        ]

        for i, (label, hint) in enumerate(campos):
            ctk.CTkLabel(
                form,
                text=label,
                font=("Segoe UI", 13),
                text_color=COLORES["texto_2"],
            ).grid(row=i, column=0, sticky="e", padx=(0, 16), pady=8)
            e = self.entrada(form, placeholder=hint, width=420)
            e.grid(row=i, column=1, pady=8, sticky="w")
            self._entradas[label] = e

        self._consent = ctk.CTkCheckBox(
            card,
            text="Autorizo tratamiento de datos (Ley 1581/2012)",
            font=("Segoe UI", 12),
            text_color=COLORES["texto_2"],
        )
        self._consent.pack(pady=12)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=16)

        self.boton(
            fila,
            "Registrar Residente",
            self._registrar,
            color=COLORES["verde"],
            hover=COLORES["verde_hover"],
            width=240,
        ).pack(side="left", padx=12)

        if QR_DISPONIBLE:
            self.boton(
                fila,
                "Generar QR",
                self._generar_qr,
                color=COLORES["amarillo"],
                hover="#ca8a04",
                width=180,
            ).pack(side="left", padx=12)

    def _validar(self, unidad: str, nombre: str, placa: str, email: str, telefono: str) -> tuple[bool, str]:
        """Validate resident form data."""
        if not validate_unidad(unidad):
            return False, "Unidad es obligatoria"
        ok, msg = validate_required(nombre, "Nombre")
        if not ok:
            return False, msg
        if not validate_placa(placa):
            return False, "Formato de placa inválido (ej: ABC123)"
        if email and not validate_email(email):
            return False, "Formato de email inválido"
        if telefono and not validate_phone(telefono):
            return False, "Formato de teléfono inválido (7-10 dígitos)"
        return True, ""

    def _registrar(self):
        """Handle resident registration."""
        if not self._consent.get():
            self.notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return

        unidad = self._entradas["Unidad *"].get().strip()
        nombre = self._entradas["Nombre completo *"].get().strip()
        placa = self._entradas["Placa *"].get().strip().upper()
        tel = self._entradas["Teléfono"].get().strip()
        email = self._entradas["Email"].get().strip()

        ok, msg = self._validar(unidad, nombre, placa, email, tel)
        if not ok:
            self.notificar("error", "Error de validación", msg)
            return

        exito, msg = crear_residente(unidad, nombre, tel, email, placa)
        self.notificar("ok" if exito else "error", "Registro", msg)
        if exito:
            self.app._ir_residentes()

    def _generar_qr(self):
        """Generate QR code for a license plate."""
        if not QR_DISPONIBLE:
            self.notificar("error", "No disponible", "Librería qrcode no instalada")
            return
        placa = self._entradas["Placa *"].get().strip().upper()
        if not placa:
            self.notificar("error", "Error", "Ingrese la placa primero")
            return
        ok, msg = generar_qr(placa)
        self.notificar("ok" if ok else "error", "QR" if ok else "Error", msg)

    def _mostrar_lista(self):
        """Show the resident list."""
        card = self.tarjeta(self._tab_content)
        card.pack(fill="both", padx=40, pady=12, expand=True)

        buscador = ctk.CTkFrame(card, fg_color="transparent")
        buscador.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(
            buscador,
            text="Buscar:",
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
        ).pack(side="left", padx=(0, 10))
        self._busq = self.entrada(buscador, placeholder="Nombre, unidad o placa...", width=360)
        self._busq.pack(side="left")
        self.boton(buscador, "Buscar", self._buscar, width=120).pack(side="left", padx=10)

        self._tabla = ctk.CTkScrollableFrame(card, fg_color="#111827", corner_radius=8)
        self._tabla.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._renderizar_tabla()

    def _renderizar_tabla(self, filtro: str = ""):
        """Render the residents table."""
        for w in self._tabla.winfo_children():
            w.destroy()

        encabezados = ["ID", "Unidad", "Nombre", "Teléfono", "Email", "Placa", "QR", "Acciones"]
        header = ctk.CTkFrame(self._tabla, fg_color="#1e3a5f", corner_radius=0)
        header.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(
                header,
                text=h,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORES["texto_3"],
            ).pack(side="left", expand=True, padx=6, pady=8)

        for i, row in enumerate(obtener_residentes(filtro)):
            bg = "#111827" if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._tabla, fg_color=bg, corner_radius=0)
            f.pack(fill="x")

            for key in ["id", "unidad", "nombre", "telefono", "email", "placa"]:
                val = row.get(key)
                texto = str(val or "—")
                ctk.CTkLabel(
                    f, text=texto, font=("Segoe UI", 12), text_color=COLORES["texto_2"]
                ).pack(side="left", expand=True, padx=6, pady=6)

            qr_path = row.get("qr_code") or ""
            qr_texto = "Si" if qr_path and os.path.exists(qr_path) else "—"
            ctk.CTkLabel(
                f, text=qr_texto, font=("Segoe UI", 12), text_color=COLORES["texto_2"]
            ).pack(side="left", expand=True, padx=6, pady=6)

            frame_acc = ctk.CTkFrame(f, fg_color="transparent")
            frame_acc.pack(side="left", padx=4)
            rid = row["id"]

            ctk.CTkButton(
                frame_acc,
                text="Edit",
                width=36,
                height=28,
                corner_radius=6,
                fg_color=COLORES["azul"],
                hover_color=COLORES["azul_hover"],
                font=("Segoe UI", 12),
                command=lambda r=row: self._editar_dialog(r),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                frame_acc,
                text="Del",
                width=36,
                height=28,
                corner_radius=6,
                fg_color=COLORES["rojo"],
                hover_color=COLORES["rojo_hover"],
                font=("Segoe UI", 12),
                command=lambda i=rid: self._eliminar(i),
            ).pack(side="left", padx=2)

    def _buscar(self):
        """Filter the resident list."""
        self._renderizar_tabla(self._busq.get().strip())

    def _editar_dialog(self, datos: dict):
        """Show dialog to edit resident."""
        from CTkMessagebox import CTkMessagebox

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Residente")
        dialog.geometry("450x400")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"Editar: {datos.get('nombre', '')}",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(16, 8))

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=30, fill="x")

        campos_def = [
            ("Unidad *", "unidad", datos.get("unidad", "")),
            ("Nombre *", "nombre", datos.get("nombre", "")),
            ("Teléfono", "telefono", datos.get("telefono", "") or ""),
            ("Email", "email", datos.get("email", "") or ""),
            ("Placa *", "placa", datos.get("placa", "")),
        ]

        entradas = {}
        for i, (label, key, val_actual) in enumerate(campos_def):
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).grid(
                row=i, column=0, sticky="w", pady=6
            )
            e = self.entrada(frame, placeholder=label, width=280)
            e.grid(row=i, column=1, pady=6, padx=(8, 0))
            e.insert(0, str(val_actual))
            entradas[key] = (e, label)

        def guardar():
            unidad = entradas["unidad"][0].get().strip()
            nombre = entradas["nombre"][0].get().strip()
            telefono = entradas["telefono"][0].get().strip()
            email = entradas["email"][0].get().strip()
            placa = entradas["placa"][0].get().strip().upper()
            ok, msg = self._validar(unidad, nombre, placa, email, telefono)
            if not ok:
                self.notificar("error", "Validación", msg)
                return
            exito, msg = editar_residente(datos["id"], unidad, nombre, telefono, email, placa)
            self.notificar("ok" if exito else "error", "Editar Residente", msg)
            if exito:
                dialog.destroy()
                self._recargar()

        self.boton(dialog, "Guardar Cambios", guardar, color=COLORES["verde"]).pack(pady=16)

    def _eliminar(self, rid: int):
        """Delete a resident (soft delete)."""
        from CTkMessagebox import CTkMessagebox

        res = CTkMessagebox(
            title="Confirmar",
            message="¿Eliminar este residente?",
            icon="warning",
            option_1="Si, eliminar",
            option_2="Cancelar",
        )
        if res.get() == "Si, eliminar":
            eliminar_residente(rid)
            self._renderizar_tabla()

    def _recargar(self):
        """Reload the residents view."""
        self.app._ir_residentes()