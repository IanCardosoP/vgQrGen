"""
Módulo de Utilidades de Registro.

Este módulo proporciona una configuración centralizada de registro para la aplicación generadora de QR.
"""

import os
import logging
import datetime
import sys
from typing import Optional
from .path_utils import resource_path

class LogManager:
    """Gestiona la configuración de registro para toda la aplicación."""
    
    _instance = None
    _initialized = False
    _file_handler = None
    _console_handler = None
    
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
            
        self.log_dir = resource_path(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Crear registrador raíz
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Prevenir manejadores duplicados
        if self.logger.handlers:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
        # Manejador de consola
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        self._console_handler.setFormatter(console_format)
        
        # Manejador de archivo
        log_file = os.path.join(
            self.log_dir,
            f"vgQrGen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self._file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self._file_handler.setLevel(logging.DEBUG)  # Siempre registrar todo a archivo
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._file_handler.setFormatter(file_format)
        
        # Agregar manejadores
        self.logger.addHandler(self._console_handler)
        self.logger.addHandler(self._file_handler)
        
        # Configurar propagación correcta
        for name in ['vgQrGen', 'openpyxl', 'PIL']:
            module_logger = logging.getLogger(name)
            module_logger.setLevel(logging.DEBUG if debug else logging.INFO)
            module_logger.propagate = True
        
        LogManager._initialized = True
        
        # Entradas iniciales de registro
        main_logger = logging.getLogger('vgQrGen')
        main_logger.info("Sistema de registro inicializado")
        main_logger.info(f"Archivo de registro: {log_file}")
        if debug:
            main_logger.debug("Registro de depuración habilitado")
    
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
            
        logger_name = name if name else 'vgQrGen'
        logger = logging.getLogger(logger_name)
        
        # Asegurar que este logger tiene el nivel y propagación correctos
        logger.setLevel(logging.DEBUG if cls._instance and getattr(cls._instance, 'logger', None) and cls._instance.logger.level == logging.DEBUG else logging.INFO)
        logger.propagate = True
        
        return logger
        
    @classmethod
    def flush(cls):
        """Forzar la escritura de todos los mensajes de registro pendientes al archivo."""
        if cls._initialized and cls._instance and cls._instance._file_handler:
            cls._instance._file_handler.flush()
            
    @classmethod
    def close(cls):
        """Cerrar correctamente los manejadores de registro."""
        if cls._initialized and cls._instance:
            if cls._instance._file_handler:
                cls._instance._file_handler.close()
            if cls._instance._console_handler:
                cls._instance._console_handler.close()