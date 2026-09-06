"""Convierte el icono JPG del proyecto al formato ICO usado por Windows."""
from pathlib import Path

from PIL import Image


carpeta = Path(__file__).resolve().parent
origen = carpeta / "icon.jpg"
destino = carpeta / "icon.ico"

if not origen.exists():
    raise FileNotFoundError(f"No se encontró el icono: {origen}")

with Image.open(origen) as imagen:
    imagen.convert("RGBA").save(
        destino,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
    )

print(f"Icono preparado: {destino}")
