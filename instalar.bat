@echo off
setlocal
title Instalador - Resumidor de Pantalla

echo ================================================
echo   Instalador de Resumidor de Pantalla
echo ================================================
echo.

where python >nul 2>nul
if not errorlevel 1 set "PYTHON=python"

if not defined PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON=py -3"
)

if not defined PYTHON (
    where winget >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python y winget no estan disponibles.
        echo Instala Python 3.11 o superior desde https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo Python no encontrado. Instalando Python 3.13 con winget...
    winget install --id Python.Python.3.13 --exact --scope user --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :error
    set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

echo Instalando dependencias...
%PYTHON% -m pip install --upgrade pip
if errorlevel 1 goto :error
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Construyendo ResumidorPantalla.exe...
%PYTHON% preparar_icono.py
if errorlevel 1 goto :error
%PYTHON% -m PyInstaller --clean --onefile --noconsole --icon "icon.ico" --name "ResumidorPantalla" tray_app.py
if errorlevel 1 goto :error

if not exist keys.txt (
    echo ADVERTENCIA: no existe keys.txt.
    echo Crea ese archivo antes de ejecutar el programa.
) else (
    copy /Y keys.txt dist\keys.txt >nul
)

if not exist "%USERPROFILE%\Desktop" mkdir "%USERPROFILE%\Desktop"
copy /Y dist\ResumidorPantalla.exe "%USERPROFILE%\Desktop\ResumidorPantalla.exe" >nul
if exist keys.txt copy /Y keys.txt "%USERPROFILE%\Desktop\keys.txt" >nul

echo.
echo Instalacion terminada.
echo Ejecutable: %cd%\dist\ResumidorPantalla.exe
echo Acceso directo ejecutable copiado al escritorio.
echo Mantén keys.txt junto al ejecutable.
echo.
pause
exit /b 0

:error
echo.
echo ERROR: la instalacion no pudo completarse.
pause
exit /b 1