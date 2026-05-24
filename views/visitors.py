import customtkinter as ctk
import sqlite3

from views.base import BaseView
from config import COLORES, FONT, DB_PATH
from config import FORMULARIO_ENTRADA_ANCHO, BOTON_SECUNDARIO_ANCHO, DIALOGO_ENTRADA_ANCHO
from config import BOTON_PEQUENO_ANCHO, BOTON_PEQUENO_ALTURA
from config import RADIO_BOTON_PEQUENO, RADIO_PANEL, PAD_LIST_BOTTOM
from config import PAD_CARD_X, PAD_CARD_Y, PAD_FORM_X, PAD_FORM_Y, PAD_SECTION_LABEL_X
from config import PAD_BUTTON_GAP_X, PAD_BUTTON_ROW_Y
from config import BUSQUEDA_ENTRADA_ANCHO
from validators import validate_required, validate_cedula, validate_unidad, validate_placa
from models import (
    registrar_entrada_visitante,
    registrar_salida_visitante,
    registrar_entrada_residente,
    registrar_salida_residente,
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
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.label_seccion(scroll, "Registro de Visitantes")
        card = self.tarjeta(scroll)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        self._crear_formulario(card)
        self._tabla_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._tabla_frame.pack(fill="x")
        self._crear_tabla_activos(self._tabla_frame)

    def _crear_formulario(self, parent):
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(pady=PAD_FORM_Y, padx=PAD_FORM_X, fill="x")

        campos = [
            ("Nombre completo *", "Ej: Carlos Perez", False),
            ("Cédula *", "Ej: 1234567890", False),
            ("Placa (opcional)", "Ej: ABC123", False),
            ("Invitado por (unidad) *", "Ej: 301", False),
        ]

        # Vertical stacked layout for visitor inputs
        for i, (label, hint, oculto) in enumerate(campos):
            lbl = ctk.CTkLabel(
                form,
                text=label,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"],
            )
            lbl.grid(row=2 * i, column=0, sticky="w", padx=(4, 0), pady=(8, 2))
            
            e = self.entrada(form, placeholder=hint, width=FORMULARIO_ENTRADA_ANCHO, show="*" if oculto else "")
            e.grid(row=2 * i + 1, column=0, pady=(0, 8), sticky="w")
            self._entradas[label] = e

        self._consent = ctk.CTkCheckBox(
            parent,
            text="Autorizo el tratamiento de datos personales (Ley 1581/2012)",
            font=FONT["checkbox"],
            text_color=COLORES["texto_2"],
            fg_color=COLORES["acento"],
            hover_color=COLORES["sidebar_hover"],
            border_color=COLORES["borde"]
        )
        self._consent.pack(pady=12)

        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(pady=PAD_BUTTON_ROW_Y)

        self.boton(fila, "Registrar Entrada", self._registrar_entrada, width=BOTON_SECUNDARIO_ANCHO).pack(
            side="left", padx=PAD_BUTTON_GAP_X
        )
        self.boton(
            fila,
            "Registrar Salida",
            self._registrar_salida,
            color=COLORES["rojo"],
            hover=COLORES["rojo_hover"],
            width=BOTON_SECUNDARIO_ANCHO,
        ).pack(side="left", padx=PAD_BUTTON_GAP_X)

    def _crear_tabla_activos(self, parent):
        ctk.CTkLabel(
            parent,
            text="Registro de visitantes",
            font=FONT["subtitulo"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=PAD_SECTION_LABEL_X, pady=(8, 4))

        lista = ctk.CTkFrame(
            parent,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_PANEL,
        )
        lista.pack(fill="x", padx=PAD_CARD_X, pady=PAD_LIST_BOTTOM)

        encabezados = ["Nombre", "Cédula", "Placa", "Unidad", "Estado", "Entrada", "Operador", "Acciones"]
        self._crear_header_tabla(lista, encabezados)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, nombre, cedula, placa, invitado_por AS unidad,
                   entrada, salida, operador
            FROM accesos
            WHERE tipo='visitante'
              AND id IN (
                SELECT MAX(id) FROM accesos WHERE tipo='visitante' GROUP BY cedula
              )
            ORDER BY entrada DESC
            LIMIT 200
        """ ).fetchall()
        conn.close()

        for i, row in enumerate(rows):
            self._crear_fila_tabla(lista, dict(row), i)

    COL_VISIT_ANCHOS = [180, 130, 100, 80, 70, 160, 120, 90]

    def _crear_header_tabla(self, parent, columnas):
        header = ctk.CTkFrame(parent, fg_color=COLORES["tabla_header"], corner_radius=0)
        header.pack(fill="x")
        for ci, h in enumerate(columnas):
            ctk.CTkLabel(
                header,
                text=h,
                width=self.COL_VISIT_ANCHOS[ci],
                font=FONT["tabla_cabecera"],
                text_color=COLORES["texto_3"],
            ).pack(side="left", padx=2, pady=8)

    def _crear_fila_tabla(self, parent, datos, indice):
        bg = COLORES["panel"] if indice % 2 == 0 else COLORES["tarjeta"]
        hover_bg = COLORES["borde"]
        dentro = datos.get("salida") is None
        f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6)
        f.pack(fill="x", pady=2, padx=4)

        for ci, key in enumerate(["nombre", "cedula", "placa", "unidad"]):
            ctk.CTkLabel(
                f,
                text=str(datos.get(key, "—") or "—"),
                width=self.COL_VISIT_ANCHOS[ci],
                font=FONT["tabla_dato"],
                text_color=COLORES["texto_2"],
            ).pack(side="left", padx=2, pady=6)

        ctk.CTkLabel(
            f,
            text="Dentro" if dentro else "Fuera",
            width=self.COL_VISIT_ANCHOS[4],
            font=FONT["tabla_dato"],
            text_color=COLORES["verde"] if dentro else COLORES["texto_3"],
        ).pack(side="left", padx=2, pady=6)

        for ci, key in enumerate(["entrada", "operador"], start=5):
            ctk.CTkLabel(
                f,
                text=str(datos.get(key, "—") or "—"),
                width=self.COL_VISIT_ANCHOS[ci],
                font=FONT["tabla_dato"],
                text_color=COLORES["texto_2"],
            ).pack(side="left", padx=2, pady=6)

        frame_acc = ctk.CTkFrame(f, fg_color="transparent")
        frame_acc.pack(side="left", padx=2)

        ctk.CTkButton(
            frame_acc,
            text="Edit",
            width=36,
            height=BOTON_PEQUENO_ALTURA,
            corner_radius=RADIO_BOTON_PEQUENO,
            fg_color=COLORES["amarillo"],
            hover_color=COLORES["hover_amarillo"],
            font=FONT["tabla_dato"],
            command=lambda d=datos: self._editar_dialog(d),
        ).pack(side="left", padx=1, pady=4)

        ctk.CTkButton(
            frame_acc,
            text="Select",
            width=36,
            height=BOTON_PEQUENO_ALTURA,
            corner_radius=RADIO_BOTON_PEQUENO,
            fg_color=COLORES["azul"],
            hover_color=COLORES["azul_hover"],
            font=FONT["tabla_dato"],
            command=lambda d=datos: self._seleccionar_para_salida(d),
        ).pack(side="left", padx=1, pady=4)

        def bind_row(row_frame, normal_c, hover_c):
            def enter(e):
                if row_frame.winfo_exists():
                    row_frame.configure(fg_color=hover_c)
            def leave(e):
                if row_frame.winfo_exists():
                    row_frame.configure(fg_color=normal_c)
            row_frame.bind("<Enter>", enter)
            row_frame.bind("<Leave>", leave)
            for child in row_frame.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.bind("<Enter>", enter)
                    child.bind("<Leave>", leave)

        bind_row(f, bg, hover_bg)

    def _seleccionar_para_salida(self, datos):
        nombre = str(datos.get("nombre") or "")
        cedula = str(datos.get("cedula") or "")
        placa = str(datos.get("placa") or "")
        unidad = str(datos.get("unidad") or "")
        self._entradas["Nombre completo *"].delete(0, "end")
        self._entradas["Nombre completo *"].insert(0, nombre)
        self._entradas["Cédula *"].delete(0, "end")
        self._entradas["Cédula *"].insert(0, cedula)
        self._entradas["Placa (opcional)"].delete(0, "end")
        self._entradas["Placa (opcional)"].insert(0, placa)
        self._entradas["Invitado por (unidad) *"].delete(0, "end")
        self._entradas["Invitado por (unidad) *"].insert(0, unidad)
        self.notificar("ok", "Seleccionado", "Datos cargados en el formulario")

    def _refrescar_tabla(self):
        for w in self._tabla_frame.winfo_children():
            w.destroy()
        self._crear_tabla_activos(self._tabla_frame)

    def _registrar_entrada(self):
        nombre = self._entradas["Nombre completo *"].get().strip()
        cedula = self._entradas["Cédula *"].get().strip()
        placa = self._entradas["Placa (opcional)"].get().strip().upper()
        unidad = self._entradas["Invitado por (unidad) *"].get().strip()

        if placa:
            conn = sqlite3.connect(DB_PATH)
            es_residente = conn.execute(
                "SELECT id FROM residentes WHERE placa=? AND activo=1", (placa,)
            ).fetchone()
            conn.close()
            if es_residente:
                if not validate_unidad(unidad):
                    self.notificar("error", "Error", "Unidad es obligatoria")
                    return
                exito, msg = registrar_entrada_residente(placa, self.app.current_user)
                self.notificar("ok" if exito else "error", "Entrada Residente", msg)
                if exito:
                    self._refrescar_tabla()
                return

        if not self._consent.get():
            self.notificar("aviso", "Atención", "Debe autorizar el tratamiento de datos")
            return

        if not validate_required(nombre, "Nombre")[0]:
            self.notificar("error", "Error", "Nombre es obligatorio")
            return
        if not validate_cedula(cedula):
            self.notificar("error", "Error", "Cédula inválida o vacía")
            return
        if not validate_unidad(unidad):
            self.notificar("error", "Error", "Unidad es obligatoria")
            return
        if placa and not validate_placa(placa):
            self.notificar("error", "Error", "Formato de placa inválido (ej: ABC123)")
            return

        exito, msg = registrar_entrada_visitante(nombre, cedula, placa, unidad, self.app.current_user)
        self.notificar("ok" if exito else "error", "Registro", msg)
        if exito:
            self._refrescar_tabla()

    def _registrar_salida(self):
        cedula = self._entradas["Cédula *"].get().strip()
        placa = self._entradas["Placa (opcional)"].get().strip().upper()

        if placa:
            conn = sqlite3.connect(DB_PATH)
            es_residente = conn.execute(
                "SELECT id FROM residentes WHERE placa=? AND activo=1", (placa,)
            ).fetchone()
            if not es_residente:
                activo = conn.execute(
                    "SELECT id FROM accesos WHERE placa=? AND salida IS NULL AND tipo='visitante'",
                    (placa,),
                ).fetchone()
            conn.close()
            if es_residente:
                exito, msg = registrar_salida_residente(placa, self.app.current_user)
                self.notificar("ok" if exito else "aviso", "Salida Residente", msg)
                if exito:
                    self._refrescar_tabla()
                return
        else:
            activo = None

        if not cedula and not placa:
            self.notificar("aviso", "Atención", "Ingrese cédula o placa para registrar salida")
            return

        if not activo:
            conn = sqlite3.connect(DB_PATH)
            activo = conn.execute(
                "SELECT id FROM accesos WHERE (cedula=? OR placa=?) AND salida IS NULL AND tipo='visitante'",
                (cedula, placa),
            ).fetchone()
            conn.close()
            if not activo:
                self.notificar("aviso", "Atención", "El visitante ya no se encuentra dentro")
                return

        exito, msg = registrar_salida_visitante(cedula, placa, self.app.current_user)
        self.notificar("ok" if exito else "aviso", "Salida", msg)
        if exito:
            self._refrescar_tabla()

    def _editar_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Visitante")
        dialog.geometry("420x500")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Editar datos del visitante",
            font=FONT["dialogo_titulo"],
            text_color=COLORES["texto"],
        ).pack(pady=(20, 8))

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=40, fill="x")

        campos = [
            ("Nombre:", "nombre", datos.get("nombre", "")),
            ("Cédula:", "cedula", datos.get("cedula", "")),
            ("Placa:", "placa", datos.get("placa", "") or ""),
            ("Unidad:", "unidad", str(datos.get("unidad") or "")),
        ]

        entradas = {}
        for i, (label, key, val) in enumerate(campos):
            ctk.CTkLabel(
                frame,
                text=label,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"]
            ).grid(row=2 * i, column=0, sticky="w", pady=(8, 2))
            
            e = self.entrada(frame, placeholder=label, width=DIALOGO_ENTRADA_ANCHO + 40)
            e.grid(row=2 * i + 1, column=0, pady=(0, 8), sticky="w")
            e.insert(0, str(val))
            entradas[key] = e

        def guardar():
            nombre = entradas["nombre"].get().strip()
            cedula = entradas["cedula"].get().strip()
            placa = entradas["placa"].get().strip().upper()
            unidad = entradas["unidad"].get().strip()
            if not nombre or not cedula:
                self.notificar("error", "Error", "Nombre y cédula son obligatorios")
                return
            acc_id = datos.get("id")
            if acc_id is None:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT id FROM accesos WHERE cedula=? AND tipo='visitante' ORDER BY entrada DESC LIMIT 1",
                    (cedula,),
                ).fetchone()
                conn.close()
                acc_id = row["id"] if row else 0
            exito, msg = editar_acceso(acc_id, nombre, cedula, placa, unidad, self.app.current_user)
            self.notificar("ok" if exito else "error", "Editar Visitante", msg)
            if exito:
                dialog.destroy()
                self._recargar()

        self.boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=20)

    def _recargar(self):
        self.app._cambiar_pagina("Visitantes", self.app._ir_visitantes)
