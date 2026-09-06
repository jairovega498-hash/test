"""
Configuración del agente Resumidor de Pantalla.
Lee config.json (creado automáticamente en el primer arranque con valores por defecto)
para que el usuario pueda cambiar de proveedor de modelo sin tocar código.
"""
import json
import os
from pathlib import Path

# Carpeta de configuración persistente en el perfil del usuario de Windows
CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "ResumidorPantalla"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "proveedor": "openai",         # "openai" | "gemini"
    "modelo": "gpt-4o-mini",       # cambia a "gemini-2.0-flash" para Gemini
    "api_key": "",                 # opcional si se usa OPENAI_API_KEY o GEMINI_API_KEY
    "intervalo_segundos": 8,        # cada cuánto captura y analiza
    "max_ancho_px": 1280,           # resize de la captura antes de enviarla
    "calidad_jpeg": 70,
    "max_resumen_chars": 800,       # tope del contexto acumulado antes de compactar
    "guardar_log": True,            # guarda historial de resúmenes en disco
    "solo_si_cambia": True,         # evita reanalizar si la pantalla no cambió
    "umbral_cambio": 0.02           # % mínimo de diferencia entre frames para reanalizar
}


def cargar_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        guardar_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Rellena claves faltantes con valores por defecto (por si se actualiza el agente)
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        if merged.get("proveedor", "").lower() not in {"openai", "gemini"}:
            merged["proveedor"] = DEFAULT_CONFIG["proveedor"]
            merged["modelo"] = DEFAULT_CONFIG["modelo"]
        return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def guardar_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
