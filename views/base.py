import customtkinter as ctk

from config import COLORES, FONT
from config import RADIO_TARJETA, RADIO_BOTON, RADIO_ENTRADA, RADIO_PANEL
from config import BOTON_ALTURA, ENTRADA_ALTURA, BORDE_TARJETA
from config import PAD_CABECERA_X, PAD_CABECERA_Y, PAD_CELDA_X, PAD_CELDA_Y


class BaseView(ctk.CTkFrame):
    """Base class for all view modules."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app

    def label_seccion(self, parent, texto: str) -> ctk.CTkLabel:
        """Create a section header label."""
        return ctk.CTkLabel(
            parent, text=texto, font=FONT["seccion"], text_color=COLORES["texto"]
        ).pack(pady=(24, 8))

    def tarjeta(self, parent, **kwargs) -> ctk.CTkFrame:
        """Create a card-style frame."""
        return ctk.CTkFrame(
            parent,
            fg_color=COLORES["tarjeta"],
            corner_radius=RADIO_TARJETA,
            border_width=BORDE_TARJETA,
            border_color=COLORES["borde"],
            **kwargs,
        )

    def boton(
        self,
        parent,
        texto: str,
        comando,
        color: str | None = None,
        hover: str | None = None,
        **kwargs,
    ) -> ctk.CTkButton:
        """Create a styled button."""
        color = color or COLORES["azul"]
        hover = hover or COLORES["azul_hover"]
        return ctk.CTkButton(
            parent,
            text=texto,
            command=comando,
            fg_color=color,
            hover_color=hover,
            corner_radius=RADIO_BOTON,
            height=BOTON_ALTURA,
            font=FONT["boton"],
            text_color=COLORES["boton_texto"],
            **kwargs,
        )

    def entrada(self, parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
        """Create a styled entry field."""
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color=COLORES["panel"],
            border_color=COLORES["borde_hover"],
            corner_radius=RADIO_ENTRADA,
            height=ENTRADA_ALTURA,
            font=FONT["cuerpo_pequeno"],
            **kwargs,
        )

    def notificar(self, tipo: str = "info", titulo: str = "", mensaje: str = "") -> None:
        """Show a non-blocking toast notification."""
        if hasattr(self.app, "toast"):
            self.app.toast.show(tipo, titulo, mensaje)

    def limpiar_contenido(self) -> None:
        """Clear all widgets from the content area."""
        if hasattr(self, "content"):
            for w in self.content.winfo_children():
                w.destroy()


def create_label_frame(parent, **kwargs) -> ctk.CTkFrame:
    """Create a transparent frame for layout purposes."""
    return ctk.CTkFrame(parent, fg_color="transparent", **kwargs)


def create_scrollable_frame(parent, height: int = 200, **kwargs) -> ctk.CTkScrollableFrame:
    """Create a styled scrollable frame."""
    return ctk.CTkScrollableFrame(
        parent,
        fg_color=COLORES["tarjeta"],
        corner_radius=RADIO_PANEL,
        height=height,
        **kwargs,
    )


def create_table_header(parent, columns: list[str]) -> None:
    """Create a table header row."""
    header_frame = ctk.CTkFrame(parent, fg_color=COLORES["tabla_header"], corner_radius=0)
    header_frame.pack(fill="x")
    for col in columns:
        ctk.CTkLabel(
            header_frame,
            text=col,
            font=FONT["tabla_cabecera"],
            text_color=COLORES["texto_3"],
        ).pack(side="left", expand=True, padx=PAD_CABECERA_X, pady=PAD_CABECERA_Y)


def create_table_row(parent, data: dict | list, index: int, keys: list[str] | None = None) -> None:
    """Create a table data row with alternating background colors."""
    bg = COLORES["panel"] if index % 2 == 0 else COLORES["tarjeta"]
    row_frame = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0)
    row_frame.pack(fill="x")

    if keys and isinstance(data, dict):
        values = [str(data.get(k, "—") or "—") for k in keys]
    elif isinstance(data, list):
        values = [str(v) if v is not None else "—" for v in data]
    else:
        values = ["—"]

    for val in values:
        ctk.CTkLabel(
            row_frame,
            text=val,
            font=FONT["tabla_dato"],
            text_color=COLORES["texto_2"],
        ).pack(side="left", expand=True, padx=PAD_CELDA_X, pady=PAD_CELDA_Y)
