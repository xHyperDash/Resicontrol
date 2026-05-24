from typing import Any
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk

from config import COLORES


_RESAMPLE = 1


_ICON_CACHE: dict[str, ctk.CTkImage] = {}

_FONT_PATH = r"C:\Windows\Fonts\seguisym.ttf"
_FONT_SIZE = 28

_GLYPH_MAP = {
    "inicio":       0x2302,
    "visitantes":   0x1F464,
    "residentes":   0x1F3E2,
    "parqueaderos": 0x1F697,
    "historial":    0x23F0,
    "incidentes":   0x26A0,
    "reportes":     0x1F4C4,
    "usuarios":     0x2699,
    "respaldos":    0x1F4BE,
    "cerrar_sesion": 0x1F6AA,
    "qr":           0x26A1,
    "escaneo":      0x1F4F7,
    "buscar":       0x1F50D,
}


def _render_glyph(char_code: int, size: int, color: str) -> Image.Image:
    try:
        font: Any = ImageFont.truetype(_FONT_PATH, _FONT_SIZE)  # noqa: ANN401
    except (OSError, IOError):
        font = ImageFont.load_default()

    img = Image.new("RGBA", (_FONT_SIZE * 2, _FONT_SIZE * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), chr(char_code), font=font, fill=color)

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    iw, ih = img.size
    if iw > 0 and ih > 0:
        scale = min(size / iw, size / ih) * 0.85
        nw, nh = int(iw * scale), int(ih * scale)
        if nw > 0 and nh > 0:
            resized = img.resize((nw, nh), _RESAMPLE)
            ox = (size - nw) // 2
            oy = (size - nh) // 2
            final.paste(resized, (ox, oy), resized)

    return final


def get_icon(name: str, size: int = 20, color: str | None = None) -> ctk.CTkImage:
    cache_key = f"{name}_{size}"
    cached = _ICON_CACHE.get(cache_key)
    if cached is not None:
        return cached

    code = _GLYPH_MAP.get(name)
    if code is None:
        raise ValueError(f"Unknown icon: {name}")

    color = color or COLORES["texto_2"]
    img = _render_glyph(code, size, color)
    icon = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    _ICON_CACHE[cache_key] = icon
    return icon


def get_icon_data() -> list[tuple[str, str]]:
    return sorted((k, k.replace("_", " ").title()) for k in _GLYPH_MAP)
