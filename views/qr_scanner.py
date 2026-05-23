import customtkinter as ctk
import sqlite3

from views.base import BaseView
from config import COLORES, FONT, DB_PATH
from config import PAD_CARD_X, PAD_CARD_Y, BOTON_SECUNDARIO_ANCHO
from qr_manager import escanear_qr

CAMARA_DISPONIBLE = False
try:
    import cv2
    import pyzbar.pyzbar as pyzbar
    CAMARA_DISPONIBLE = True
except ImportError:
    pass


class QRScannerView(BaseView):
    """View for QR code scanning."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.contenido = app.contenido
        self.pack(fill="both", expand=True)
        self.video_label: ctk.CTkLabel | None = None
        self._crear_vista()

    def _crear_vista(self):
        if not CAMARA_DISPONIBLE:
            self.label_seccion(self, "Escaneo QR")
            card = self.tarjeta(self)
            card.pack(fill="both", padx=PAD_CARD_X, pady=PAD_CARD_Y, expand=True)
            ctk.CTkLabel(
                card,
                text="Camera libraries not installed (cv2, pyzbar)",
                font=FONT["cuerpo"],
                text_color=COLORES["rojo"],
            ).pack(pady=40)
            return

        self.label_seccion(self, "Escaneo de Placa QR")
        card = self.tarjeta(self)
        card.pack(fill="both", padx=PAD_CARD_X, pady=PAD_CARD_Y, expand=True)

        self.video_label = ctk.CTkLabel(
            card, text="Presiona 'Iniciar' para activar la cámara",
            font=FONT["cuerpo"],
        )
        self.video_label.pack(pady=20)

        self.boton(card, "Iniciar escaneo", self._iniciar, width=BOTON_SECUNDARIO_ANCHO).pack(pady=8)
        self.boton(
            card,
            "Detener",
            self._detener,
            color=COLORES["rojo"],
            hover=COLORES["rojo_hover"],
            width=BOTON_SECUNDARIO_ANCHO,
        ).pack(pady=8)

        self.info_qr = ctk.CTkLabel(
            card, text="", font=FONT["cuerpo"], text_color=COLORES["texto_2"]
        )
        self.info_qr.pack(pady=12)

    def _iniciar(self):
        self.app.scanning = True
        self.app.cap = cv2.VideoCapture(0)

        if not self.app.cap.isOpened():
            self.notificar("error", "Error", "No se pudo abrir la cámara")
            self.app.scanning = False
            return

        self._leer_frame()

    def _leer(self):
        if not self.app.scanning or not self.app.cap:
            return

        ret, frame = self.app.cap.read()
        if not ret:
            self.after(30, self._leer_frame)
            return

        placa = escanear_qr(frame)
        if placa:
            self._detener()
            self._mostrar_info_residente(placa)
            return

        from PIL import Image

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((640, 400))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 400))
        self.video_label.configure(image=ctk_img, text="")
        self.video_label.image = ctk_img
        self.after(15, self._leer_frame)

    def _leer_frame(self):
        self._leer()

    def _detener(self):
        self.app._detener_camara()

    def _mostrar_info_residente(self, placa: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM residentes WHERE placa=? AND activo=1", (placa,)
        ).fetchone()
        conn.close()

        if row:
            info = (
                f"Unidad: {row['unidad']}\n"
                f"Nombre: {row['nombre']}\n"
                f"Teléfono: {row['telefono'] or '—'}\n"
                f"Placa: {row['placa']}"
            )
            self.notificar("info", "Residente encontrado", info)
        else:
            self.notificar(
                "aviso", "No registrado", f"Placa {placa} no encontrada en residentes activos"
            )
