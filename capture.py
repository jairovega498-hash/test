"""
Captura de pantalla optimizada: resize + compresión JPEG,
y detección de cambio de frame para evitar analizar pantallas repetidas.
"""
import io
import mss
from PIL import Image, ImageChops
import numpy as np


class Capturador:
    def __init__(self, max_ancho=1280, calidad_jpeg=70):
        self.max_ancho = max_ancho
        self.calidad_jpeg = calidad_jpeg
        self._ultimo_frame_gris = None

    def _tomar_raw(self) -> Image.Image:
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # escritorio virtual: todas las pantallas
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
        if self.max_ancho and img.width > self.max_ancho:
            ratio = self.max_ancho / img.width
            img = img.resize((self.max_ancho, int(img.height * ratio)))
        return img

    def capturar_bytes(self) -> bytes:
        """Devuelve la captura actual como JPEG en bytes, lista para enviar al modelo."""
        img = self._tomar_raw()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self.calidad_jpeg)
        return buf.getvalue()

    def cambio_significativo(self, umbral=0.02) -> bool:
        """
        Compara la pantalla actual con la anterior (en escala de grises, downscale)
        para decidir si vale la pena reanalizar. Devuelve True si cambió lo suficiente.
        """
        img = self._tomar_raw().convert("L").resize((160, 90))
        actual = np.asarray(img, dtype=np.int16)

        if self._ultimo_frame_gris is None:
            self._ultimo_frame_gris = actual
            return True

        diff = np.abs(actual - self._ultimo_frame_gris)
        proporcion_cambio = np.mean(diff > 15)  # píxeles que cambiaron notablemente
        self._ultimo_frame_gris = actual
        return proporcion_cambio > umbral
