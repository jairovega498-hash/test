@echo off
REM Empaqueta el agente como ejecutable de Windows sin consola visible.
REM Requiere Python 3.13 instalado y pyinstaller (ver requirements.txt).

python -m pip install -r requirements.txt

pyinstaller --onefile --noconsole --name "ResumidorPantalla" tray_app.py
if exist keys.txt copy /Y keys.txt dist\keys.txt >nul

echo.
echo Listo. El ejecutable esta en dist\ResumidorPantalla.exe
echo Mantén keys.txt junto al ejecutable.
echo Para autostart:
echo   python autostart_windows.py activar "%cd%\dist\ResumidorPantalla.exe"
pause
