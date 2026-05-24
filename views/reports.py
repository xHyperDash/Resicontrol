import customtkinter as ctk
from datetime import datetime

from views.base import BaseView
from config import COLORES, FONT
from config import PAD_CARD_X, PAD_CARD_Y, PAD_FORM_X, PAD_FORM_Y, ENTRADA_ALTURA
from report_generator import generar_pdf
from qr_manager import abrir_archivo as abrir_archivo_qr


class ReportsView(BaseView):
    """View for PDF report generation."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self._crear_vista()

    def _crear_vista(self):
        self.label_seccion(self, "Generación de Reportes")
        card = self.tarjeta(self)
        card.pack(fill="x", padx=PAD_CARD_X, pady=PAD_CARD_Y)

        self._crear_formulario(card)

    def _crear_formulario(self, parent):
        opciones = ctk.CTkFrame(parent, fg_color="transparent")
        opciones.pack(pady=PAD_FORM_Y, padx=40, fill="x")

        icono_calendario = "\U0001F4C5"

        ctk.CTkLabel(
            opciones,
            text="Fecha inicio:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=0, column=0, sticky="w", pady=(8, 2))

        fila_ini = ctk.CTkFrame(opciones, fg_color="transparent")
        fila_ini.grid(row=1, column=0, sticky="w", pady=(0, 8))
        self._rep_fecha_ini = self.entrada(fila_ini, placeholder="YYYY-MM-DD", width=220)
        self._rep_fecha_ini.pack(side="left")
        self._rep_fecha_ini.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkButton(
            fila_ini, text=icono_calendario, width=36, height=ENTRADA_ALTURA or 28,
            fg_color=COLORES["tarjeta"], hover_color=COLORES["borde"],
            font=FONT["cuerpo_pequeno"],
            command=lambda: self._abrir_calendario(self._rep_fecha_ini),
        ).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(
            opciones,
            text="Fecha fin:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=2, column=0, sticky="w", pady=(8, 2))

        fila_fin = ctk.CTkFrame(opciones, fg_color="transparent")
        fila_fin.grid(row=3, column=0, sticky="w", pady=(0, 8))
        self._rep_fecha_fin = self.entrada(fila_fin, placeholder="YYYY-MM-DD", width=220)
        self._rep_fecha_fin.pack(side="left")
        self._rep_fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkButton(
            fila_fin, text=icono_calendario, width=36, height=ENTRADA_ALTURA or 28,
            fg_color=COLORES["tarjeta"], hover_color=COLORES["borde"],
            font=FONT["cuerpo_pequeno"],
            command=lambda: self._abrir_calendario(self._rep_fecha_fin),
        ).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(
            opciones,
            text="Tipo de accesos:",
            font=FONT["pequeno_bold"],
            text_color=COLORES["texto_2"],
        ).grid(row=4, column=0, sticky="w", pady=(8, 2))

        self._rep_tipo = ctk.CTkComboBox(
            opciones,
            values=["Todos", "residente", "visitante"],
            width=220,
            state="readonly",
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
        )
        self._rep_tipo.grid(row=5, column=0, sticky="w", pady=(0, 16))
        self._rep_tipo.set("Selecciona uno")

        self.boton(
            parent,
            "Generar PDF",
            self._generar_pdf,
            color=COLORES["azul_oscuro"],
            hover=COLORES["azul_hover"],
            width=260,
        ).pack(pady=PAD_FORM_Y)

    def _abrir_calendario(self, entrada_objetivo):
        from calendar import monthcalendar, month_name
        top = ctk.CTkToplevel(self.app)
        top.title("Seleccionar fecha")
        top.geometry("300x280")
        top.configure(fg_color=COLORES["panel"])
        top.transient(self.app)
        top.grab_set()
        top.resizable(False, False)

        ahora = datetime.now()
        año = ahora.year
        mes = ahora.month

        def actualizar_calendario():
            for w in marco_dias.winfo_children():
                w.destroy()
            for di, dia in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]):
                ctk.CTkLabel(marco_dias, text=dia, font=FONT["pequeno_bold"],
                             text_color=COLORES["texto_3"], width=36).grid(row=0, column=di, padx=1, pady=1)
            for si, semana in enumerate(monthcalendar(año, mes)):
                for di, dia in enumerate(semana):
                    if dia == 0:
                        ctk.CTkLabel(marco_dias, text="", width=36).grid(row=si+1, column=di, padx=1, pady=1)
                    else:
                        ctk.CTkButton(
                            marco_dias, text=str(dia), width=36, height=28,
                            fg_color="transparent", text_color=COLORES["texto"],
                            hover_color=COLORES["sidebar_hover"], corner_radius=4,
                            font=FONT["tabla_dato"],
                            command=lambda d=dia: seleccionar(d),
                        ).grid(row=si+1, column=di, padx=1, pady=1)
            lbl_mes.configure(text=f"{month_name[mes]} {año}")

        def mes_anterior():
            nonlocal año, mes
            mes -= 1
            if mes == 0:
                mes = 12
                año -= 1
            actualizar_calendario()

        def mes_siguiente():
            nonlocal año, mes
            mes += 1
            if mes == 13:
                mes = 1
                año += 1
            actualizar_calendario()

        def seleccionar(dia):
            fecha = f"{año:04d}-{mes:02d}-{dia:02d}"
            entrada_objetivo.delete(0, "end")
            entrada_objetivo.insert(0, fecha)
            top.destroy()

        nav = ctk.CTkFrame(top, fg_color="transparent")
        nav.pack(pady=(12, 4))
        ctk.CTkButton(nav, text="<", width=32, height=28,
                      fg_color="transparent", text_color=COLORES["texto"],
                      hover_color=COLORES["sidebar_hover"], command=mes_anterior).pack(side="left", padx=2)
        lbl_mes = ctk.CTkLabel(nav, text="", font=FONT["dialogo_titulo"], text_color=COLORES["texto"])
        lbl_mes.pack(side="left", padx=12)
        ctk.CTkButton(nav, text=">", width=32, height=28,
                      fg_color="transparent", text_color=COLORES["texto"],
                      hover_color=COLORES["sidebar_hover"], command=mes_siguiente).pack(side="left", padx=2)

        marco_dias = ctk.CTkFrame(top, fg_color="transparent")
        marco_dias.pack(padx=12, pady=(0, 12))
        actualizar_calendario()

    def _generar_pdf(self):
        fecha_ini = self._rep_fecha_ini.get().strip()
        fecha_fin = self._rep_fecha_fin.get().strip()
        tipo = self._rep_tipo.get()

        if tipo == "Selecciona uno":
            self.notificar("aviso", "Tipo requerido", "Seleccione un tipo de acceso")
            return

        try:
            datetime.strptime(fecha_ini, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            self.notificar("error", "Fecha inválida", "Use el formato YYYY-MM-DD")
            return

        exito, msg = generar_pdf(fecha_ini, fecha_fin, tipo, self.app.current_user)
        if exito:
            abrir_archivo_qr(msg)
        self.notificar("ok" if exito else "error", "Reporte", msg)
