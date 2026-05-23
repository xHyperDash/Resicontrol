import customtkinter as ctk
from config import COLORES, FONT


_TOAST_COLORS = {
    "ok": COLORES["verde"],
    "error": COLORES["rojo"],
    "aviso": COLORES["amarillo"],
    "info": COLORES["azul"],
}

_TOAST_ICONS = {
    "ok": "✓",
    "error": "✗",
    "aviso": "⚠",
    "info": "ℹ",
}


class ToastManager:
    """Manages non-blocking toast notifications stacked at top-right."""

    def __init__(self, parent: ctk.CTkBaseClass):
        self.parent = parent
        self._toasts: list[ctk.CTkFrame] = []
        self._offset = 12

    def show(
        self,
        tipo: str = "info",
        titulo: str = "",
        mensaje: str = "",
        duracion: int = 3500,
    ) -> None:
        color = _TOAST_COLORS.get(tipo, COLORES["azul"])
        icono = _TOAST_ICONS.get(tipo, "ℹ")

        toast = ctk.CTkFrame(
            self.parent,
            fg_color=COLORES["panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORES["borde"],
        )

        accent = ctk.CTkFrame(toast, width=4, corner_radius=0, fg_color=color)
        accent.pack(side="left", fill="y")
        accent.pack_propagate(False)

        body = ctk.CTkFrame(toast, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=f"{icono}  {titulo}",
            font=FONT["subtitulo"],
            text_color=color,
        ).pack(side="left")

        close_btn = ctk.CTkButton(
            header,
            text="✕",
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLORES["borde"],
            font=FONT["cuerpo_pequeno"],
            text_color=COLORES["texto_3"],
            command=lambda t=toast: self._dismiss(t),
        )
        close_btn.pack(side="right")

        if mensaje:
            ctk.CTkLabel(
                body,
                text=mensaje,
                font=FONT["cuerpo_pequeno"],
                text_color=COLORES["texto_2"],
                wraplength=280,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

        toast.bind("<Button-1>", lambda e, t=toast: self._dismiss(t))

        toast.update_idletasks()
        w = 340
        h = toast.winfo_reqheight()

        toast.place(
            x=self.parent.winfo_width() - w - self._offset,
            y=self._offset + sum(
                t.winfo_height() + 8 for t in self._toasts if t.winfo_exists()
            ),
        )
        toast.configure(width=w)

        self._toasts.append(toast)

        self.parent.after(duracion, lambda t=toast: self._dismiss(t))

    def _dismiss(self, toast: ctk.CTkFrame) -> None:
        if not toast.winfo_exists():
            return
        toast.destroy()
        self._reposition()

    def _reposition(self) -> None:
        self._toasts = [t for t in self._toasts if t.winfo_exists()]
        y = self._offset
        for toast in self._toasts:
            toast.place_configure(y=y)
            y += toast.winfo_height() + 8

    def clear(self) -> None:
        for toast in self._toasts:
            if toast.winfo_exists():
                toast.destroy()
        self._toasts.clear()
