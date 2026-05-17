"""
Navigation sidebar and menu management for ResiControl.

Provides helper functions for creating navigation menus based on user roles.
"""

import customtkinter as ctk
from config import COLORES


CAMARA_DISPONIBLE = False
try:
    import cv2
    import pyzbar.pyzbar as pyzbar
    CAMARA_DISPONIBLE = True
except ImportError:
    pass


def get_menu_items(rol: str) -> list[tuple]:
    """
    Get the menu items based on user role.

    Args:
        rol: User role (admin, operador, residente)

    Returns:
        List of tuples: (menu_text, icon, method_reference)
    """
    menu = [
        ("Inicio", "H", "inicio"),
        ("Visitantes", "V", "visitantes"),
        ("Residentes", "R", "residentes"),
        ("Parqueaderos", "P", "parqueaderos"),
        ("Historial", "H", "historial"),
        ("Incidentes", "I", "incidentes"),
        ("Reportes PDF", "R", "reportes"),
    ]

    if rol == "admin":
        menu.append(("Usuarios", "U", "usuarios"))

    if CAMARA_DISPONIBLE:
        menu.insert(3, ("Escaneo QR", "Q", "qr"))

    menu.append(("Respaldos", "B", "backups"))
    menu.append(("Cerrar Sesión", "S", "logout"))

    return menu


def create_sidebar_menu(
    app,
    sidebar: ctk.CTkFrame,
    menu_items: list[tuple],
) -> dict[str, ctk.CTkButton]:
    """
    Create the sidebar menu with buttons.

    Args:
        app: The main ResiControl application
        sidebar: The sidebar CTkFrame
        menu_items: List of menu items from get_menu_items

    Returns:
        Dictionary mapping menu text to buttons
    """
    menu_btns: dict[str, ctk.CTkButton] = {}

    action_map = {
        "inicio": app._ir_inicio,
        "visitantes": app._ir_visitantes,
        "residentes": app._ir_residentes,
        "parqueaderos": app._ir_parqueaderos,
        "historial": app._ir_historial,
        "incidentes": app._ir_incidentes,
        "reportes": app._ir_reportes,
        "usuarios": app._ir_usuarios,
        "qr": app._ir_qr,
        "backups": app._ir_backups,
        "logout": app.mostrar_login,
    }

    for texto, _, cmd_key in menu_items:
        es_peligro = texto == "Cerrar Sesión"
        fg = COLORES["rojo"] if es_peligro else "transparent"
        hover = COLORES["rojo_hover"] if es_peligro else "#1f2937"
        accion = action_map.get(cmd_key, lambda: None)
        btn = ctk.CTkButton(
            sidebar,
            text=f"  {texto}",
            fg_color=fg,
            hover_color=hover,
            anchor="w",
            height=52,
            corner_radius=0,
            font=("Segoe UI", 13),
            text_color=COLORES["texto_2"],
            command=lambda t=texto, a=accion: app._cambiar_pagina(t, a),
        )
        btn.pack(fill="x", padx=12, pady=2)
        menu_btns[texto] = btn

    return menu_btns