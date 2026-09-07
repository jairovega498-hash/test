"""Protección de ventanas contra mecanismos de captura compatibles con Windows."""
import ctypes
import logging
import os
from ctypes import wintypes

logger = logging.getLogger(__name__)

WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

_user32 = None
if os.name == "nt":
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    _user32.SetWindowDisplayAffinity.restype = wintypes.BOOL


def set_capture_protection(hwnd: int, enabled: bool = True) -> bool:
    """Activa o desactiva la protección del HWND y devuelve si fue aceptada.

    En Windows 10 versión 2004 o posterior se solicita WDA_EXCLUDEFROMCAPTURE.
    En sistemas antiguos se intenta WDA_MONITOR, que oculta el contenido durante
    la proyección, pero no ofrece la misma semántica de exclusión.
    """
    if os.name != "nt" or _user32 is None:
        logger.warning("Protección de captura no disponible: el sistema no es Windows.")
        return False
    if not hwnd:
        logger.error("Protección de captura rechazada: HWND vacío.")
        return False

    affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
    if _user32.SetWindowDisplayAffinity(hwnd, affinity):
        logger.info(
            "Protección de captura %s para HWND %s%s.",
            "activada" if enabled else "desactivada",
            hwnd,
            " (WDA_EXCLUDEFROMCAPTURE)" if enabled else "",
        )
        return True

    error = ctypes.get_last_error()
    if enabled and _user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR):
        logger.warning(
            "WDA_EXCLUDEFROMCAPTURE fue rechazada para HWND %s (WinError %s); "
            "se aplicó fallback WDA_MONITOR.",
            hwnd,
            error,
        )
        return True

    logger.error(
        "Windows rechazó la protección de captura para HWND %s (WinError %s).",
        hwnd,
        error,
    )
    return False
