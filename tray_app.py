"""Widget flotante para capturar y analizar la pantalla con Alt+Z."""
import ctypes
import asyncio
import logging
import threading
import tkinter as tk
from ctypes import wintypes
from io import BytesIO
from tkinter import messagebox

from PIL import Image, ImageTk

from capture import Capturador
from config import CONFIG_DIR, cargar_config, guardar_config
from capture_protection import set_capture_protection
from model_adapters import crear_adaptador
from session_manager import GestorSesion


WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_MONITOR = 0x00000001
MOD_ALT = 0x0001
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
VK_Z = 0x5A
VK_S = 0x53
VK_SNAPSHOT = 0x2C
HOTKEY_ID = 1
HOTKEY_CAPTURE_PRINTSCREEN = 2
HOTKEY_CAPTURE_SNIPPING = 3

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=CONFIG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


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
            max_preguntas_contexto=self.config["max_preguntas_contexto"],
            guardar_log=self.config["guardar_log"],
            log_path=CONFIG_DIR / "historial.log",
        )
        self.root = tk.Tk()
        self.root.title("Resumidor de pantalla")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#ffffff")
        self.root.protocol("WM_DELETE_WINDOW", self._salir)
        self.imagen_bytes = None
        self.imagen_tk = None
        self.hotkey_thread_id = None
        self.hotkey_activo = True
        self.arrastre_x = 0
        self.arrastre_y = 0
        self.analisis_id = 0
        self.analisis_loop = None
        self.analisis_task = None
        self.restaurar_id = None
        self.captura_oculta = False
        self._construir_widget()
        self._posicionar_widget()
        self._aplicar_proteccion(self.root)
        self.root.after_idle(lambda: self._aplicar_proteccion(self.root))
        self.root.after(500, self._forzar_siempre_encima)

    def _aplicar_proteccion(self, ventana):
        ventana.update_idletasks()
        if self.config.get("proteccion_capturas", True):
            set_capture_protection(ventana.winfo_id(), True)
        else:
            set_capture_protection(ventana.winfo_id(), False)

    def _forzar_siempre_encima(self):
        if not self.hotkey_activo or self.captura_oculta or not self.root.winfo_exists():
            return
        self.root.attributes("-topmost", True)
        ctypes.windll.user32.SetWindowPos(
            self.root.winfo_id(),
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
        self.root.after(500, self._forzar_siempre_encima)

    def _construir_widget(self):
        contenedor = tk.Frame(
            self.root,
            bg="#ffffff",
            padx=10,
            pady=5,
            highlightbackground="#b8b8b8",
            highlightcolor="#b8b8b8",
            highlightthickness=1,
        )
        contenedor.pack(fill="both", expand=True)

        controles = tk.Frame(contenedor, bg="#ffffff")
        controles.pack(fill="x")

        self.etiqueta_estado = tk.Label(
            controles,
            text="Alt+Z o cámara",
            bg="#ffffff",
            fg="#111111",
            font=("Segoe UI", 9),
        )
        self.etiqueta_estado.pack(side="left", padx=(0, 7))

        self.boton_capturar = tk.Button(
            controles,
            text="📷",
            command=self._capturar,
            bg="#eeeeee",
            fg="#111111",
            activebackground="#dddddd",
            activeforeground="#111111",
            relief="solid",
            bd=1,
            padx=7,
            pady=1,
            font=("Segoe UI Emoji", 11),
        )
        self.boton_capturar.pack(side="left", padx=(0, 6))
        self._agregar_hover(self.boton_capturar, "#eeeeee", "#d8d8d8")

        self.boton_imagen = tk.Button(
            controles,
            text="imagen capturada",
            command=self._mostrar_captura,
            state="disabled",
            bg="#f0f0f0",
            fg="#111111",
            activebackground="#dedede",
            activeforeground="#111111",
            relief="flat",
            padx=7,
            pady=1,
            font=("Segoe UI", 9),
        )
        self.boton_imagen.pack(side="left", padx=(0, 6))
        self._agregar_hover(self.boton_imagen, "#f0f0f0", "#dedede")

        self.boton_analizar = tk.Button(
            controles,
            text="ANALIZAR",
            command=self._analizar,
            state="disabled",
            bg="#8fd3a8",
            fg="#111111",
            activebackground="#75bf91",
            activeforeground="#111111",
            relief="flat",
            padx=10,
            pady=1,
            font=("Segoe UI", 9, "bold"),
        )
        self.boton_analizar.pack(side="left")
        self._agregar_hover(self.boton_analizar, "#8fd3a8", "#75bf91")

        self.boton_cancelar = tk.Button(
            controles,
            text="CANCELAR",
            command=self._cancelar_analisis,
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            activebackground="#eeeeee",
            activeforeground="#111111",
            relief="solid",
            bd=1,
            padx=8,
            pady=1,
            font=("Segoe UI", 9),
        )
        self.boton_cancelar.pack(side="left", padx=(6, 0))
        self.boton_cancelar.pack_forget()
        self._agregar_hover(self.boton_cancelar, "#ffffff", "#eeeeee")

        panel_respuesta = tk.Frame(contenedor, bg="#ffffff")
        panel_respuesta.pack(fill="both", expand=True, pady=(3, 0))

        self.etiqueta_respuesta = tk.Text(
            panel_respuesta,
            height=3,
            width=48,
            wrap="word",
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            insertbackground="#111111",
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 10),
            padx=6,
            pady=3,
        )
        self.etiqueta_respuesta.pack(side="left", fill="both", expand=True)

        barra_respuesta = tk.Scrollbar(
            panel_respuesta,
            orient="vertical",
            command=self.etiqueta_respuesta.yview,
        )
        barra_respuesta.pack(side="right", fill="y")
        self.etiqueta_respuesta.configure(yscrollcommand=barra_respuesta.set)

        pie = tk.Frame(contenedor, bg="#ffffff")
        pie.pack(fill="x", pady=(4, 0))

        self.boton_config = tk.Button(
            pie,
            text="CONFIG",
            command=self._abrir_configuracion,
            bg="#eeeeee",
            fg="#111111",
            activebackground="#dddddd",
            activeforeground="#111111",
            relief="solid",
            bd=1,
            padx=9,
            pady=2,
            font=("Segoe UI", 9),
        )
        self.boton_config.pack(side="left")
        self._agregar_hover(self.boton_config, "#eeeeee", "#dddddd")

        self.boton_salir = tk.Button(
            pie,
            text="SALIR",
            command=self._confirmar_salida,
            bg="#f3b4b4",
            fg="#111111",
            activebackground="#e79d9d",
            activeforeground="#111111",
            relief="solid",
            bd=1,
            padx=9,
            pady=2,
            font=("Segoe UI", 9),
        )
        self.boton_salir.pack(side="right")
        self._agregar_hover(self.boton_salir, "#f3b4b4", "#e79d9d")

        for widget in (contenedor, controles, self.etiqueta_estado, panel_respuesta, pie):
            widget.bind("<Button-1>", self._iniciar_arrastre)
            widget.bind("<B1-Motion>", self._arrastrar)

    def _agregar_hover(self, boton, color_normal, color_hover):
        boton.bind("<Enter>", lambda _evento: boton.config(bg=color_hover))
        boton.bind("<Leave>", lambda _evento: boton.config(bg=color_normal))

    def _abrir_configuracion(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Configuración")
        ventana.configure(bg="#ffffff")
        ventana.resizable(False, False)
        ventana.transient(self.root)
        ventana.grab_set()
        self._aplicar_proteccion(ventana)

        campos = {}
        formulario = tk.Frame(ventana, bg="#ffffff", padx=16, pady=14)
        formulario.pack(fill="both", expand=True)

        def agregar_campo(nombre, etiqueta, secreto=False):
            fila = tk.Frame(formulario, bg="#ffffff")
            fila.pack(fill="x", pady=3)
            tk.Label(
                fila, text=etiqueta, width=22, anchor="w",
                bg="#ffffff", fg="#111111", font=("Segoe UI", 9),
            ).pack(side="left")
            variable = tk.StringVar(value=str(self.config.get(nombre, "")))
            entrada = tk.Entry(
                fila, textvariable=variable, width=32,
                show="*" if secreto else "", font=("Segoe UI", 9),
            )
            entrada.pack(side="left")
            campos[nombre] = variable

        proveedor_var = tk.StringVar(value=self.config.get("proveedor", "openai"))
        fila_proveedor = tk.Frame(formulario, bg="#ffffff")
        fila_proveedor.pack(fill="x", pady=3)
        tk.Label(
            fila_proveedor, text="Proveedor", width=22, anchor="w",
            bg="#ffffff", fg="#111111", font=("Segoe UI", 9),
        ).pack(side="left")
        tk.OptionMenu(fila_proveedor, proveedor_var, "openai", "gemini").pack(side="left", fill="x")

        agregar_campo("modelo", "Modelo")
        agregar_campo("api_key", "API key", secreto=True)
        agregar_campo("intervalo_segundos", "Intervalo (segundos)")
        agregar_campo("max_ancho_px", "Ancho máximo (px)")
        agregar_campo("calidad_jpeg", "Calidad JPEG")
        agregar_campo("max_resumen_chars", "Máximo resumen (chars)")
        agregar_campo("max_preguntas_contexto", "Preguntas por contexto")
        agregar_campo("umbral_cambio", "Umbral de cambio")

        guardar_log_var = tk.BooleanVar(value=bool(self.config.get("guardar_log", True)))
        solo_cambia_var = tk.BooleanVar(value=bool(self.config.get("solo_si_cambia", True)))
        proteccion_capturas_var = tk.BooleanVar(
            value=bool(self.config.get("proteccion_capturas", True))
        )
        tk.Checkbutton(
            formulario, text="Guardar historial", variable=guardar_log_var,
            bg="#ffffff", fg="#111111", activebackground="#ffffff",
        ).pack(anchor="w", pady=(5, 0))
        tk.Checkbutton(
            formulario, text="Usar solo si cambia la pantalla", variable=solo_cambia_var,
            bg="#ffffff", fg="#111111", activebackground="#ffffff",
        ).pack(anchor="w")
        tk.Checkbutton(
            formulario, text="Protección contra capturas", variable=proteccion_capturas_var,
            bg="#ffffff", fg="#111111", activebackground="#ffffff",
        ).pack(anchor="w")

        def guardar_desde_formulario():
            try:
                nueva_config = dict(self.config)
                nueva_config.update({
                    "proveedor": proveedor_var.get().strip().lower(),
                    "modelo": campos["modelo"].get().strip(),
                    "api_key": campos["api_key"].get().strip(),
                    "intervalo_segundos": int(campos["intervalo_segundos"].get()),
                    "max_ancho_px": int(campos["max_ancho_px"].get()),
                    "calidad_jpeg": int(campos["calidad_jpeg"].get()),
                    "max_resumen_chars": int(campos["max_resumen_chars"].get()),
                    "max_preguntas_contexto": int(campos["max_preguntas_contexto"].get()),
                    "umbral_cambio": float(campos["umbral_cambio"].get()),
                    "guardar_log": guardar_log_var.get(),
                    "solo_si_cambia": solo_cambia_var.get(),
                    "proteccion_capturas": proteccion_capturas_var.get(),
                })
                if not nueva_config["modelo"]:
                    raise ValueError("El modelo no puede estar vacío.")
                if nueva_config["intervalo_segundos"] <= 0 or nueva_config["max_ancho_px"] <= 0:
                    raise ValueError("El intervalo y el ancho deben ser mayores que cero.")
                if not 1 <= nueva_config["calidad_jpeg"] <= 95:
                    raise ValueError("La calidad JPEG debe estar entre 1 y 95.")
                if nueva_config["max_resumen_chars"] <= 0:
                    raise ValueError("El máximo del resumen debe ser mayor que cero.")
                if nueva_config["max_preguntas_contexto"] <= 0:
                    raise ValueError("Las preguntas por contexto deben ser mayores que cero.")
                if not 0 <= nueva_config["umbral_cambio"] <= 1:
                    raise ValueError("El umbral debe estar entre 0 y 1.")
                guardar_config(nueva_config)
                self.config = cargar_config()
                self.capturador.max_ancho = self.config["max_ancho_px"]
                self.capturador.calidad_jpeg = self.config["calidad_jpeg"]
                self.sesion.max_resumen_chars = self.config["max_resumen_chars"]
                self.sesion.max_preguntas_contexto = self.config["max_preguntas_contexto"]
                self._aplicar_proteccion(self.root)
                self.modelo = crear_adaptador(self.config)
                self.sesion.modelo = self.modelo
                ventana.destroy()
                self.etiqueta_estado.config(text="Configuración guardada")
            except Exception as error:
                messagebox.showerror("Configuración", str(error), parent=ventana)

        botones = tk.Frame(formulario, bg="#ffffff")
        botones.pack(fill="x", pady=(12, 0))
        boton_guardar = tk.Button(
            botones, text="GUARDAR", command=guardar_desde_formulario,
            bg="#8fd3a8", fg="#111111", relief="solid", bd=1,
            padx=10, pady=2, font=("Segoe UI", 9, "bold"),
        )
        boton_guardar.pack(side="right")
        self._agregar_hover(boton_guardar, "#8fd3a8", "#75bf91")
        boton_cancelar_config = tk.Button(
            botones, text="CANCELAR", command=ventana.destroy,
            bg="#eeeeee", fg="#111111", relief="solid", bd=1,
            padx=8, pady=2, font=("Segoe UI", 9),
        )
        boton_cancelar_config.pack(side="right", padx=(0, 6))
        self._agregar_hover(boton_cancelar_config, "#eeeeee", "#dddddd")

    def _establecer_respuesta(self, texto, color="#111111"):
        self.etiqueta_respuesta.config(state="normal", fg=color)
        self.etiqueta_respuesta.delete("1.0", "end")
        self.etiqueta_respuesta.insert("1.0", texto)
        self.etiqueta_respuesta.config(state="disabled")
        self.etiqueta_respuesta.see("1.0")

    def _posicionar_widget(self):
        self.root.update_idletasks()
        ancho = 420
        alto = max(102, self.root.winfo_reqheight())
        x = (self.root.winfo_screenwidth() - ancho) // 2
        y = self.root.winfo_screenheight() - alto - 35
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _iniciar_arrastre(self, evento):
        self.arrastre_x = evento.x_root - self.root.winfo_x()
        self.arrastre_y = evento.y_root - self.root.winfo_y()

    def _arrastrar(self, evento):
        x = evento.x_root - self.arrastre_x
        y = evento.y_root - self.arrastre_y
        self.root.geometry(f"+{x}+{y}")

    def _capturar(self):
        if self.captura_oculta:
            return
        self.captura_oculta = True
        self.boton_capturar.config(state="disabled")
        self.boton_imagen.config(state="disabled")
        self.boton_analizar.config(state="disabled")
        self.etiqueta_estado.config(text="Capturando...")
        self.root.withdraw()
        self.root.after(150, self._capturar_con_widget_oculto)

    def _capturar_con_widget_oculto(self):
        try:
            self.imagen_bytes = self.capturador.capturar_bytes()
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self._aplicar_proteccion(self.root)
            self.captura_oculta = False
            self.boton_capturar.config(state="normal")
            self.boton_imagen.config(state="normal")
            self.boton_analizar.config(state="normal")
            self.etiqueta_estado.config(text="Captura lista")
            self._establecer_respuesta("")
            self._analizar()
        except Exception as error:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self._aplicar_proteccion(self.root)
            self.captura_oculta = False
            self.boton_capturar.config(state="normal")
            self.etiqueta_estado.config(text="Error al capturar")
            self._establecer_respuesta(str(error), "#b00020")

    def _mostrar_captura(self):
        if not self.imagen_bytes:
            return
        imagen = Image.open(BytesIO(self.imagen_bytes))
        imagen.thumbnail((180, 110))
        self.imagen_tk = ImageTk.PhotoImage(imagen)
        self.boton_imagen.config(image=self.imagen_tk, compound="top")

    def _analizar(self):
        if not self.imagen_bytes:
            return
        self.analisis_id += 1
        analisis_id = self.analisis_id
        self.boton_analizar.config(state="disabled", text="ANALIZANDO...")
        self.boton_cancelar.config(state="normal")
        self.boton_cancelar.pack(side="left", padx=(6, 0))
        self.etiqueta_estado.config(text="Analizando...")
        threading.Thread(
            target=self._analizar_en_segundo_plano,
            args=(self.imagen_bytes, analisis_id),
            daemon=True,
        ).start()

    def _analizar_en_segundo_plano(self, imagen_bytes, analisis_id):
        loop = asyncio.new_event_loop()
        self.analisis_loop = loop
        asyncio.set_event_loop(loop)
        tarea = loop.create_task(self._procesar_analisis(imagen_bytes))
        self.analisis_task = tarea
        try:
            respuesta = loop.run_until_complete(tarea)
            self.root.after(0, self._mostrar_respuesta, respuesta, analisis_id)
        except asyncio.CancelledError:
            pass
        except Exception as error:
            self.root.after(0, self._mostrar_error, error, analisis_id)
        finally:
            loop.run_until_complete(self.modelo.cerrar_async())
            loop.close()
            self.analisis_task = None
            self.analisis_loop = None

    async def _procesar_analisis(self, imagen_bytes):
        return await self.sesion.procesar_ciclo_async(imagen_bytes)

    def _cancelar_analisis(self):
        self.analisis_id += 1
        if self.analisis_loop and self.analisis_task:
            self.analisis_loop.call_soon_threadsafe(self.analisis_task.cancel)
        self.boton_analizar.config(state="normal", text="ANALIZAR")
        self.boton_cancelar.config(state="disabled")
        self.boton_cancelar.pack_forget()
        self.etiqueta_estado.config(text="Análisis cancelado")

    def _mostrar_respuesta(self, respuesta, analisis_id):
        if analisis_id != self.analisis_id:
            return
        self.etiqueta_estado.config(text="Análisis terminado")
        self._establecer_respuesta(respuesta)
        self.boton_analizar.config(state="normal", text="ANALIZAR")
        self.boton_cancelar.config(state="disabled")
        self.boton_cancelar.pack_forget()

    def _mostrar_error(self, error, analisis_id):
        if analisis_id != self.analisis_id:
            return
        self.etiqueta_estado.config(text="Error de análisis")
        self._establecer_respuesta(str(error), "#b00020")
        self.boton_analizar.config(state="normal", text="ANALIZAR")
        self.boton_cancelar.config(state="disabled")
        self.boton_cancelar.pack_forget()

    def _escuchar_hotkey(self):
        self.hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_Z):
            self.root.after(0, lambda: messagebox.showerror(
                "Resumidor de pantalla",
                "No se pudo registrar Alt+Z. Puede estar siendo usado por otra aplicación.",
            ))
            return
        user32.RegisterHotKey(
            None, HOTKEY_CAPTURE_PRINTSCREEN, MOD_NOREPEAT, VK_SNAPSHOT
        )
        user32.RegisterHotKey(
            None,
            HOTKEY_CAPTURE_SNIPPING,
            MOD_WIN | MOD_SHIFT | MOD_NOREPEAT,
            VK_S,
        )
        mensaje = wintypes.MSG()
        while self.hotkey_activo and user32.GetMessageW(ctypes.byref(mensaje), None, 0, 0) > 0:
            if mensaje.message == WM_HOTKEY and mensaje.wParam == HOTKEY_ID:
                self.root.after(0, self._capturar)
            elif mensaje.message == WM_HOTKEY and mensaje.wParam in {
                HOTKEY_CAPTURE_PRINTSCREEN,
                HOTKEY_CAPTURE_SNIPPING,
            }:
                self.root.after(0, self._ocultar_para_captura)
        user32.UnregisterHotKey(None, HOTKEY_CAPTURE_PRINTSCREEN)
        user32.UnregisterHotKey(None, HOTKEY_CAPTURE_SNIPPING)
        user32.UnregisterHotKey(None, HOTKEY_ID)

    def _ocultar_para_captura(self):
        if not self.root.winfo_viewable():
            return
        self.root.withdraw()
        if self.restaurar_id:
            self.root.after_cancel(self.restaurar_id)
        self.restaurar_id = self.root.after(2500, self._restaurar_despues_de_captura)

    def _restaurar_despues_de_captura(self):
        self.restaurar_id = None
        if self.hotkey_activo:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self._aplicar_proteccion(self.root)

    def iniciar(self):
        threading.Thread(target=self._escuchar_hotkey, daemon=True).start()
        self.root.mainloop()

    def _confirmar_salida(self):
        if messagebox.askyesno("Salir", "¿Está seguro?", parent=self.root):
            self._salir()

    def _salir(self):
        self.hotkey_activo = False
        if self.restaurar_id:
            self.root.after_cancel(self.restaurar_id)
        if self.analisis_loop and self.analisis_task:
            self.analisis_loop.call_soon_threadsafe(self.analisis_task.cancel)
        if self.hotkey_thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.hotkey_thread_id, WM_QUIT, 0, 0)
        self.root.destroy()


if __name__ == "__main__":
    try:
        AgenteResumidor().iniciar()
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(None, str(error), "Resumidor de pantalla", 0x10)
