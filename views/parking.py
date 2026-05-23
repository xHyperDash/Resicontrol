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
        self.label_seccion(self, "Parqueaderos")
        self._renderizar_resumen()
        self._renderizar_grids()
        self._crear_asignacion()

    def _renderizar_resumen(self):
        res = obtener_parqueaderos_resumen()
        res_frame = ctk.CTkFrame(self, fg_color="transparent")
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

    def _renderizar_grids(self):
        mapa = self.tarjeta(self)
        mapa.pack(fill="both", expand=True, padx=PAD_CARD_X, pady=8)

        # Residentes Grid Header
        ctk.CTkLabel(
            mapa,
            text="ZONA RESIDENTES (R01 - R10)",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=24, pady=(16, 4))

        self._grid_parqueaderos(mapa, "residente")

        # Access road / Street visual separator
        calle = ctk.CTkFrame(mapa, height=32, fg_color=COLORES["panel"], corner_radius=6)
        calle.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(
            calle,
            text="◄  VÍA DE CIRCULACIÓN VEHICULAR  ►",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_3"],
        ).pack(expand=True)

        # Visitantes Grid Header
        ctk.CTkLabel(
            mapa,
            text="ZONA VISITANTES (V01 - V10)",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=24, pady=(4, 4))

        self._grid_parqueaderos(mapa, "visitante")

    def _grid_parqueaderos(self, parent, tipo: str):
        filas = obtener_parqueaderos_por_tipo(tipo)
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(padx=24, pady=4, fill="x")
        cols = PARKING_COLUMNAS

        for idx, row in enumerate(filas):
            col = idx % cols
            fila_idx = idx // cols
            
            # Premium real-world parking blueprint styling
            if row["estado"] == "libre":
                fg = "transparent"
                border_col = COLORES["verde"]
                border_w = 2
                txt_col = COLORES["verde_brillante"]
                hover = COLORES["parking_hover"]
            else:
                fg = COLORES["rojo"]
                border_col = COLORES["rojo_hover"]
                border_w = 1
                txt_col = COLORES["boton_texto"]
                hover = COLORES["rojo_hover"]
                
            texto = row["numero"]

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
                command=lambda p=row["numero"], s=row["estado"], pl=row["placa"]: self._accion(p, s, pl),
            )
            btn.grid(row=fila_idx, column=col, padx=6, pady=6)

    def _accion(self, numero: str, estado: str, placa: str | None):
        from CTkMessagebox import CTkMessagebox

        if estado == "ocupado":
            msg = f"Parqueadero {numero}\nPlaca: {placa or '—'}\n\n¿Liberar?"
            res = CTkMessagebox(
                title="Parqueadero ocupado", message=msg, icon="warning", option_1="Liberar", option_2="Cancelar"
            )
            if res.get() == "Liberar":
                liberar_parqueadero(numero)
                self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)
        else:
            self.notificar("info", "Parqueadero libre", f"{numero} está disponible")

    def _crear_asignacion(self):
        sec = self.tarjeta(self)
        sec.pack(fill="x", padx=PAD_CARD_X, pady=PAD_BUTTON_ROW_Y)
        ctk.CTkLabel(
            sec,
            text="Asignar parqueadero a visitante",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 16))

        # Vertical alignment for forms: label stack could be added but since this is inline, let's make it highly spacious
        self._park_placa = self.entrada(fila, placeholder="Placa del vehículo", width=220)
        self._park_placa.pack(side="left", padx=(0, 12))

        self._park_numero = ctk.CTkComboBox(
            fila,
            width=160,
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

        self.boton(fila, "Asignar", self._asignar, width=140).pack(side="left")

    def _asignar(self):
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
            self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)
