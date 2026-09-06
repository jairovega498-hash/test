# Resumidor de Pantalla — Agente en bandeja del sistema

Agente para Windows que observa el escritorio periódicamente, genera un resumen breve
de lo que ocurre (incluidas preguntas con opciones múltiples) usando un
modelo de visión, y mantiene un contexto acumulado y compactado sin saturar la
ventana de contexto del modelo. Funciona desde la bandeja del sistema, sin
consola visible; el último resumen se puede consultar en el título del ícono y
en el historial.
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
  "max_ancho_px": 1280,
  "calidad_jpeg": 70,
  "max_resumen_chars": 800,
  "guardar_log": true,
  "solo_si_cambia": true,
  "umbral_cambio": 0.02
}
```

### Cambiar de proveedor

| proveedor | modelo (ejemplo) | requiere |
|-----------|------------------|----------|
| `openai`  | `gpt-4o-mini`    | `api_key` de OpenAI |
| `gemini`  | `gemini-2.0-flash` | `api_key` de Google AI |

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

## Uso

- El ícono en la bandeja cambia de color: verde = activo, gris = sin cambios en
  pantalla (no reanalizó), rojo = error.
- Clic derecho → menú:
  - **Pausar / Reanudar**: detiene la captura sin cerrar el agente.
  - **Ver historial**: abre el log de resúmenes (`%APPDATA%\ResumidorPantalla\historial.log`).
  - **Editar configuración**: abre `config.json`.
  - **Salir**: cierra el agente.

## Estructura del proyecto

```
resumidor_pantalla/
├── tray_app.py          # punto de entrada: bandeja + loop principal
├── capture.py           # captura de pantalla + detección de cambios
├── model_adapters.py    # adaptadores por proveedor (OpenAI/Gemini)
├── session_manager.py   # acumulación y compactación del resumen/contexto
├── config.py            # config persistente en %APPDATA%
├── autostart_windows.py # registro en el inicio de sesión de Windows
├── build.bat            # empaquetado a .exe con PyInstaller
└── requirements.txt
```

## Notas de privacidad importantes

Este agente captura la pantalla de forma continua. Antes de instalarlo en un
equipo (propio o de terceros):

- Deja claro a cualquier otra persona que use el equipo que el agente está activo
  (el ícono de bandeja ya cumple parte de esa función; considera además un aviso
  visible si el equipo es compartido).
- Cada captura se envía al proveedor en la nube seleccionado (OpenAI o Gemini); evita
  activarlo mientras haya contraseñas, datos bancarios u otra información sensible.
- Revisa `historial.log` periódicamente si te preocupa qué se está registrando.
