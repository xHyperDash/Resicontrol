import customtkinter as ctk
import os

from views.base import BaseView
from config import COLORES, FONT
from config import FORMULARIO_ENTRADA_ANCHO, BOTON_SECUNDARIO_ANCHO, DIALOGO_ENTRADA_ANCHO
from config import BOTON_PEQUENO_ANCHO, BOTON_PEQUENO_ALTURA, BUSQUEDA_ENTRADA_ANCHO
from config import RADIO_BOTON_PEQUENO, RADIO_PANEL, RADIO_ENTRADA, PAD_CARD_X, PAD_CARD_Y
from config import PAD_FORM_X, PAD_FORM_Y, PAD_SECTION_LABEL_X, PAD_LIST_BOTTOM
from config import PAD_BUTTON_GAP_X, PAD_BUTTON_ROW_Y, TAB_BOTON_ALTURA
from validators import validate_email, validate_placa, validate_phone, validate_unidad, validate_required
from models import crear_residente, obtener_residentes, editar_residente, eliminar_residente

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
        self.label_seccion(self, "Gestión de Residentes")
        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=PAD_CARD_X, pady=4)
        self._tab_content = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_content.pack(fill="both", expand=True)

        self._crear_tabs(tab_frame)
        self._mostrar_formulario()

    def _crear_tabs(self, parent):
        def cambiar_tab(tab):
            for w in self._tab_content.winfo_children():
                w.destroy()
            if tab == "nuevo":
                self._mostrar_formulario()
            else:
                self._mostrar_lista()
            for t, b in self._tab_btns.items():
                if t == tab:
                    b.configure(
                        fg_color=COLORES["tarjeta"],
                        text_color=COLORES["acento"],
                        border_width=1,
                        border_color=COLORES["borde"],
                    )
                else:
                    b.configure(
                        fg_color="transparent",
                        text_color=COLORES["texto_3"],
                        border_width=0,
                    )

        for nombre, clave in [("Nuevo residente", "nuevo"), ("Ver residentes", "lista")]:
            b = ctk.CTkButton(
                parent,
                text=nombre,
                width=160,
                height=TAB_BOTON_ALTURA,
                corner_radius=RADIO_ENTRADA,
                font=FONT["cuerpo_pequeno"],
                fg_color="transparent",
                text_color=COLORES["texto_3"],
                hover_color=COLORES["sidebar_hover"],
                command=lambda k=clave: cambiar_tab(k),
            )
            b.pack(side="left", padx=4)
            self._tab_btns[clave] = b
            
        # Select active tab initially
        self._tab_btns["nuevo"].configure(
            fg_color=COLORES["tarjeta"],
            text_color=COLORES["acento"],
            border_width=1,
            border_color=COLORES["borde"],
        )

    def _mostrar_formulario(self):
        scroll = ctk.CTkScrollableFrame(self._tab_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card = self.tarjeta(scroll)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=PAD_FORM_Y, padx=PAD_FORM_X, fill="x")

        campos = [
            ("Unidad *", "Ej: 301"),
            ("Nombre completo *", "Ej: Maria Lopez"),
            ("Teléfono", "Ej: 3001234567"),
            ("Email", "Ej: maria@correo.com"),
            ("Placa *", "Ej: XYZ789"),
        ]

        # Stack form fields vertically for premium SaaS layout
        for i, (label, hint) in enumerate(campos):
            lbl = ctk.CTkLabel(
                form,
                text=label,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"],
            )
            lbl.grid(row=2 * i, column=0, sticky="w", padx=(4, 0), pady=(8, 2))
            
            e = self.entrada(form, placeholder=hint, width=FORMULARIO_ENTRADA_ANCHO)
            e.grid(row=2 * i + 1, column=0, pady=(0, 8), sticky="w")
            self._entradas[label] = e

        self._consent = ctk.CTkCheckBox(
            card,
            text="Autorizo tratamiento de datos (Ley 1581/2012)",
            font=FONT["checkbox"],
            text_color=COLORES["texto_2"],
            fg_color=COLORES["acento"],
            hover_color=COLORES["sidebar_hover"],
            border_color=COLORES["borde"]
        )
        self._consent.pack(pady=12)

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(pady=PAD_BUTTON_ROW_Y)

        self.boton(
            fila,
            "Registrar Residente",
            self._registrar,
            color=COLORES["verde"],
            hover=COLORES["verde_hover"],
            width=240,
        ).pack(side="left", padx=PAD_BUTTON_GAP_X)

        if QR_DISPONIBLE:
            self.boton(
                fila,
                "Generar QR",
                self._generar_qr,
                color=COLORES["amarillo"],
                hover=COLORES["hover_amarillo"],
                width=180,
            ).pack(side="left", padx=PAD_BUTTON_GAP_X)

    def _validar(self, unidad, nombre, placa, email, telefono):
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
            self.app._cambiar_pagina("Residentes", self.app._ir_residentes)

    def _generar_qr(self):
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
        card = self.tarjeta(self._tab_content)
        card.pack(fill="both", padx=PAD_CARD_X, pady=PAD_CARD_Y, expand=True)

        buscador = ctk.CTkFrame(card, fg_color="transparent")
        buscador.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(
            buscador,
            text="Buscar:",
            font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_2"],
        ).pack(side="left", padx=(0, 10))
        self._busq = self.entrada(buscador, placeholder="Nombre, unidad o placa...", width=BUSQUEDA_ENTRADA_ANCHO)
        self._busq.pack(side="left")
        self.boton(buscador, "Buscar", self._buscar, width=120).pack(side="left", padx=10)

        # Style table scrollable frame with thin scrollbars
        self._tabla = ctk.CTkScrollableFrame(
            card,
            fg_color=COLORES["panel"],
            corner_radius=RADIO_ENTRADA,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        self._tabla.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._renderizar_tabla()

    def _renderizar_tabla(self, filtro=""):
        for w in self._tabla.winfo_children():
            w.destroy()

        encabezados = ["ID", "Unidad", "Nombre", "Teléfono", "Email", "Placa", "QR", "Acciones"]
        header = ctk.CTkFrame(self._tabla, fg_color=COLORES["tabla_header"], corner_radius=0)
        header.pack(fill="x")
        for h in encabezados:
            ctk.CTkLabel(
                header,
                text=h,
                font=FONT["tabla_cabecera"],
                text_color=COLORES["texto_3"],
            ).pack(side="left", expand=True, padx=6, pady=8)

        for i, row in enumerate(obtener_residentes(filtro)):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            hover_bg = COLORES["borde"]
            f = ctk.CTkFrame(self._tabla, fg_color=bg, corner_radius=6)
            f.pack(fill="x", pady=2, padx=4)

            for key in ["id", "unidad", "nombre", "telefono", "email", "placa"]:
                val = row.get(key)
                texto = str(val or "—")
                ctk.CTkLabel(
                    f, text=texto, font=FONT["tabla_dato"], text_color=COLORES["texto_2"]
                ).pack(side="left", expand=True, padx=6, pady=6)

            qr_path = row.get("qr_code") or ""
            qr_texto = "Si" if qr_path and os.path.exists(qr_path) else "—"
            ctk.CTkLabel(
                f, text=qr_texto, font=FONT["tabla_dato"], text_color=COLORES["texto_2"]
            ).pack(side="left", expand=True, padx=6, pady=6)

            frame_acc = ctk.CTkFrame(f, fg_color="transparent")
            frame_acc.pack(side="left", padx=8)
            rid = row["id"]

            ctk.CTkButton(
                frame_acc,
                text="Edit",
                width=BOTON_PEQUENO_ANCHO,
                height=BOTON_PEQUENO_ALTURA,
                corner_radius=RADIO_BOTON_PEQUENO,
                fg_color=COLORES["azul"],
                hover_color=COLORES["azul_hover"],
                font=FONT["tabla_dato"],
                command=lambda r=row: self._editar_dialog(r),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                frame_acc,
                text="Del",
                width=BOTON_PEQUENO_ANCHO,
                height=BOTON_PEQUENO_ALTURA,
                corner_radius=RADIO_BOTON_PEQUENO,
                fg_color=COLORES["rojo"],
                hover_color=COLORES["rojo_hover"],
                font=FONT["tabla_dato"],
                command=lambda i=rid: self._eliminar(i),
            ).pack(side="left", padx=4)

            # High fidelity row hover bindings
            def bind_row_hover(row_frame, normal_c, hover_c):
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

            bind_row_hover(f, bg, hover_bg)

    def _buscar(self):
        self._renderizar_tabla(self._busq.get().strip())

    def _editar_dialog(self, datos: dict):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Residente")
        dialog.geometry("450x520")
        dialog.configure(fg_color=COLORES["panel"])
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"Editar: {datos.get('nombre', '')}",
            font=FONT["dialogo_titulo"],
            text_color=COLORES["texto"],
        ).pack(pady=(20, 8))

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(padx=40, fill="x")

        campos_def = [
            ("Unidad *", "unidad", datos.get("unidad", "")),
            ("Nombre *", "nombre", datos.get("nombre", "")),
            ("Teléfono", "telefono", datos.get("telefono", "") or ""),
            ("Email", "email", datos.get("email", "") or ""),
            ("Placa *", "placa", datos.get("placa", "")),
        ]

        # Stack dialog inputs vertically as well
        entradas = {}
        for i, (label, key, val_actual) in enumerate(campos_def):
            ctk.CTkLabel(
                frame,
                text=label,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"]
            ).grid(row=2 * i, column=0, sticky="w", pady=(8, 2))
            
            e = self.entrada(frame, placeholder=label, width=DIALOGO_ENTRADA_ANCHO + 40)
            e.grid(row=2 * i + 1, column=0, pady=(0, 8), sticky="w")
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

        self.boton(dialog, "Guardar Cambios", guardar, color=COLORES["verde"]).pack(pady=20)

    def _eliminar(self, rid: int):
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
        self.app._cambiar_pagina("Residentes", self.app._ir_residentes)
