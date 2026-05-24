import customtkinter as ctk

from views.base import BaseView
from config import COLORES, FONT
from config import TEXTO_INCIDENTE_ALTURA, TABLA_SCROLL_ALTURA
from config import RADIO_ENTRADA, RADIO_PANEL, PAD_CARD_X, PAD_CARD_Y, PAD_LIST_BOTTOM, PAD_SECTION_LABEL_X
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
        self.label_seccion(self, "Registro de Incidentes")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        ctk.CTkLabel(
            card,
            text="Descripción del incidente *",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=20, pady=(16, 4))

        self._inc_desc = ctk.CTkTextbox(
            card,
            height=TEXTO_INCIDENTE_ALTURA,
            font=FONT["cuerpo_pequeno"],
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            border_width=1,
            corner_radius=RADIO_ENTRADA
        )
        self._inc_desc.pack(fill="x", padx=20)

        ctk.CTkLabel(
            card,
            text="Nivel de alerta",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).pack(anchor="w", padx=20, pady=(12, 4))

        self._inc_nivel = ctk.CTkComboBox(
            card,
            values=["bajo", "medio", "alto"],
            width=200,
            state="readonly",
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._inc_nivel.pack(anchor="w", padx=20, pady=(0, 16))
        self._inc_nivel.set("Selecciona uno")

        self.boton(
            card,
            "Registrar Incidente",
            self._registrar,
            color=COLORES["amarillo"],
            hover=COLORES["hover_amarillo"],
        ).pack(pady=PAD_CARD_Y)

        # Explicitly call _crear_lista to display recent incidents below the form!
        self._crear_lista()

    def _crear_lista(self):
        ctk.CTkLabel(
            self,
            text="Incidentes recientes",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=PAD_SECTION_LABEL_X, pady=(16, 4))

        lista = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_PANEL,
            height=TABLA_SCROLL_ALTURA,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        lista.pack(fill="x", padx=PAD_CARD_X, pady=PAD_LIST_BOTTOM)

        colores_nivel = {
            "bajo": COLORES["verde_brillante"],
            "medio": COLORES["amarillo"],
            "alto": COLORES["rojo"],
        }

        for i, row in enumerate(obtener_incidentes()):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            hover_bg = COLORES["borde"]
            f = ctk.CTkFrame(lista, fg_color=bg, corner_radius=6)
            f.pack(fill="x", pady=2, padx=4)

            color = colores_nivel.get(row["nivel"], COLORES["texto_3"])

            ctk.CTkLabel(
                f,
                text=f"[{row['nivel'].upper()}]",
                font=FONT["pequeno_bold"],
                text_color=color,
                width=70,
            ).pack(side="left", padx=8, pady=6)

            ctk.CTkLabel(
                f,
                text=row["descripcion"],
                font=FONT["tabla_dato"],
                text_color=COLORES["texto_2"],
                wraplength=500,
                justify="left",
            ).pack(side="left", expand=True)

            ctk.CTkLabel(
                f,
                text=f"{row['operador']} — {row['fecha']}",
                font=FONT["pequeno"],
                text_color=COLORES["texto_3"],
            ).pack(side="right", padx=12)

            # Elegant row hover highlight
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

    def _registrar(self):
        desc = self._inc_desc.get("1.0", "end").strip()
        nivel = self._inc_nivel.get()

        if not validate_required(desc, "Descripción")[0]:
            self.notificar("error", "Error", "La descripción es obligatoria")
            return

        if nivel == "Selecciona uno":
            self.notificar("aviso", "Nivel requerido", "Seleccione un nivel de alerta")
            return

        registrar_incidente(desc, nivel, self.app.current_user)
        self.notificar("ok", "Éxito", "Incidente registrado correctamente")
        self.app._cambiar_pagina("Incidentes", self.app._ir_incidentes)
