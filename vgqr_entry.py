#!/usr/bin/env python
"""
Punto de entrada principal para la aplicación Generadora de QR.
Este archivo sirve como punto de entrada compatible con PyInstaller.
"""

import sys
import os
import argparse

def ensure_directories():
    """Garantiza que las carpetas necesarias para la aplicación existan."""
    # Determinar la ruta base (ya sea en modo desarrollo o empaquetado)
    if getattr(sys, 'frozen', False):
        # Modo PyInstaller
        base_dir = os.path.dirname(sys.executable)
    else:
        # Modo desarrollo
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crear directorios necesarios
    for folder in ['codes', 'logs']:
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"Asegurado directorio: {folder_path}")

def main():
    """Punto de entrada principal para la aplicación."""
    # Asegurar que las carpetas existan
    ensure_directories()
    
    # Asegurar que el directorio raíz esté en el path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    
    # Usar importaciones absolutas
    from vgQRGen.utils.logging_utils import LogManager
    from vgQRGen.gui.main_window import MainWindow
    
    # Analizar argumentos
    parser = argparse.ArgumentParser(
        description="Generador de Códigos QR WiFi - Herramienta GUI y CLI"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Habilitar registro de depuración"
    )
    args = parser.parse_args()
    
    # Inicializar registro
    logger = LogManager(debug=args.debug).get_logger()
    
    try:
        logger.info("Iniciando aplicación VG QR Generator")
        # Iniciar GUI
        app = MainWindow()
        app.run()
        logger.info("Aplicación finalizada correctamente")
        return 0
    except Exception as e:
        logger.critical(f"Error fatal al iniciar la aplicación: {str(e)}", exc_info=True)
        print(f"Error al iniciar la aplicación: {str(e)}", file=sys.stderr)
        return 1
    finally:
        # Asegurar que los logs se escriban y cierren correctamente
        LogManager.flush()
        LogManager.close()

if __name__ == "__main__":
    sys.exit(main())
