"""
Gestor de sesión: acumula resúmenes breves de cada ciclo y compacta el contexto
cuando crece demasiado, para no saturar la ventana de contexto del modelo.
"""
import datetime
from pathlib import Path
from model_adapters import ModeloVision

PROMPT_ANALISIS = (
    "Analiza cuidadosamente la captura completa, pero céntrate exclusivamente en las preguntas "
    "visibles y sus opciones de respuesta. Ignora barras de tareas, menús, ventanas ajenas, "
    "notificaciones y cualquier contenido que no pertenezca a la pregunta. Busca una o varias "
    "preguntas, incluidas preguntas de opción múltiple, y usa el texto y las imágenes asociadas "
    "para resolverlas. "
    "Devuelve exclusivamente este formato, sin introducción ni explicaciones adicionales:\n\n"
    "EJEMPLO SALIDA(usalo como guía)--> Pregunta #1\n"
    "EJEMPLO SALIDA(usalo como guía)--> Respuesta: A\n\n"
    "EJEMPLO SALIDA(usalo como guía)--> Pregunta #2\n"
    "EJEMPLO SALIDA(usalo como guía)--> Respuesta: A y C\n\n"
    "Incluye tantas preguntas como existan. Usa la letra o letras de la opción correcta, por ejemplo "
    "A, B, A y C, según corresponda. Si no puedes determinar una respuesta con seguridad, escribe "
    "EJEMPLO SALIDA(usalo como guía)--> Respuesta: No determinada. No inventes preguntas, opciones ni respuestas."
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

    async def procesar_ciclo_async(self, imagen_bytes: bytes) -> str:
        nuevo_analisis = await self.modelo.analizar_imagen_async(
            imagen_bytes, PROMPT_ANALISIS, contexto=self.resumen_actual
        )
        self._registrar_log(nuevo_analisis)
        await self._acumular_y_compactar_async(nuevo_analisis)
        return nuevo_analisis

    async def _acumular_y_compactar_async(self, nuevo_analisis: str):
        combinado = f"{self.resumen_actual}\n- {nuevo_analisis}".strip()
        if len(combinado) > self.max_resumen_chars:
            try:
                self.resumen_actual = await self.modelo.compactar_texto_async(
                    combinado, PROMPT_COMPACTACION
                )
            except Exception:
                self.resumen_actual = combinado[-self.max_resumen_chars:]
        else:
            self.resumen_actual = combinado

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
