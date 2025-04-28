"""
Módulo de Utilidades de Registro.

Este módulo proporciona una configuración centralizada de registro para la aplicación generadora de QR.
"""

import os
import logging
import datetime
from typing import Optional

class LogManager:
    """Gestiona la configuración de registro para toda la aplicación."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Asegurar patrón singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: str = "logs", debug: bool = False):
        """
        Inicializar configuración de registro.
        
        Args:
            log_dir (str): Directorio para almacenar archivos de registro
            debug (bool): Si se debe habilitar el registro de depuración
        """
        # Omitir si ya está inicializado
        if LogManager._initialized:
            return
            
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Crear registrador
        self.logger = logging.getLogger('vgQrGen')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Prevenir manejadores duplicados
        if self.logger.handlers:
            return
            
        # Manejador de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        
        # Manejador de archivo
        log_file = os.path.join(
            log_dir,
            f"vgQrGen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        
        # Agregar manejadores
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        LogManager._initialized = True
        
        # Entradas iniciales de registro
        self.logger.info("Sistema de registro inicializado")
        if debug:
            self.logger.debug("Registro de depuración habilitado")
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Obtener una instancia de registrador.
        
        Args:
            name (Optional[str]): Nombre del registrador para registro específico de módulo
            
        Returns:
            logging.Logger: Instancia de registrador configurada
        """
        if not cls._initialized:
            cls()
        return logging.getLogger(name if name else 'vgQrGen')