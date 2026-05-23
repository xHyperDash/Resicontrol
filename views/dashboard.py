import customtkinter as ctk
from views.base import BaseView
from config import COLORES, FONT
from config import CABECERA_ALTURA, SECCION_RAPIDA_ALTURA, BORDE_TARJETA, RADIO_TARJETA
from models import obtener_metricas, obtener_entradas_por_hora_hoy, obtener_incidentes_por_nivel, obtener_dentro_desglose
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
        self._crear_graficos()
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

        self._renderizar_graficos()

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

    def _crear_graficos(self):
        self.graficos_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.graficos_frame.pack(fill="x", padx=32, pady=(0, 16))

        self._chart_lbls: dict[str, ctk.CTkLabel] = {}

        for titulo, key in [
            ("Entradas por hora (hoy)", "entradas_hora"),
            ("Incidentes (7 días)", "incidentes_nivel"),
            ("Dentro ahora", "dentro_ahora"),
        ]:
            card = ctk.CTkFrame(
                self.graficos_frame,
                fg_color=COLORES["tarjeta"],
                corner_radius=RADIO_TARJETA,
                border_width=BORDE_TARJETA,
                border_color=COLORES["borde"],
            )
            card.pack(side="left", expand=True, padx=6, fill="both")

            ctk.CTkLabel(
                card, text=titulo, font=FONT["tarjeta_titulo"],
                text_color=COLORES["texto_3"],
            ).pack(pady=(10, 0))

            lbl = ctk.CTkLabel(card, text="")
            lbl.pack(padx=8, pady=(4, 10), fill="both", expand=True)
            self._chart_lbls[key] = lbl

        self._renderizar_graficos()

    def _renderizar_graficos(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from io import BytesIO
        from PIL import Image

        plt.close("all")
        bg = "#1e293b"
        txt_color = "#f1f5f9"
        grid_color = "#334155"

        # 1. Entradas por hora
        data = obtener_entradas_por_hora_hoy()
        fig1 = Figure(figsize=(3.2, 1.8), dpi=100, facecolor=bg)
        ax1 = fig1.add_subplot(111, facecolor=bg)
        horas_labels = [f"{h:02d}" for h in range(24)]
        res_vals = [data.get(f"{h:02d}", {}).get("residente", 0) for h in range(24)]
        vis_vals = [data.get(f"{h:02d}", {}).get("visitante", 0) for h in range(24)]
        ax1.bar(horas_labels, res_vals, label="Residente", color="#00aaff", width=0.6)
        ax1.bar(horas_labels, vis_vals, bottom=res_vals, label="Visitante", color="#22c55e", width=0.6)
        ax1.tick_params(colors=txt_color, labelsize=6)
        ax1.set_xticks(range(0, 24, 3))
        ax1.set_xticklabels([f"{h:02d}" for h in range(0, 24, 3)], fontsize=5)
        ax1.set_ylabel("Entradas", color=txt_color, fontsize=6)
        for spine in ax1.spines.values():
            spine.set_color(grid_color)
        ax1.grid(axis="y", color=grid_color, linewidth=0.3)
        ax1.legend(fontsize=5, labelcolor=txt_color, facecolor=bg, edgecolor=grid_color)
        self._set_chart_image("entradas_hora", fig1)

        # 2. Incidentes por nivel
        inc = obtener_incidentes_por_nivel()
        fig2 = Figure(figsize=(1.7, 1.8), dpi=100, facecolor=bg)
        ax2 = fig2.add_subplot(111, facecolor=bg)
        niveles = ["bajo", "medio", "alto"]
        colores_nivel = {"bajo": "#22c55e", "medio": "#eab308", "alto": "#ef4444"}
        counts = [inc.get(n, 0) for n in niveles]
        bars2 = ax2.barh(niveles, counts, color=[colores_nivel[n] for n in niveles], height=0.5)
        for bar, val in zip(bars2, counts):
            ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=7, color=txt_color)
        ax2.tick_params(colors=txt_color, labelsize=6)
        ax2.set_xlabel("Cantidad", color=txt_color, fontsize=6)
        for spine in ax2.spines.values():
            spine.set_color(grid_color)
        ax2.grid(axis="x", color=grid_color, linewidth=0.3)
        self._set_chart_image("incidentes_nivel", fig2)

        # 3. Dentro ahora
        dd = obtener_dentro_desglose()
        fig3 = Figure(figsize=(1.7, 1.8), dpi=100, facecolor=bg)
        ax3 = fig3.add_subplot(111, facecolor=bg)
        cats = ["Residentes", "Visitantes"]
        vals3 = [dd["residente"], dd["visitante"]]
        col_dentro = ["#00aaff", "#22c55e"]
        bars3 = ax3.barh(cats, vals3, color=col_dentro, height=0.5)
        for bar, val in zip(bars3, vals3):
            ax3.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=7, color=txt_color)
        ax3.tick_params(colors=txt_color, labelsize=6)
        ax3.set_xlabel("Personas", color=txt_color, fontsize=6)
        for spine in ax3.spines.values():
            spine.set_color(grid_color)
        ax3.grid(axis="x", color=grid_color, linewidth=0.3)
        self._set_chart_image("dentro_ahora", fig3)

        plt.close("all")

    def _set_chart_image(self, attr_name: str, fig):  # fig: matplotlib.figure.Figure
        from io import BytesIO
        from PIL import Image
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100,
                    facecolor=fig.get_facecolor(), edgecolor="none")
        buf.seek(0)
        pil_img = Image.open(buf)
        ctk_img = ctk.CTkImage(pil_img, size=(pil_img.width, pil_img.height))
        lbl = self._chart_lbls.get(attr_name)
        if lbl and lbl.winfo_exists():
            lbl.configure(image=ctk_img)
        buf.close()
