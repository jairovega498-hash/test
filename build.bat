@echo off
REM Empaqueta el agente como ejecutable de Windows sin consola visible.
REM Requiere Python 3.13 instalado y pyinstaller (ver requirements.txt).

python -m pip install -r requirements.txt
python preparar_icono.py
if errorlevel 1 goto :error

pyinstaller --clean --onefile --noconsole --icon "icon.ico" --name "ResumidorPantalla" tray_app.py
if errorlevel 1 goto :error
if exist keys.txt copy /Y keys.txt dist\keys.txt >nul
if exist "%USERPROFILE%\Desktop" copy /Y dist\ResumidorPantalla.exe "%USERPROFILE%\Desktop\ResumidorPantalla.exe" >nul
if exist keys.txt copy /Y keys.txt "%USERPROFILE%\Desktop\keys.txt" >nul

echo.
echo Listo. El ejecutable esta en dist\ResumidorPantalla.exe
echo Tambien se copio al escritorio.
echo Mantén keys.txt junto al ejecutable.
echo Para autostart:
echo   python autostart_windows.py activar "%cd%\dist\ResumidorPantalla.exe"
pause
exit /b 0

:error
echo.
echo ERROR: no se pudo preparar el ejecutable.
pause
exit /b 1
