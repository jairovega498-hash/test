"""
Registra (o quita) el agente para que arranque automáticamente
al iniciar sesión en Windows, usando el registro HKCU (no requiere admin).

Uso:
    python autostart_windows.py activar   "C:\\ruta\\a\\ResumidorPantalla.exe"
    python autostart_windows.py desactivar
"""
import sys
import winreg

CLAVE = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE_ENTRADA = "ResumidorPantalla"


def activar(ruta_exe: str):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, NOMBRE_ENTRADA, 0, winreg.REG_SZ, f'"{ruta_exe}"')
    print(f"Autostart activado: {ruta_exe}")


def desactivar():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, NOMBRE_ENTRADA)
        print("Autostart desactivado.")
    except FileNotFoundError:
        print("No había entrada de autostart registrada.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    accion = sys.argv[1].lower()
    if accion == "activar":
        if len(sys.argv) < 3:
            print("Falta la ruta al .exe")
            sys.exit(1)
        activar(sys.argv[2])
    elif accion == "desactivar":
        desactivar()
    else:
        print(__doc__)
