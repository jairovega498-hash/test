"""
Punto de entrada del agente. Corre en la bandeja del sistema de Windows,
captura pantalla periódicamente, la analiza con el modelo configurado
y muestra un resumen breve accesible desde el ícono de la bandeja.

Uso:
    python tray_app.py
o, empaquetado:
    ResumidorPantalla.exe
"""
import threading
import time
import webbrowser
import ctypes
import pystray
from PIL import Image, ImageDraw

from config import cargar_config, CONFIG_DIR
from capture import Capturador
from model_adapters import crear_adaptador
from session_manager import GestorSesion


class AgenteResumidor:
    def __init__(self):
        self.config = cargar_config()
        self.capturador = Capturador(
            max_ancho=self.config["max_ancho_px"],
            calidad_jpeg=self.config["calidad_jpeg"],
        )
        self.modelo = crear_adaptador(self.config)
        self.sesion = GestorSesion(
            modelo=self.modelo,
            max_resumen_chars=self.config["max_resumen_chars"],
            guardar_log=self.config["guardar_log"],
            log_path=CONFIG_DIR / "historial.log",
        )
        self.activo = True
        self.pausado = False
        self.ultimo_resumen = "Iniciando..."
        self.icon = None

    # ---------- Ícono dinámico ----------
    def _icono(self, color=(0, 200, 120)):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((8, 8, 56, 56), fill=color)
        return img

    # ---------- Loop principal en hilo secundario ----------
    def _loop(self):
        while self.activo:
            if self.pausado:
                time.sleep(1)
                continue
            try:
                debe_analizar = True
                if self.config.get("solo_si_cambia", True):
                    debe_analizar = self.capturador.cambio_significativo(
                        umbral=self.config.get("umbral_cambio", 0.02)
                    )
                if debe_analizar:
                    img_bytes = self.capturador.capturar_bytes()
                    resumen = self.sesion.procesar_ciclo(img_bytes)
                    self.ultimo_resumen = resumen
                    if self.icon:
                        self.icon.icon = self._icono((0, 200, 120))
                        self.icon.title = f"Resumidor: {resumen[:120]}"
                else:
                    if self.icon:
                        self.icon.icon = self._icono((100, 100, 100))
            except Exception as e:
                self.ultimo_resumen = f"Error: {e}"
                if self.icon:
                    self.icon.icon = self._icono((200, 40, 40))
                    self.icon.title = f"Resumidor - Error: {e}"[:127]
            time.sleep(self.config["intervalo_segundos"])

    # ---------- Acciones del menú de bandeja ----------
    def _toggle_pausa(self, icon, item):
        self.pausado = not self.pausado
        icon.icon = self._icono((200, 160, 0) if self.pausado else (0, 200, 120))

    def _abrir_log(self, icon, item):
        log_path = CONFIG_DIR / "historial.log"
        if log_path.exists():
            webbrowser.open(str(log_path))

    def _abrir_config(self, icon, item):
        from config import CONFIG_PATH
        webbrowser.open(str(CONFIG_PATH))

    def _salir(self, icon, item):
        self.activo = False
        icon.stop()

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: "Reanudar" if self.pausado else "Pausar",
                self._toggle_pausa,
            ),
            pystray.MenuItem("Ver historial", self._abrir_log),
            pystray.MenuItem("Editar configuración", self._abrir_config),
            pystray.MenuItem("Salir", self._salir),
        )

    def iniciar(self):
        hilo = threading.Thread(target=self._loop, daemon=True)
        hilo.start()
        self.icon = pystray.Icon(
            "resumidor_pantalla",
            self._icono(),
            "Resumidor de Pantalla - iniciando...",
            menu=self._menu(),
        )
        self.icon.run()


if __name__ == "__main__":
    try:
        AgenteResumidor().iniciar()
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(
            None,
            str(error),
            "Resumidor de Pantalla",
            0x10,
        )
