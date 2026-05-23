from collections.abc import Callable
import customtkinter as ctk

from config import COLORES, FONT


class TableView(ctk.CTkFrame):
    """Reusable table component with header, alternating rows, and action buttons."""

    def __init__(
        self,
        parent,
        columns: list[str],
        data_callback: Callable[[], list[dict]] | None = None,
        key_map: dict[str, str] | None = None,
        actions: list[dict] | None = None,
        height: int = 280,
        searchable: bool = False,
        search_placeholder: str = "Buscar...",
        search_callback: Callable[[str], list[dict]] | None = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._columns = columns
        self._data_callback = data_callback
        self._key_map = key_map or {}
        self._actions = actions or []
        self._search_callback = search_callback
        self._search_text = ""

        scroll_kwargs = dict(fg_color=COLORES["tarjeta"], corner_radius=12, height=height)

        if searchable:
            top = ctk.CTkFrame(self, fg_color="transparent")
            top.pack(fill="x", padx=20, pady=(0, 8))

            self._search_entry = ctk.CTkEntry(
                top,
                placeholder_text=search_placeholder,
                fg_color=COLORES["panel"],
                border_color=COLORES["borde_hover"],
                corner_radius=8,
                height=42,
                font=FONT["cuerpo_pequeno"],
                width=340,
            )
            self._search_entry.pack(side="left", padx=(0, 10))

            ctk.CTkButton(
                top,
                text="Filtrar",
                command=self._on_search,
                fg_color=COLORES["azul"],
                hover_color=COLORES["azul_hover"],
                corner_radius=10,
                height=46,
                font=FONT["boton"],
                text_color=COLORES["boton_texto"],
                width=120,
            ).pack(side="left")

            self._frame = ctk.CTkScrollableFrame(self, **scroll_kwargs)
            self._frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        else:
            self._frame = ctk.CTkScrollableFrame(self, **scroll_kwargs)
            self._frame.pack(fill="both", expand=True)

        self._header = None
        self._render_header()
        self.refresh()

    def _render_header(self):
        self._header = ctk.CTkFrame(self._frame, fg_color=COLORES["tabla_header"], corner_radius=0)
        self._header.pack(fill="x")

        for col in self._columns:
            is_actions = col == "Acciones"
            ctk.CTkLabel(
                self._header,
                text=col,
                font=FONT["tabla_cabecera"],
                text_color=COLORES["texto_3"],
                width=80 if is_actions else None,
            ).pack(side="left", expand=not is_actions, padx=6, pady=8)

    def _on_search(self):
        self._search_text = self._search_entry.get().strip()
        self.refresh()

    def _get_key(self, col: str) -> str:
        return self._key_map.get(col, col.lower())

    def refresh(self):
        for w in self._frame.winfo_children():
            w.destroy()

        self._render_header()

        if self._search_callback and self._search_text:
            rows = self._search_callback(self._search_text)
        elif self._data_callback:
            rows = self._data_callback()
        else:
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._frame,
                text="No hay datos para mostrar",
                font=FONT["cuerpo"],
                text_color=COLORES["texto_3"],
            ).pack(pady=40)
            return

        for i, row in enumerate(rows):
            bg = COLORES["panel"] if i % 2 == 0 else COLORES["tarjeta"]
            f = ctk.CTkFrame(self._frame, fg_color=bg, corner_radius=0)
            f.pack(fill="x")

            for col in self._columns:
                if col == "Acciones":
                    actions_frame = ctk.CTkFrame(f, fg_color="transparent")
                    actions_frame.pack(side="left", padx=4)

                    for action in self._actions:
                        condition = action.get("condition")
                        if condition and not condition(row):
                            continue

                        ctk.CTkButton(
                            actions_frame,
                            text=action["label"],
                            width=action.get("width", 36),
                            height=action.get("height", 28),
                            corner_radius=action.get("radius", 6),
                            fg_color=action.get("color", COLORES["azul"]),
                            hover_color=action.get("hover", COLORES["azul_hover"]),
                            font=FONT["tabla_dato"],
                            command=lambda r=row, cb=action["callback"]: cb(r),
                        ).pack(side="left", padx=2)
                else:
                    key = self._get_key(col)
                    val = row.get(key, "—")
                    texto = str(val) if val is not None else "—"
                    ctk.CTkLabel(
                        f,
                        text=texto,
                        font=FONT["tabla_dato"],
                        text_color=COLORES["texto_2"],
                        wraplength=150,
                    ).pack(side="left", expand=True, padx=6, pady=6)
