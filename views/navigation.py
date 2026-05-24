import customtkinter as ctk
from config import COLORES, FONT
from icons import get_icon


CAMARA_DISPONIBLE = False
try:
    import cv2
    import pyzbar.pyzbar as pyzbar
    CAMARA_DISPONIBLE = True
except ImportError:
    pass


def get_menu_items(rol: str) -> list[tuple]:
    menu: list[tuple] = [
        ("Inicio", "inicio", "inicio"),
        ("Visitantes", "visitantes", "visitantes"),
        ("Residentes", "residentes", "residentes"),
        ("Parqueaderos", "parqueaderos", "parqueaderos"),
        ("Historial", "historial", "historial"),
        ("Incidentes", "incidentes", "incidentes"),
        ("Reportes PDF", "reportes", "reportes"),
    ]

    if rol == "admin":
        menu.append(("Usuarios", "usuarios", "usuarios"))

    if CAMARA_DISPONIBLE:
        menu.insert(3, ("Escaneo QR", "escaneo", "qr"))

    menu.append(("Respaldos", "respaldos", "backups"))
    menu.append(("Cerrar Sesión", "cerrar_sesion", "logout"))

    return menu


def create_sidebar_menu(
    app,
    sidebar: ctk.CTkFrame,
    menu_items: list[tuple],
) -> dict[str, dict]:
    menu_data: dict[str, dict] = {}

    def _confirmar_cierre():
        from CTkMessagebox import CTkMessagebox
        res = CTkMessagebox(
            title="Cerrar Sesión",
            message="¿Está seguro de que desea cerrar sesión?",
            icon="question",
            option_1="Cancelar",
            option_2="Cerrar sesión",
        )
        if res.get() == "Cerrar sesión":
            app.mostrar_login()

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
        "logout": _confirmar_cierre,
    }

    for texto, icono, cmd_key in menu_items:
        es_peligro = texto == "Cerrar Sesión"

        icon = get_icon(icono, size=18, color=COLORES["texto_2"])
        accion = action_map.get(cmd_key, lambda: None)

        btn = ctk.CTkButton(
            sidebar,
            text=f"  {texto}",
            image=icon,
            compound="left",
            fg_color="transparent",
            hover_color=COLORES["sidebar_hover"],
            anchor="w",
            height=38,
            corner_radius=8,
            font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_2"],
            command=lambda t=texto, a=accion, p=es_peligro: _confirmar_cierre() if p else app._cambiar_pagina(t, a),
        )
        btn.pack(fill="x", padx=(10, 6), pady=3)

        if es_peligro:
            btn.configure(
                fg_color="transparent",
                hover_color=COLORES["rojo_hover"],
                text_color=COLORES["rojo"],
            )

        menu_data[texto] = {
            "btn": btn,
            "es_peligro": es_peligro,
            "icono_nombre": icono,
        }

    return menu_data


def update_active(menu_data: dict[str, dict], active_text: str | None = None) -> None:
    for texto, data in menu_data.items():
        btn = data["btn"]
        icono_nombre = data.get("icono_nombre", "")
        es_peligro = data.get("es_peligro", False)
        es_activo = texto == active_text

        if es_peligro:
            btn.configure(
                fg_color="transparent",
                text_color=COLORES["rojo"],
            )
        elif es_activo:
            icon_act = get_icon(icono_nombre, size=18, color=COLORES["acento"])
            btn.configure(
                fg_color=COLORES["sidebar_hover"],
                text_color=COLORES["acento"],
                image=icon_act,
            )
        else:
            icon_inact = get_icon(icono_nombre, size=18, color=COLORES["texto_2"])
            btn.configure(
                fg_color="transparent",
                text_color=COLORES["texto_2"],
                image=icon_inact,
            )
