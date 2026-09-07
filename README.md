# Resumidor de Pantalla — Widget flotante para Windows

Agente para Windows que captura el escritorio bajo demanda y analiza preguntas
visibles en pantalla usando un modelo de visión. Presenta el resultado en un
widget sin marco, siempre visible por encima de las demás ventanas y sin ícono
en la bandeja del sistema.
Analiza el escritorio virtual completo, incluyendo todas las pantallas conectadas.
Es compatible con OpenAI y Gemini.

## Requisitos

- Python 3.13 (o el disponible en tu equipo — el código no usa nada exclusivo de 3.13).
- Windows 10/11.
- Un proveedor de modelo de visión configurado (ver abajo).

## Instalación rápida (modo desarrollo)

```bat
pip install -r requirements.txt
python tray_app.py
```

Al primer arranque se crea `%APPDATA%\ResumidorPantalla\config.json` con valores
por defecto para OpenAI. Edítalo para elegir el proveedor:

```json
{
  "proveedor": "openai",
  "modelo": "gpt-4o-mini",
  "api_key": "",
  "intervalo_segundos": 8,
  "max_ancho_px": 896,
  "calidad_jpeg": 45,
  "max_resumen_chars": 800,
  "max_preguntas_contexto": 3,
  "guardar_log": true,
  "solo_si_cambia": true,
  "umbral_cambio": 0.02
}
```

### Cambiar de proveedor

| proveedor | modelo (ejemplo) | requiere |
|-----------|------------------|----------|
| `openai`  | `gpt-4o-mini`    | `api_key` de OpenAI |
| `gemini`  | `gemini-2.5-flash` | `api_key` de Google AI |

Las dos librerías se instalan con `requirements.txt`. Para este modo de uso,
escribe las claves en `keys.txt`, ubicado junto a `tray_app.py`:

```text
OPENAI_API_KEY=tu-clave-de-openai
GEMINI_API_KEY=tu-clave-de-google-ai
```

El agente usa primero la clave de `keys.txt`, luego `config.json` y finalmente
la variable de entorno correspondiente. No compartas este archivo ni lo subas
a un repositorio.

Como alternativa, las variables de entorno son:

```bat
setx OPENAI_API_KEY "tu-clave"
setx GEMINI_API_KEY "tu-clave"
```

Usa solo la variable correspondiente al proveedor seleccionado. Reinicia la
aplicación después de usar `setx`.

## Empaquetar como .exe (instalación final, sin abrir terminal)

```bat
build.bat
```

Esto genera `dist\ResumidorPantalla.exe`, ejecutable con doble clic, sin ventana
de consola. El proceso de construcción copia `keys.txt` automáticamente a
`dist`; debe permanecer junto al `.exe`.

### Arranque automático con Windows (opcional)

```bat
python autostart_windows.py activar "C:\ruta\completa\a\dist\ResumidorPantalla.exe"
```

Para quitarlo:
```bat
python autostart_windows.py desactivar
```

### Instalación automática

Ejecuta `instalar.bat`. El script intenta instalar Python mediante `winget` si no
está disponible, instala las dependencias, construye `dist\ResumidorPantalla.exe`
y copia el ejecutable y `keys.txt` automáticamente al escritorio. Después
completa las claves en el `keys.txt` del escritorio y abre
`ResumidorPantalla.exe` con doble clic.

Se requiere conexión a Internet durante la instalación. Si el PC no tiene
`winget`, instala Python 3.11 o superior manualmente y vuelve a ejecutar el script.

## Uso

- El widget aparece sin bordes y Windows lo mantiene como ventana superior sobre
  aplicaciones normales, juegos en modo ventana y juegos sin bordes.
- Presiona `Alt+Z` desde cualquier aplicación para capturar todas las pantallas. La imagen se
  conserva completa para mantener el contexto, pero el análisis se centra únicamente en las
  preguntas y sus opciones.
- Pulsa **imagen capturada** para mostrar una vista previa.
- La captura inicia automáticamente el análisis y también puedes pulsar **ANALIZAR**
  para repetirlo.
- Mientras se analiza aparece **CANCELAR**. Cancela la tarea asíncrona, cierra el
  cliente HTTP del proveedor y permite reintentar sin conservar esa conexión.
- Pulsa **CONFIG** en la parte inferior para editar desde la interfaz el proveedor,
  modelo, API key y el resto de parámetros de `config.json`. Pulsa **GUARDAR** para
  aplicar los cambios sin editar el archivo manualmente.
- El contexto conserva como máximo 3 preguntas. Al alcanzar ese límite se limpia
  automáticamente y la siguiente captura comienza una ventana nueva. Si el texto
  supera `max_resumen_chars`, también se reinicia sin hacer una llamada extra de
  compactación.
- La respuesta se muestra con este formato:

```text
Pregunta #1
Respuesta: A

Pregunta #2
Respuesta: A y C
```

La ventana se cierra con `Alt+F4`.

Nota: un juego en modo pantalla completa exclusiva puede impedir que Windows
muestre ventanas externas por encima. Para usar el widget sobre un juego,
selecciona modo ventana o pantalla completa sin bordes.

Por privacidad, el widget solicita a Windows `WDA_EXCLUDEFROMCAPTURE`: las
capturas de pantalla, grabaciones y sesiones remotas compatibles no muestran
la ventana. Esta protección depende del método de captura y no puede bloquear
cámaras físicas, drivers de captura o herramientas con privilegios especiales.
Además, el widget se oculta temporalmente al detectar `PrintScreen` o
`Win+Shift+S` y vuelve a aparecer después de 2,5 segundos. Las herramientas de
recorte que usan otros atajos o APIs no notifican su captura a las aplicaciones,
por lo que no pueden detectarse universalmente.

## Estructura del proyecto

```
resumidor_pantalla/
├── tray_app.py          # punto de entrada: widget + atajo global Alt+Z
├── capture.py           # captura + escala de grises + compresión JPEG
├── model_adapters.py    # adaptadores por proveedor (OpenAI/Gemini)
├── session_manager.py   # acumulación y compactación del resumen/contexto
├── config.py            # config persistente en %APPDATA%
├── autostart_windows.py # registro en el inicio de sesión de Windows
├── build.bat            # empaquetado a .exe con PyInstaller
├── instalar.bat         # instalación automática y empaquetado
├── preparar_icono.py    # convierte icon.jpg a icon.ico para Windows
├── icon.jpg             # icono de la aplicación
└── requirements.txt
```

## Notas de privacidad importantes

Este agente captura la pantalla de forma continua. Antes de instalarlo en un
equipo (propio o de terceros):

- Deja claro a cualquier otra persona que use el equipo que el agente está activo;
  el widget permanece visible, pero considera además un aviso si el equipo es compartido.
- Cada captura se envía al proveedor en la nube seleccionado (OpenAI o Gemini); evita
  activarlo mientras haya contraseñas, datos bancarios u otra información sensible.
- Revisa `historial.log` periódicamente si te preocupa qué se está registrando.
