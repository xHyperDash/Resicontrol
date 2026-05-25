import customtkinter as ctk

from views.base import BaseView
from config import COLORES, FONT
from config import PARKING_BOTON_ANCHO, PARKING_BOTON_ALTURA, PARKING_COLUMNAS
from config import RADIO_PANEL, RADIO_BOTON, RADIO_BOTON_PEQUENO, BORDE_TARJETA
from config import PAD_CARD_X, PAD_LIST_BOTTOM, PAD_SECTION_LABEL_X, PAD_BUTTON_ROW_Y
from validators import validate_placa
from models import (
    obtener_parqueaderos_resumen,
    obtener_parqueaderos_por_tipo,
    obtener_parqueaderos_libres_visitante,
    obtener_total_por_tipo,
    agregar_parqueadero,
    eliminar_parqueadero,
    asignar_parqueadero,
    liberar_parqueadero,
)


class ParkingView(BaseView):
    """View for parking lot management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        if not hasattr(self.app, "_parking_selected"):
            self.app._parking_selected = None
        self._slot_btns: dict[str, ctk.CTkButton] = {}
        self._crear_vista()

    def _crear_vista(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.label_seccion(scroll, "Parqueaderos")
        self._renderizar_resumen(scroll)
        self._crear_toolbar(scroll)
        self._renderizar_grids(scroll)
        self._crear_asignacion(scroll)

    def _crear_toolbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=PAD_CARD_X, pady=(0, 8))
        self._eliminar_btn = ctk.CTkButton(
            bar,
            text="✕ Eliminar seleccionado",
            width=160,
            height=30,
            corner_radius=RADIO_BOTON_PEQUENO,
            fg_color=COLORES["rojo"],
            hover_color=COLORES["rojo_hover"],
            font=FONT["cuerpo_pequeno"],
            state="disabled",
            command=self._eliminar_seleccionado,
        )
        self._eliminar_btn.pack(side="left")
        if self.app._parking_selected:
            self._eliminar_btn.configure(state="normal")

    def _renderizar_resumen(self, parent):
        res = obtener_parqueaderos_resumen()
        res_frame = ctk.CTkFrame(parent, fg_color="transparent")
        res_frame.pack(fill="x", padx=PAD_CARD_X, pady=(0, 16))

        for titulo, valor, color in [
            ("Residentes libres", str(res["libres_residente"]), COLORES["verde_brillante"]),
            ("Visitantes libres", str(res["libres_visitante"]), COLORES["azul"]),
            ("Ocupados", str(res["ocupados"]), COLORES["rojo"]),
        ]:
            c = ctk.CTkFrame(
                res_frame,
                fg_color=COLORES["tarjeta"],
                corner_radius=RADIO_PANEL,
                border_width=BORDE_TARJETA,
                border_color=COLORES["borde"],
            )
            c.pack(side="left", expand=True, padx=10, fill="both")
            ctk.CTkLabel(
                c, text=titulo, font=FONT["tabla_dato"], text_color=COLORES["texto_3"]
            ).pack(pady=(12, 2))
            ctk.CTkLabel(
                c, text=valor, font=FONT["tarjeta_valor"], text_color=color
            ).pack(pady=(0, 12))

    def _renderizar_grids(self, parent):
        mapa = self.tarjeta(parent)
        mapa.pack(fill="both", expand=True, padx=PAD_CARD_X, pady=8)

        def build_zone(tipo, label):
            total = obtener_total_por_tipo(tipo)
            header = ctk.CTkFrame(mapa, fg_color="transparent")
            header.pack(fill="x", padx=24, pady=(16, 4))
            ctk.CTkLabel(
                header,
                text=f"ZONA {label} ({total} espacios)",
                font=FONT["titulo_seccion"],
                text_color=COLORES["texto_3"],
            ).pack(side="left")

            ctk.CTkButton(
                header,
                text="+ Agregar",
                width=100,
                height=28,
                corner_radius=RADIO_BOTON_PEQUENO,
                fg_color=COLORES["verde"],
                hover_color=COLORES["verde_hover"],
                font=FONT["cuerpo_pequeno"],
                command=lambda t=tipo: self._agregar_espacio(t),
            ).pack(side="right", padx=(0, 4))

            self._grid_parqueaderos(mapa, tipo)

        build_zone("residente", "RESIDENTES")

        calle = ctk.CTkFrame(mapa, height=32, fg_color=COLORES["panel"], corner_radius=6)
        calle.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(
            calle,
            text="◄  VÍA DE CIRCULACIÓN VEHICULAR  ►",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_3"],
        ).pack(expand=True)

        build_zone("visitante", "VISITANTES")

    def _grid_parqueaderos(self, parent, tipo: str):
        filas = obtener_parqueaderos_por_tipo(tipo)
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(padx=24, pady=4, fill="x")
        cols = PARKING_COLUMNAS

        for idx, row in enumerate(filas):
            col = idx % cols
            fila_idx = idx // cols
            num = row["numero"]

            if row["estado"] == "libre":
                is_selected = self.app._parking_selected == num
                fg = COLORES["azul"] if is_selected else "transparent"
                border_col = COLORES["azul"] if is_selected else COLORES["verde"]
                border_w = 3 if is_selected else 2
                txt_col = COLORES["boton_texto"] if is_selected else COLORES["verde_brillante"]
                hover = COLORES["parking_hover"]
            else:
                fg = COLORES["rojo"]
                border_col = COLORES["rojo_hover"]
                border_w = 1
                txt_col = COLORES["boton_texto"]
                hover = COLORES["rojo_hover"]

            texto = num

            btn = ctk.CTkButton(
                grid,
                text=texto,
                width=PARKING_BOTON_ANCHO,
                height=PARKING_BOTON_ALTURA,
                corner_radius=RADIO_BOTON,
                fg_color=fg,
                border_color=border_col,
                border_width=border_w,
                hover_color=hover,
                font=FONT["tabla_cabecera"],
                text_color=txt_col,
                command=lambda p=num, s=row["estado"], pl=row["placa"]: self._accion(p, s, pl),
            )
            btn.grid(row=fila_idx, column=col, padx=6, pady=6)
            self._slot_btns[num] = btn

    def _accion(self, numero: str, estado: str, placa: str | None):
        if estado == "ocupado":
            from CTkMessagebox import CTkMessagebox
            msg = f"Parqueadero {numero}\nPlaca: {placa or '—'}\n\n¿Liberar?"
            res = CTkMessagebox(
                title="Parqueadero ocupado", message=msg, icon="warning", option_1="Liberar", option_2="Cancelar"
            )
            if res.get() == "Liberar":
                liberar_parqueadero(numero)
                self.app._parking_selected = None
                self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)
        else:
            # Deselect previous slot
            prev = self.app._parking_selected
            if prev and prev in self._slot_btns:
                self._slot_btns[prev].configure(
                    fg_color="transparent",
                    border_color=COLORES["verde"],
                    border_width=2,
                    text_color=COLORES["verde_brillante"],
                )
            # Toggle current slot
            if prev == numero:
                self.app._parking_selected = None
                self._eliminar_btn.configure(state="disabled")
            else:
                self.app._parking_selected = numero
                btn = self._slot_btns[numero]
                btn.configure(
                    fg_color=COLORES["azul"],
                    border_color=COLORES["azul"],
                    border_width=3,
                    text_color=COLORES["boton_texto"],
                )
                self._eliminar_btn.configure(state="normal")

    def _agregar_espacio(self, tipo):
        exito, msg = agregar_parqueadero(tipo)
        self.notificar("ok" if exito else "aviso", "Parqueadero", msg)
        if exito:
            self.app._parking_selected = None
            self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)

    def _eliminar_seleccionado(self):
        if not self.app._parking_selected:
            return
        from CTkMessagebox import CTkMessagebox
        res = CTkMessagebox(
            title="Eliminar parqueadero",
            message=f"¿Eliminar {self.app._parking_selected}? Esta acción no se puede deshacer.",
            icon="warning",
            option_1="Eliminar",
            option_2="Cancelar",
        )
        if res.get() == "Eliminar":
            exito, msg = eliminar_parqueadero(self.app._parking_selected)
            self.notificar("ok" if exito else "error", "Eliminar", msg)
            self.app._parking_selected = None
            if exito:
                self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)

    def _crear_asignacion(self, parent):
        sec = self.tarjeta(parent)
        sec.pack(fill="x", padx=PAD_CARD_X, pady=PAD_BUTTON_ROW_Y)
        ctk.CTkLabel(
            sec,
            text="Asignar parqueadero a visitante",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 16))

        self._park_placa = self.entrada(fila, placeholder="Placa del vehículo", width=220)
        self._park_placa.pack(side="left", padx=(0, 12))

        self._park_numero = ctk.CTkComboBox(
            fila,
            width=160,
            state="readonly",
            values=obtener_parqueaderos_libres_visitante(),
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._park_numero.pack(side="left", padx=(0, 12))
        self._park_numero.set("Selecciona uno")

        self.boton(fila, "Asignar", self._asignar, width=140).pack(side="left")

    def _asignar(self):
        placa = self._park_placa.get().strip().upper()
        numero = self._park_numero.get().strip()

        if not placa or not numero or numero in ("Sin espacio", "Selecciona uno"):
            self.notificar("error", "Error", "Ingrese placa y seleccione un parqueadero")
            return

        if not validate_placa(placa):
            self.notificar("error", "Error", "Formato de placa inválido")
            return

        exito, msg = asignar_parqueadero(numero, placa, self.app.current_user)
        self.notificar("ok" if exito else "aviso", "Asignación", msg)
        if exito:
            self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)
