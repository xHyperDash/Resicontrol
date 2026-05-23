import customtkinter as ctk
from views.base import BaseView
from config import COLORES, FONT
from config import CABECERA_ALTURA, SECCION_RAPIDA_ALTURA, BORDE_TARJETA, RADIO_TARJETA
from models import obtener_metricas
from icons import get_icon


class DashboardView(BaseView):
    """Dashboard view showing metrics and quick actions."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self.metric_labels = {}  # Store references to update metric values dynamically
        self._crear_vista()

    def _crear_vista(self):
        self._crear_header()
        self._crear_metricas()
        self._crear_accesos_rapidos()

    def _crear_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORES["tarjeta"], height=CABECERA_ALTURA, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"Bienvenido, {self.app.current_user.upper()}",
            font=FONT["bienvenida"],
            text_color=COLORES["acento"],
        ).pack(pady=18)

    def _crear_metricas(self):
        self.metricas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metricas_frame.pack(fill="x", padx=32, pady=(24, 16))

        m = obtener_metricas()
        datos = [
            ("Entradas hoy", str(m["entradas_hoy"]), COLORES["verde_brillante"]),
            ("Residentes", str(m["residentes"]), COLORES["azul"]),
            ("Parqueaderos oc.", str(m["ocupados"]), COLORES["amarillo"]),
            ("Dentro ahora", str(m["dentro"]), COLORES["rojo"]),
        ]

        for titulo, valor, color in datos:
            self._crear_tarjeta_metrica(titulo, valor, color)

        if self.app.current_page == "Inicio":
            self.after(10000, self._actualizar_metricas)

    def _crear_tarjeta_metrica(self, titulo: str, valor: str, color: str):
        card = ctk.CTkFrame(
            self.metricas_frame,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_TARJETA,
            border_width=BORDE_TARJETA,
            border_color=COLORES["borde"],
        )
        card.pack(side="left", expand=True, padx=10, fill="both")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            top, text=titulo, font=FONT["tarjeta_titulo"], text_color=COLORES["texto_3"]
        ).pack(side="left")

        # Resolve clean premium icon for each metric
        icon_name = "visitantes"
        if "Residente" in titulo:
            icon_name = "residentes"
        elif "Parqueadero" in titulo:
            icon_name = "parqueaderos"
        elif "Dentro" in titulo:
            icon_name = "inicio"

        icon = get_icon(icon_name, size=22, color=color)
        ctk.CTkLabel(
            top, text="", image=icon
        ).pack(side="right")

        val_lbl = ctk.CTkLabel(
            card, text=valor, font=FONT["tarjeta_valor"], text_color=COLORES["texto"]
        )
        val_lbl.pack(pady=(4, 14))
        
        # Save reference to update dynamically without reconstructing the frame
        self.metric_labels[titulo] = val_lbl

    def _actualizar_metricas(self):
        if self.app.current_page != "Inicio" or not hasattr(self, "metric_labels"):
            return
        
        m = obtener_metricas()
        
        mapping = {
            "Entradas hoy": str(m["entradas_hoy"]),
            "Residentes": str(m["residentes"]),
            "Parqueaderos oc.": str(m["ocupados"]),
            "Dentro ahora": str(m["dentro"]),
        }

        for titulo, valor in mapping.items():
            if titulo in self.metric_labels:
                lbl = self.metric_labels[titulo]
                if lbl.winfo_exists():
                    lbl.configure(text=valor)

        # Reschedule next check safely
        self.after(10000, self._actualizar_metricas)

    def _crear_accesos_rapidos(self):
        sec = self.tarjeta(self)
        sec.pack(fill="x", padx=32, pady=(0, 24))
        sec.pack_propagate(False)
        sec.configure(height=SECCION_RAPIDA_ALTURA)

        ctk.CTkLabel(
            sec,
            text="Accesos rápidos",
            font=FONT["boton"],
            text_color=COLORES["texto_3"],
        ).pack(anchor="w", padx=20, pady=(8, 4))

        fila = ctk.CTkFrame(sec, fg_color="transparent")
        fila.pack(padx=16)

        botones = [
            ("Visitantes", COLORES["azul"], "Visitantes", self.app._ir_visitantes, "visitantes"),
            ("Residentes", COLORES["azul_hover"], "Residentes", self.app._ir_residentes, "residentes"),
            ("Parqueaderos", COLORES["verde"], "Parqueaderos", self.app._ir_parqueaderos, "parqueaderos"),
            ("Historial", COLORES["amarillo"], "Historial", self.app._ir_historial, "historial"),
            ("Reportes", COLORES["azul_oscuro"], "Reporte", self.app._ir_reportes, "reportes"),
        ]

        for texto, color, nombre, cmd, icon_name in botones:
            btn_icon = get_icon(icon_name, size=18, color=COLORES["boton_texto"])
            ctk.CTkButton(
                fila,
                text=f"  {texto}",
                image=btn_icon,
                compound="left",
                width=160,
                height=44,
                corner_radius=10,
                fg_color=color,
                hover_color=COLORES["hover_generico"],
                font=FONT["tabla_cabecera"],
                text_color=COLORES["boton_texto"],
                command=lambda n=nombre, c=cmd: self.app._cambiar_pagina(n, c),
            ).pack(side="left", padx=8)
