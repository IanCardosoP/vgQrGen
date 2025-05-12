"""
Punto de entrada principal para la aplicación Generadora de QR.

Este módulo inicializa el sistema de registro y arranca la aplicación GUI.
"""

import sys
import argparse
from .utils.logging_utils import LogManager
from .gui.main_window import MainWindow

def parse_args():
    """Analizar argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Generador de Códigos QR WiFi - Herramienta GUI y CLI"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Habilitar registro de depuración"
    )
    return parser.parse_args()

def main():
    """Punto de entrada principal para la aplicación."""
    args = parse_args()
    
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