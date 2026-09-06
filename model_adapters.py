"""
Capa de abstracción de modelos de IA (patrón Adapter/Strategy).
El resto del agente solo conoce la interfaz ModeloVision; cambiar de proveedor
es cuestión de configuración (config.json), no de código.
"""
from abc import ABC, abstractmethod
import base64
import os
import sys
from pathlib import Path


KEYS_PATH = (
    Path(sys.executable).resolve().parent / "keys.txt"
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent / "keys.txt"
)


class ModeloVision(ABC):
    @abstractmethod
    def analizar_imagen(self, imagen_bytes: bytes, prompt: str, contexto: str = "") -> str:
        """Analiza una imagen junto con un prompt y contexto previo. Devuelve texto."""
        ...

    @abstractmethod
    def compactar_texto(self, texto: str, prompt: str) -> str:
        """Condensa texto puro (sin imagen) — usado para compactar el resumen acumulado."""
        ...


class AdaptadorOpenAI(ModeloVision):
    def __init__(self, api_key, modelo="gpt-4o-mini", **_):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.modelo = modelo

    def analizar_imagen(self, imagen_bytes, prompt, contexto=""):
        b64 = base64.b64encode(imagen_bytes).decode()
        resp = self.client.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": "Eres un asistente que resume contenido visual de forma breve y neutral."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"{contexto}\n\n{prompt}" if contexto else prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ]},
            ],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()

    def compactar_texto(self, texto, prompt):
        resp = self.client.chat.completions.create(
            model=self.modelo,
            messages=[{"role": "user", "content": f"{prompt}\n\n{texto}"}],
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()


class AdaptadorGemini(ModeloVision):
    def __init__(self, api_key, modelo="gemini-2.0-flash", **_):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.modelo = modelo

    def analizar_imagen(self, imagen_bytes, prompt, contexto=""):
        from google.genai import types
        contenido = f"{contexto}\n\n{prompt}" if contexto else prompt
        resp = self.client.models.generate_content(
            model=self.modelo,
            contents=[contenido, types.Part.from_bytes(data=imagen_bytes, mime_type="image/jpeg")],
        )
        return (resp.text or "").strip()

    def compactar_texto(self, texto, prompt):
        resp = self.client.models.generate_content(
            model=self.modelo,
            contents=f"{prompt}\n\n{texto}",
        )
        return (resp.text or "").strip()


def _cargar_keys() -> dict:
    if not KEYS_PATH.exists():
        return {}
    keys = {}
    with KEYS_PATH.open("r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            nombre, valor = linea.split("=", 1)
            keys[nombre.strip()] = valor.strip().strip('"').strip("'")
    return keys


def _obtener_api_key(config: dict, proveedor: str) -> str:
    variable = "OPENAI_API_KEY" if proveedor == "openai" else "GEMINI_API_KEY"
    api_key = _cargar_keys().get(variable, "").strip()
    if not api_key:
        api_key = str(config.get("api_key", "")).strip()
    if not api_key:
        api_key = os.environ.get(variable, "").strip()
    if not api_key:
        raise ValueError(
            f"Falta la clave de {proveedor}. Añádela a {KEYS_PATH.name} junto al programa."
        )
    return api_key


def crear_adaptador(config: dict) -> ModeloVision:
    """Fábrica: instancia el adaptador correcto según config['proveedor']."""
    proveedor = str(config.get("proveedor", "openai")).strip().lower()
    mapa = {
        "openai": AdaptadorOpenAI,
        "gemini": AdaptadorGemini,
    }
    if proveedor not in mapa:
        raise ValueError(f"Proveedor desconocido: {proveedor}. Opciones: {list(mapa.keys())}")
    return mapa[proveedor](
        api_key=_obtener_api_key(config, proveedor),
        modelo=config.get("modelo"),
    )
