import customtkinter as ctk

from views.base import BaseView
from config import COLORES, FONT
from config import LISTA_USUARIOS_ALTURA, ACCION_BOTON_ANCHO, BOTON_PEQUENO_ALTURA
from config import RADIO_PANEL, RADIO_BOTON_PEQUENO, BOTON_SECUNDARIO_ANCHO
from config import PAD_CARD_X, PAD_CARD_Y, PAD_FORM_X, PAD_FORM_Y, PAD_SECTION_LABEL_X, PAD_LIST_BOTTOM
from auth import hash_password, validate_password_strength
from models import crear_usuario, obtener_usuarios, eliminar_usuario


class UsersView(BaseView):
    """View for user management (admin only)."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._entradas: dict[str, ctk.CTkEntry] = {}
        self._crear_vista()

    def _crear_vista(self):
        if self.app.rol != "admin":
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.label_seccion(scroll, "Gestión de Usuarios")
        card = self.tarjeta(scroll)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        self._crear_formulario(card)
        self._crear_lista(scroll)

    def _crear_formulario(self, parent):
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(pady=PAD_FORM_Y, padx=PAD_FORM_X, fill="x")

        campos_usr = [("Usuario *", "Nuevo usuario"), ("Contraseña *", "Contraseña")]

        # Stack input fields vertically
        for i, (lbl, hint) in enumerate(campos_usr):
            ctk.CTkLabel(
                form,
                text=lbl,
                font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"],
            ).grid(row=2 * i, column=0, sticky="w", pady=(8, 2))
            
            mostrar = "*" if "Contraseña" in lbl else ""
            e = self.entrada(form, placeholder=hint, width=320, show=mostrar)
            e.grid(row=2 * i + 1, column=0, sticky="w", pady=(0, 8))
            self._entradas[lbl] = e

        self._entradas["Contraseña *"].bind("<KeyRelease>", self._mostrar_fortaleza)
        self._fortaleza_lbl = ctk.CTkLabel(
            form, text="", font=FONT["pequeno"], text_color=COLORES["texto_3"]
        )
        self._fortaleza_lbl.grid(row=4, column=0, sticky="w", pady=(0, 8))

        ctk.CTkLabel(
            form,
            text="Rol *",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=5, column=0, sticky="w", pady=(8, 2))

        self._usr_rol = ctk.CTkComboBox(
            form,
            values=["admin", "operador", "residente"],
            width=320,
            fg_color=COLORES["panel"],
            state="readonly",
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._usr_rol.grid(row=6, column=0, sticky="w", pady=(0, 16))
        self._usr_rol.set("Selecciona uno")

        self.boton(parent, "Crear Usuario", self._crear, width=BOTON_SECUNDARIO_ANCHO).pack(pady=PAD_CARD_Y)

    def _crear_lista(self, parent=None):
        if parent is None:
            parent = self
        ctk.CTkLabel(
            parent,
            text="Usuarios existentes",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=PAD_SECTION_LABEL_X, pady=(16, 4))

        # Thin scrollbar styling
        lista = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_PANEL,
            height=LISTA_USUARIOS_ALTURA,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        lista.pack(fill="x", padx=PAD_CARD_X, pady=PAD_LIST_BOTTOM)

        COL_USR_ANCHOS = [100, 400, 250, 150]

        fila_h = ctk.CTkFrame(lista, fg_color=COLORES["tabla_header"], corner_radius=0)
        fila_h.pack(fill="x")

        for ci, h in enumerate(["ID", "Usuario", "Rol", "Acciones"]):
            ctk.CTkLabel(
                fila_h,
                text=h,
                width=COL_USR_ANCHOS[ci],
                font=FONT["tabla_cabecera"],
                text_color=COLORES["texto_3"],
            ).pack(side="left", padx=2, pady=8)

        for i, row in enumerate(obtener_usuarios()):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            hover_bg = COLORES["borde"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=6)
            f.pack(fill="x", pady=2, padx=4)

            for ci, val in enumerate([row["id"], row["usuario"], row["rol"]]):
                ctk.CTkLabel(
                    f,
                    text=str(val),
                    width=COL_USR_ANCHOS[ci],
                    font=FONT["tabla_dato"],
                    text_color=COLORES["texto_2"],
                ).pack(side="left", padx=2, pady=6)

            if row["usuario"] != "admin":
                ctk.CTkButton(
                    f,
                    text="Eliminar",
                    width=COL_USR_ANCHOS[3],
                    height=BOTON_PEQUENO_ALTURA,
                    fg_color=COLORES["rojo"],
                    hover_color=COLORES["rojo_hover"],
                    font=FONT["pequeno"],
                    corner_radius=RADIO_BOTON_PEQUENO,
                    command=lambda uid=row["id"]: self._eliminar(uid),
                ).pack(side="left", padx=2)

            # High fidelity row hover binders
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

    def _mostrar_fortaleza(self, event=None):
        pwd = self._entradas["Contraseña *"].get()
        if not pwd:
            self._fortaleza_lbl.configure(text="")
            return
        ok, msg = validate_password_strength(pwd)
        color = COLORES["verde"] if ok else COLORES["rojo"]
        icono = "OK" if ok else "!"
        self._fortaleza_lbl.configure(text=f"{icono} {msg}", text_color=color)

    def _crear(self):
        usuario = self._entradas["Usuario *"].get().strip()
        pwd = self._entradas["Contraseña *"].get().strip()
        rol = self._usr_rol.get()

        if not usuario or not pwd:
            self.notificar("error", "Error", "Usuario y contraseña son obligatorios")
            return

        if rol == "Selecciona uno":
            self.notificar("aviso", "Rol requerido", "Seleccione un rol para el usuario")
            return

        ok, msg = validate_password_strength(pwd)
        if not ok:
            self.notificar("error", "Contraseña débil", msg)
            return

        nuevo_hash = hash_password(pwd)
        exito, msg = crear_usuario(usuario, nuevo_hash, rol)
        if exito:
            self.notificar("ok", "Éxito", f"Usuario '{usuario}' creado con rol {rol}")
            self.app._cambiar_pagina("Usuarios", self.app._ir_usuarios)
        else:
            self.notificar("error", "Error", f"Usuario '{usuario}' ya existe")

    def _eliminar(self, uid: int):
        from CTkMessagebox import CTkMessagebox

        res = CTkMessagebox(
            title="Confirmar",
            message="¿Eliminar este usuario?",
            icon="warning",
            option_1="Si",
            option_2="Cancelar",
        )
        if res.get() == "Si":
            eliminar_usuario(uid)
            self.app._cambiar_pagina("Usuarios", self.app._ir_usuarios)
