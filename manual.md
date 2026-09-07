# Manual de usuario

## USO DE LA APP

1. Abre `ResumidorPantalla.exe`.
2. Coloca en pantalla la pregunta que quieres analizar.
3. Pulsa `Alt+Z` para capturar la pantalla.
4. Espera a que termine el análisis automático.
5. Lee la respuesta en el panel del widget. Usa el desplazamiento si es larga.
6. Pulsa **SALIR** y confirma cuando quieras cerrar la aplicación.

## 1. Instalación

En Windows, ejecuta `instalar.bat` desde la carpeta del proyecto. El instalador:

- Instala las dependencias necesarias.
- Construye `ResumidorPantalla.exe`.
- Copia el ejecutable y `keys.txt` al escritorio.
- Usa `icon.jpg` como icono de la aplicación.

También puedes ejecutar el programa directamente con:

```bat
python tray_app.py
```

## 2. Configurar el proveedor

Pulsa el botón **CONFIG** del widget. Desde ahí puedes modificar:

- Proveedor: `openai` o `gemini`.
- Modelo.
- API key.
- Calidad y tamaño de la imagen.
- Historial y demás opciones disponibles.

Pulsa **GUARDAR** para guardar los cambios en:

```text
%APPDATA%\ResumidorPantalla\config.json
```

También puedes configurar las claves en `keys.txt`, ubicado junto al ejecutable:

```text
OPENAI_API_KEY=tu-clave-de-openai
GEMINI_API_KEY=tu-clave-de-gemini
```

La API key guardada desde **CONFIG** tiene prioridad sobre `keys.txt`.

## 3. Capturar y analizar

1. Abre la aplicación.
2. Pulsa `Alt+Z` desde cualquier aplicación.
3. Se capturará el escritorio virtual completo.
4. La imagen se comprime y se convierte a escala de grises.
5. El análisis comienza automáticamente.
6. La respuesta aparecerá en el panel del widget.

El análisis se centra en las preguntas y opciones visibles, ignorando contenido ajeno como barras, menús y notificaciones.

## 4. Controles del widget

- **imagen capturada**: muestra una vista previa de la última captura.
- **ANALIZAR**: repite el análisis de la captura actual.
- **CANCELAR**: aparece únicamente durante un análisis activo y cancela la tarea para permitir un reintento.
- **CONFIG**: abre la configuración completa.
- **SALIR**: cierra la aplicación después de confirmar `¿Está seguro?`.

La aplicación conserva como máximo tres preguntas en cada ventana de contexto.
Después inicia automáticamente una ventana nueva.

El panel de respuesta tiene desplazamiento vertical para leer respuestas largas.

## 5. Ventana flotante

El widget permanece sobre otras ventanas y puede moverse arrastrando su área principal. Está diseñado para funcionar sobre aplicaciones normales, juegos en modo ventana y juegos sin bordes.

Los juegos en pantalla completa exclusiva pueden impedir que Windows muestre ventanas externas encima.

## 6. Privacidad

El widget solicita a Windows que lo excluya de capturas y grabaciones compatibles. También intenta ocultarse temporalmente al detectar `PrintScreen`.

Esta protección no puede garantizarse frente a cámaras físicas, drivers especiales o herramientas ejecutadas con privilegios elevados.

Las capturas se envían al proveedor seleccionado, OpenAI o Gemini. No uses la aplicación mientras haya contraseñas, información bancaria u otros datos sensibles visibles.
