"""
Gestor de sesión: acumula resúmenes breves de cada ciclo y compacta el contexto
cuando crece demasiado, para no saturar la ventana de contexto del modelo.
"""
import datetime
from pathlib import Path
from model_adapters import ModeloVision

PROMPT_ANALISIS = (
    "Observa esta captura de pantalla. Describe en 1-2 frases, de forma breve y neutral, "
    "qué contenido o actividad relevante hay (documento, video, código, navegación web, etc.) "
    "y qué cambió respecto al contexto previo si aplica. Si hay una pregunta de opción múltiple, "
    "transcribe la pregunta y las opciones visibles, e indica la respuesta solo si puede inferirse "
    "con seguridad. No inventes detalles que no veas."
)

PROMPT_COMPACTACION = (
    "Condensa el siguiente historial de observaciones en un resumen de máximo 3 frases, "
    "preservando únicamente la información más relevante y descartando detalles repetidos "
    "o ya superados:"
)


class GestorSesion:
    def __init__(self, modelo: ModeloVision, max_resumen_chars=800,
                 guardar_log=True, log_path: Path = None):
        self.modelo = modelo
        self.max_resumen_chars = max_resumen_chars
        self.resumen_actual = ""
        self.guardar_log = guardar_log
        self.log_path = log_path

    def procesar_ciclo(self, imagen_bytes: bytes) -> str:
        nuevo_analisis = self.modelo.analizar_imagen(
            imagen_bytes, PROMPT_ANALISIS, contexto=self.resumen_actual
        )
        self._registrar_log(nuevo_analisis)
        self._acumular_y_compactar(nuevo_analisis)
        return nuevo_analisis

    def _acumular_y_compactar(self, nuevo_analisis: str):
        combinado = f"{self.resumen_actual}\n- {nuevo_analisis}".strip()
        if len(combinado) > self.max_resumen_chars:
            try:
                self.resumen_actual = self.modelo.compactar_texto(combinado, PROMPT_COMPACTACION)
            except Exception:
                # Si falla la compactación por IA, hace fallback a truncado simple
                self.resumen_actual = combinado[-self.max_resumen_chars:]
        else:
            self.resumen_actual = combinado

    def _registrar_log(self, texto: str):
        if not self.guardar_log or not self.log_path:
            return
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            marca = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{marca}] {texto}\n")
        except Exception:
            pass  # el log nunca debe tumbar el agente
