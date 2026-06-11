import customtkinter as ctk

from views.base import BaseView
from config import COLORES, FONT
from config import PARKING_BOTON_ANCHO, PARKING_BOTON_ALTURA, PARKING_COLUMNAS
from config import RADIO_PANEL, RADIO_BOTON, RADIO_BOTON_PEQUENO, BORDE_TARJETA, BOTON_PEQUENO_ALTURA
from config import PAD_CARD_X, PAD_LIST_BOTTOM, PAD_SECTION_LABEL_X, PAD_BUTTON_ROW_Y

from models import (
    obtener_parqueaderos_resumen,
    obtener_parqueaderos_por_tipo,
    obtener_total_por_tipo,
    agregar_parqueadero,
    eliminar_parqueadero,
    asignar_parqueadero,
    liberar_parqueadero,
    obtener_residentes,
    obtener_visitantes_activos,
)


VERDE_CLARO = "#6ee7b7"

class ParkingView(BaseView):
    """View for parking lot management."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        if not hasattr(self.app, "_parking_selected"):
            self.app._parking_selected = None
        if getattr(self.app, "_parking_recargando", False):
            self._edit_mode = bool(getattr(self.app, "_parking_edit_mode", False))
            self._edit_selected = getattr(self.app, "_parking_edit_selected", set())
            self.app._parking_recargando = False
        else:
            self.app._parking_edit_mode = False
            self.app._parking_edit_selected = set()
            self._edit_mode = False
            self._edit_selected = set()
        self._slot_btns: dict[str, ctk.CTkButton] = {}
        self._crear_vista()

    def _crear_vista(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.label_seccion(scroll, "Parqueaderos")
        self._renderizar_resumen(scroll)
        self._crear_toolbar(scroll)
        self._renderizar_grids(scroll)
        self._crear_edit_panel(scroll)
        self._crear_asignacion(scroll)
        if self._edit_mode:
            self._edit_panel.pack(fill="x", padx=PAD_CARD_X, pady=PAD_BUTTON_ROW_Y)
        else:
            self._asignacion_card.pack(fill="x", padx=PAD_CARD_X)

    def _crear_toolbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=PAD_CARD_X, pady=(0, 8))
        self._edit_btn = ctk.CTkButton(
            bar,
            text="Editar",
            width=120,
            height=30,
            corner_radius=RADIO_BOTON_PEQUENO,
            fg_color=COLORES["acento"] if self._edit_mode else "transparent",
            hover_color=COLORES["azul_hover"],
            font=FONT["cuerpo_pequeno"],
            text_color=COLORES["boton_texto"] if self._edit_mode else COLORES["texto_3"],
            border_width=1 if not self._edit_mode else 0,
            border_color=COLORES["borde"] if not self._edit_mode else COLORES["panel"],
            command=self._toggle_edit,
        )
        self._edit_btn.pack(side="left")
        self._edit_hint = ctk.CTkLabel(
            bar, text="", font=FONT["cuerpo_pequeno"], text_color=COLORES["amarillo"],
        )
        self._edit_hint.pack(side="left", padx=12)
        if self._edit_mode:
            self._edit_hint.configure(text="Seleccione espacios libres para eliminar. Use los campos abajo para agregar.")

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
                if self._edit_mode:
                    is_selected = num in self._edit_selected
                    fg = VERDE_CLARO if is_selected else "transparent"
                    border_col = VERDE_CLARO if is_selected else COLORES["verde"]
                    border_w = 3 if is_selected else 2
                    txt_col = COLORES["panel"] if is_selected else COLORES["verde_brillante"]
                    hover = COLORES["parking_hover"]
                else:
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
        elif self._edit_mode:
            # Toggle in/out of edit selection (lighter green)
            if numero in self._edit_selected:
                self._edit_selected.remove(numero)
                if numero in self._slot_btns:
                    self._slot_btns[numero].configure(
                        fg_color="transparent",
                        border_color=COLORES["verde"],
                        border_width=2,
                        text_color=COLORES["verde_brillante"],
                    )
            else:
                self._edit_selected.add(numero)
                if numero in self._slot_btns:
                    self._slot_btns[numero].configure(
                        fg_color=VERDE_CLARO,
                        border_color=VERDE_CLARO,
                        border_width=3,
                        text_color=COLORES["panel"],
                    )
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
            else:
                self.app._parking_selected = numero
                btn = self._slot_btns[numero]
                btn.configure(
                    fg_color=COLORES["azul"],
                    border_color=COLORES["azul"],
                    border_width=3,
                    text_color=COLORES["boton_texto"],
                )

            # Fill parking slot entry in assignment form
            if hasattr(self, "_park_slot_entry"):
                self._park_slot_entry.delete(0, "end")
                if self.app._parking_selected:
                    self._park_slot_entry.insert(0, numero)

    # ─── Edit mode ───────────────────────────────────────────────────────────

    def _recargar(self):
        self.app._parking_recargando = True
        self.app._parking_edit_mode = self._edit_mode
        self.app._parking_edit_selected = self._edit_selected
        self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)

    def _toggle_edit(self):
        self._edit_mode = not self._edit_mode
        if not self._edit_mode:
            self._edit_selected.clear()
        else:
            self.app._parking_selected = None
        self._recargar()

    def _crear_edit_panel(self, parent):
        self._edit_panel = ctk.CTkFrame(parent, fg_color="transparent")

        card = self.tarjeta(self._edit_panel)
        card.pack(fill="x")

        ctk.CTkLabel(
            card,
            text="Agregar espacios",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        input_row = ctk.CTkFrame(card, fg_color="transparent")
        input_row.pack(fill="x", padx=20, pady=6)
        input_row.grid_columnconfigure(0, weight=1)
        input_row.grid_columnconfigure(1, weight=1)

        r_frame = ctk.CTkFrame(input_row, fg_color="transparent")
        r_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(
            r_frame, text="Residentes:", font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_2"],
        ).pack(side="left", padx=(0, 8))
        self._bulk_r_entry = ctk.CTkEntry(
            r_frame, font=FONT["cuerpo"],
            fg_color=COLORES["panel"], border_color=COLORES["borde"],
            text_color=COLORES["texto"], placeholder_text="N",
        )
        self._bulk_r_entry.pack(side="left", fill="x", expand=True)

        v_frame = ctk.CTkFrame(input_row, fg_color="transparent")
        v_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(
            v_frame, text="Visitantes:", font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_2"],
        ).pack(side="left", padx=(0, 8))
        self._bulk_v_entry = ctk.CTkEntry(
            v_frame, font=FONT["cuerpo"],
            fg_color=COLORES["panel"], border_color=COLORES["borde"],
            text_color=COLORES["texto"], placeholder_text="N",
        )
        self._bulk_v_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            card,
            text=f"{'—' * 50}",
            font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_3"],
        ).pack(pady=8)

        fila_submit = ctk.CTkFrame(card, fg_color="transparent")
        fila_submit.pack(pady=(4, 16))
        self.boton(
            fila_submit, "Guardar cambios de edición", self._submit_edit,
            width=240, color=COLORES["verde"],
        ).pack()

    def _agregar_bulk(self, tipo, entry):
        try:
            n = int(entry.get().strip())
        except (ValueError, AttributeError):
            self.notificar("error", "Error", "Ingrese un número válido")
            return
        if n < 1:
            self.notificar("error", "Error", "Debe agregar al menos 1 espacio")
            return

        agregados = 0
        for _ in range(n):
            exito, msg = agregar_parqueadero(tipo)
            if not exito:
                if agregados > 0:
                    self.notificar("aviso", "Límite", f"Se agregaron {agregados}, luego: {msg}")
                else:
                    self.notificar("aviso", "Límite", msg)
                break
            agregados += 1

        if agregados > 0:
            self.notificar("ok", "Agregar", f"{agregados} espacio(s) agregado(s)")
            self._recargar()

    def _submit_edit(self):
        n_add_r = 0
        try:
            n_add_r = max(0, int(self._bulk_r_entry.get().strip()))
        except (ValueError, AttributeError):
            n_add_r = 0
        n_add_v = 0
        try:
            n_add_v = max(0, int(self._bulk_v_entry.get().strip()))
        except (ValueError, AttributeError):
            n_add_v = 0
        n_del = len(self._edit_selected)
        if n_add_r == 0 and n_add_v == 0 and n_del == 0:
            self.notificar("aviso", "Sin cambios", "No hay cambios para guardar")
            return

        partes = []
        if n_add_r > 0:
            partes.append(f"Agregar {n_add_r} residente(s)")
        if n_add_v > 0:
            partes.append(f"Agregar {n_add_v} visitante(s)")
        if n_del > 0:
            partes.append(f"Eliminar {n_del} espacio(s)")
        msg = ". ".join(partes) + ". ¿Confirmar?"

        from CTkMessagebox import CTkMessagebox
        res = CTkMessagebox(
            title="Confirmar edición",
            message=msg,
            icon="question",
            option_1="Confirmar",
            option_2="Cancelar",
        )
        if res.get() != "Confirmar":
            return

        for num in list(self._edit_selected):
            eliminar_parqueadero(num)

        for tipo, n in [("residente", n_add_r), ("visitante", n_add_v)]:
            for _ in range(n):
                agregar_parqueadero(tipo)

        self._edit_mode = False
        self._edit_selected.clear()
        self._recargar()

    # ─── Asignación ──────────────────────────────────────────────────────────

    COL_PARK_ASIGN_ANCHOS = [70, 200, 130, 120, 80, 110, 90]

    def _crear_asignacion(self, parent):
        self._asignacion_card = ctk.CTkFrame(parent, fg_color="transparent")
        sec = self.tarjeta(self._asignacion_card)
        sec.pack(fill="x")
        ctk.CTkLabel(
            sec,
            text="Asignar parqueadero",
            font=FONT["titulo_seccion"],
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 6))

        # Filtros
        filtros = ctk.CTkFrame(sec, fg_color="transparent")
        filtros.pack(fill="x", padx=20, pady=(0, 8))

        self._park_busq_var = ctk.StringVar()
        self._park_busq_var.trace_add("write", lambda *_: self._poblar_tabla_asignacion())
        ctk.CTkEntry(
            filtros,
            textvariable=self._park_busq_var,
            placeholder_text="Buscar por nombre, cédula o placa...",
            width=260,
            font=FONT["cuerpo"],
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            text_color=COLORES["texto"],
            placeholder_text_color=COLORES["texto_2"],
        ).pack(side="left", padx=(0, 10))

        self._park_filtro_tipo = ctk.CTkComboBox(
            filtros,
            values=["Residentes", "Visitantes"],
            width=140,
            state="readonly",
            fg_color=COLORES["panel"],
            border_color=COLORES["borde"],
            button_color=COLORES["tarjeta"],
            button_hover_color=COLORES["borde"],
            dropdown_fg_color=COLORES["panel"],
            dropdown_hover_color=COLORES["borde"],
            dropdown_text_color=COLORES["texto"],
            command=lambda _: self._poblar_tabla_asignacion(),
        )
        self._park_filtro_tipo.pack(side="left")
        self._park_filtro_tipo.set("Residentes")

        # Tabla de personas
        self._park_tabla = ctk.CTkScrollableFrame(
            sec,
            fg_color="transparent",
            height=200,
            scrollbar_button_color=COLORES["borde"],
            scrollbar_button_hover_color=COLORES["borde_hover"],
            scrollbar_fg_color="transparent",
        )
        self._park_tabla.pack(fill="x", padx=20, pady=6)

        # Read-only form for selected person
        form_card = ctk.CTkFrame(sec, fg_color=COLORES["panel"], corner_radius=8)
        form_card.pack(fill="x", padx=20, pady=(4, 8))
        self._park_form_entries = {}
        campos = [("Nombre", "nombre"), ("Cédula", "cedula"), ("Placa", "placa"), ("Unidad", "unidad")]
        for ci, (label, key) in enumerate(campos):
            ctk.CTkLabel(
                form_card, text=label, font=FONT["pequeno_bold"],
                text_color=COLORES["texto_2"],
            ).grid(row=0, column=ci * 2, padx=(16 if ci == 0 else 4, 0), pady=12, sticky="w")
            e = ctk.CTkEntry(
                form_card, width=160, font=FONT["cuerpo"],
                fg_color=COLORES["tarjeta"], text_color=COLORES["texto"],
                border_color=COLORES["borde"], state="readonly",
            )
            e.grid(row=0, column=ci * 2 + 1, padx=4, pady=12, sticky="w")
            self._park_form_entries[key] = e

        # Assign row: parking slot entry + button
        assign_row = ctk.CTkFrame(sec, fg_color="transparent")
        assign_row.pack(fill="x", padx=20, pady=(0, 16))

        self._park_slot_entry = ctk.CTkEntry(
            assign_row, width=160, font=FONT["cuerpo"],
            placeholder_text="Parqueadero #",
            fg_color=COLORES["panel"], text_color=COLORES["texto"],
            border_color=COLORES["borde"],
        )
        self._park_slot_entry.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            assign_row, text="Limpiar", width=100, height=30,
            corner_radius=RADIO_BOTON_PEQUENO,
            fg_color=COLORES["rojo"], hover_color=COLORES["rojo_hover"],
            font=FONT["cuerpo_pequeno"],
            command=self._limpiar_asignacion,
        ).pack(side="left", padx=(0, 12))

        self.boton(assign_row, "Asignar", self._asignar, width=120).pack(side="left")

        self._poblar_tabla_asignacion()

    def _poblar_tabla_asignacion(self, *args):
        for w in self._park_tabla.winfo_children():
            w.destroy()

        busq = self._park_busq_var.get().strip()
        tipo = self._park_filtro_tipo.get()

        import sqlite3
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        ocupados = {
            r[0].upper(): r[1]
            for r in conn.execute(
                "SELECT placa, numero FROM parqueaderos WHERE estado='ocupado' AND placa IS NOT NULL"
            ).fetchall()
        }
        conn.close()

        if tipo == "Residentes":
            datos = obtener_residentes(filtro=busq)
            enc = ["Tipo", "Nombre", "Cédula", "Placa", "Unidad", "Parqueadero", "Acción"]
        else:
            datos = obtener_visitantes_activos()
            if busq:
                b = busq.lower()
                datos = [d for d in datos if b in d.get("nombre", "").lower() or b in d.get("cedula", "").lower() or b in d.get("placa", "").lower()]
            enc = ["Tipo", "Nombre", "Cédula", "Placa", "Unidad", "Parqueadero", "Acción"]

        header = ctk.CTkFrame(self._park_tabla, fg_color=COLORES["tabla_header"], corner_radius=0)
        header.pack(fill="x")
        for ci, h in enumerate(enc):
            ctk.CTkLabel(
                header, text=h, width=self.COL_PARK_ASIGN_ANCHOS[ci],
                font=FONT["tabla_cabecera"], text_color=COLORES["texto_3"],
            ).pack(side="left", padx=2, pady=8)

        for i, r in enumerate(datos):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._park_tabla, fg_color=bg, corner_radius=6)
            f.pack(fill="x", pady=2, padx=4)

            placa = (r.get("placa") or "").upper()
            parq = ocupados.get(placa, "—")

            tipo_texto = "Residente" if tipo == "Residentes" else "Visitante"
            vals = [
                tipo_texto,
                r.get("nombre", ""),
                r.get("cedula", ""),
                placa,
                str(r.get("unidad", "") or ""),
                parq,
            ]
            for ci, val in enumerate(vals):
                ctk.CTkLabel(
                    f, text=val, width=self.COL_PARK_ASIGN_ANCHOS[ci],
                    font=FONT["tabla_dato"], text_color=COLORES["texto_2"],
                ).pack(side="left", padx=2, pady=6)

            ctk.CTkButton(
                f, text="Seleccionar", width=self.COL_PARK_ASIGN_ANCHOS[6],
                height=BOTON_PEQUENO_ALTURA, corner_radius=RADIO_BOTON_PEQUENO,
                fg_color=COLORES["acento"], hover_color=COLORES["azul_hover"],
                font=FONT["tabla_dato"],
                command=lambda d=r: self._seleccionar_persona(d),
            ).pack(side="left", padx=2, pady=4)

    def _seleccionar_persona(self, datos):
        nombre = datos.get("nombre", "")
        placa = datos.get("placa", "")
        cedula = datos.get("cedula", "")
        unidad = datos.get("unidad", "") or datos.get("invitado_por", "") or ""
        self._selected_person = {"nombre": nombre, "placa": placa, "cedula": cedula, "unidad": unidad}

        self._park_form_entries["nombre"].configure(state="normal")
        self._park_form_entries["nombre"].delete(0, "end")
        self._park_form_entries["nombre"].insert(0, nombre)
        self._park_form_entries["nombre"].configure(state="readonly")

        self._park_form_entries["cedula"].configure(state="normal")
        self._park_form_entries["cedula"].delete(0, "end")
        self._park_form_entries["cedula"].insert(0, cedula)
        self._park_form_entries["cedula"].configure(state="readonly")

        self._park_form_entries["placa"].configure(state="normal")
        self._park_form_entries["placa"].delete(0, "end")
        self._park_form_entries["placa"].insert(0, placa)
        self._park_form_entries["placa"].configure(state="readonly")

        self._park_form_entries["unidad"].configure(state="normal")
        self._park_form_entries["unidad"].delete(0, "end")
        self._park_form_entries["unidad"].insert(0, unidad)
        self._park_form_entries["unidad"].configure(state="readonly")

        self.notificar("ok", "Seleccionado", nombre)

    def _limpiar_asignacion(self):
        self._selected_person = None
        for key in self._park_form_entries:
            self._park_form_entries[key].configure(state="normal")
            self._park_form_entries[key].delete(0, "end")
            self._park_form_entries[key].configure(state="readonly")
        self._park_slot_entry.delete(0, "end")

    def _asignar(self):
        if not hasattr(self, "_selected_person") or not self._selected_person:
            self.notificar("error", "Error", "Seleccione una persona primero")
            return

        placa = self._selected_person["placa"]
        if not placa:
            self.notificar("error", "Error", "La persona seleccionada no tiene placa registrada")
            return

        numero = self._park_slot_entry.get().strip().upper()
        if not numero:
            self.notificar("error", "Error", "Haga clic en un parqueadero libre para seleccionarlo")
            return

        exito, msg = asignar_parqueadero(numero, placa, self.app.current_user)
        self.notificar("ok" if exito else "aviso", "Asignación", msg)
        if exito:
            self.app._cambiar_pagina("Parqueaderos", self.app._ir_parqueaderos)
