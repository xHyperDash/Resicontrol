"""
Base view components and shared UI utilities for ResiControl.

Contains common CTkFrame components, button styles, entry fields,
and utility methods used across all view modules.
"""

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from config import COLORES


class BaseView(ctk.CTkFrame):
    """
    Base class for all view modules.
    Provides common UI components and utilities.
    """

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app

    def label_seccion(self, parent, texto: str) -> ctk.CTkLabel:
        """Create a section header label."""
        return ctk.CTkLabel(
            parent, text=texto, font=("Segoe UI", 26, "bold"), text_color=COLORES["texto"]
        ).pack(pady=(24, 8))

    def tarjeta(self, parent, **kwargs) -> ctk.CTkFrame:
        """Create a card-style frame."""
        return ctk.CTkFrame(
            parent,
            fg_color=COLORES["tarjeta"],
            corner_radius=14,
            border_width=1,
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
            corner_radius=10,
            height=46,
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff",
            **kwargs,
        )

    def entrada(self, parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
        """Create a styled entry field."""
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color="#111827",
            border_color=COLORES["borde_hover"],
            corner_radius=8,
            height=42,
            font=("Segoe UI", 13),
            **kwargs,
        )

    def notificar(self, tipo: str, titulo: str, mensaje: str) -> None:
        """Show a notification dialog."""
        iconos = {"ok": "check", "error": "cancel", "aviso": "warning", "info": "info"}
        CTkMessagebox(title=titulo, message=mensaje, icon=iconos.get(tipo, "info"))

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
        corner_radius=12,
        height=height,
        **kwargs,
    )


def create_table_header(parent, columns: list[str]) -> None:
    """Create a table header row."""
    header_frame = ctk.CTkFrame(parent, fg_color="#1e3a5f", corner_radius=0)
    header_frame.pack(fill="x")
    for col in columns:
        ctk.CTkLabel(
            header_frame,
            text=col,
            font=("Segoe UI", 12, "bold"),
            text_color=COLORES["texto_3"],
        ).pack(side="left", expand=True, padx=6, pady=8)


def create_table_row(parent, data: dict | list, index: int, keys: list[str] | None = None) -> None:
    """Create a table data row with alternating background colors."""
    bg = "#111827" if index % 2 == 0 else COLORES["tarjeta"]
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
            font=("Segoe UI", 12),
            text_color=COLORES["texto_2"],
        ).pack(side="left", expand=True, padx=6, pady=6)