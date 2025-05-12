import sys
import os

def resource_path(relative_path):
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller y desarrollo."""
    if getattr(sys, 'frozen', False):
        # Estamos ejecutando en modo empaquetado por PyInstaller
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
            base_path = sys._MEIPASS
        else:
            # Fallback a directorio del ejecutable
            base_path = os.path.dirname(sys.executable)
    else:
        # Estamos en modo desarrollo
        base_path = os.path.abspath(os.path.dirname(__file__))
        # Si tus recursos están fuera de utils/, sube al root del proyecto:
        base_path = os.path.abspath(os.path.join(base_path, '..', '..'))
    
    return os.path.join(base_path, relative_path)
