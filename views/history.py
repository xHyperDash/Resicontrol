import customtkinter as ctk
from datetime import datetime

from views.base import BaseView
from config import COLORES, FONT
from config import BUSQUEDA_ENTRADA_ANCHO, TABLA_HISTORIAL_ALTURA, DIALOGO_ENTRADA_ANCHO
from config import BOTON_PEQUENO_ANCHO, BOTON_PEQUENO_ALTURA, RADIO_BOTON_PEQUENO, RADIO_PANEL
from config import PAD_CARD_X, PAD_CARD_Y, PAD_LIST_BOTTOM
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
        self.label_seccion(self, "Historial de Accesos")
        filtros = ctk.CTkFrame(self, fg_color="transparent")
        filtros.pack(fill="x", padx=PAD_CARD_X, pady=(8, 0))

        self._hist_busq = self.entrada(filtros, placeholder="Buscar por nombre, cédula o placa...", width=BUSQUEDA_ENTRADA_ANCHO)
        self._hist_busq.pack(side="left", padx=(0, 10))

        self._hist_tipo = ctk.CTkComboBox(
            filtros,
            values=["Todos", "residente", "visitante"],
            width=160,
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._hist_tipo.pack(side="left", padx=(0, 10))

        self.boton(filtros, "Filtrar", self._filtrar, width=120).pack(side="left")
        self.boton(
            filtros, "CSV", self._exportar_csv, width=100, color=COLORES["gris"]
        ).pack(side="left", padx=(10, 0))

        self._crear_tabla()

    def _crear_tabla(self):
        # Configure thin scrollbar
        self._hist_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_PANEL,
            height=TABLA_HISTORIAL_ALTURA,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        self._hist_frame.pack(fill="both", padx=PAD_CARD_X, pady=PAD_CARD_Y, expand=True)
        self._renderizar()

    def _renderizar(self, busq="", tipo="Todos"):
        for w in self._hist_frame.winfo_children():
            w.destroy()

        encabezados = ["Tipo", "Nombre", "Cédula", "Placa", "Entrada", "Salida", "Operador", "Acciones"]
        fila_h = ctk.CTkFrame(self._hist_frame, fg_color=COLORES["tabla_header"], corner_radius=0)
        fila_h.pack(fill="x")

        for h in encabezados:
            ctk.CTkLabel(
                fila_h,
                text=h,
                font=FONT["tabla_cabecera"],
                text_color=COLORES["texto_3"],
            ).pack(side="left", expand=True, padx=6, pady=8)

        registros = obtener_historial(busq, tipo)

        for i, row in enumerate(registros):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            hover_bg = COLORES["borde"]
            f = ctk.CTkFrame(self._hist_frame, fg_color=bg, corner_radius=6)
            f.pack(fill="x", pady=2, padx=4)

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
                    font=FONT["tabla_dato"],
                    text_color=COLORES["texto_2"],
                    wraplength=150,
                ).pack(side="left", expand=True, padx=6, pady=6)

            if row.get("salida") is None:
                ctk.CTkButton(
                    f,
                    text="Edit",
                    width=BOTON_PEQUENO_ANCHO,
                    height=BOTON_PEQUENO_ALTURA,
                    corner_radius=RADIO_BOTON_PEQUENO,
                    fg_color=COLORES["amarillo"],
                    hover_color=COLORES["hover_amarillo"],
                    font=FONT["tabla_dato"],
                    command=lambda r=row: self._editar_dialog(r),
                ).pack(side="left", padx=8, pady=4)

            # Row hover highlights
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

    def _filtrar(self):
        self._renderizar(self._hist_busq.get().strip(), self._hist_tipo.get())

    def _exportar_csv(self):
        busq = self._hist_busq.get().strip()
        fecha_ini = busq if busq else "2020-01-01"
        fecha_fin = busq if busq else datetime.now().strftime("%Y-%m-%d")
        ok, ruta = generar_csv(fecha_ini, fecha_fin, self._hist_tipo.get())
        if ok:
            abrir_archivo_qr(ruta)
        self.notificar("ok" if ok else "error", "Exportar CSV", ruta)

    def _editar_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Registro")
        dialog.geometry("400x420")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Editar registro activo",
            font=FONT["dialogo_titulo"],
            text_color=COLORES["texto"]
        ).pack(pady=(20, 8))

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=40, fill="x")

        lbls = [
            ("Nombre:", "nombre", datos.get("nombre", "")),
            ("Cédula:", "cedula", datos.get("cedula", "")),
            ("Placa:", "placa", datos.get("placa", "") or ""),
        ]

        # Stack dialog inputs vertically
        ents = {}
        for i, (label, key, val) in enumerate(lbls):
            ctk.CTkLabel(
                frame,
                text=label,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"]
            ).grid(row=2 * i, column=0, sticky="w", pady=(8, 2))
            
            e = self.entrada(frame, placeholder=label, width=DIALOGO_ENTRADA_ANCHO + 40)
            e.grid(row=2 * i + 1, column=0, pady=(0, 8), sticky="w")
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
                self.app._cambiar_pagina("Historial", self.app._ir_historial)

        self.boton(dialog, "Guardar", guardar, color=COLORES["verde"]).pack(pady=20)
