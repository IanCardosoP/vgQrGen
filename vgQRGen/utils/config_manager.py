"""
Módulo para manejar la configuración persistente de la aplicación.
"""

import os
import json
from typing import Dict, List, Optional
from .logging_utils import LogManager

logger = LogManager.get_logger(__name__)

class ConfigManager:
    """Gestiona la configuración persistente de la aplicación."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializar gestor de configuración.
        
        Args:
            config_file (str): Nombre del archivo de configuración
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Cargar configuración desde archivo."""
        default_config = {
            "recent_files": [],  # Lista de diccionarios {path: str, last_sheet: str}
            "max_recent_files": 5  # Máximo número de archivos recientes a recordar
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando configuración: {str(e)}")
        
        return default_config
        
    def save_config(self):
        """Guardar configuración actual en archivo."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")
            
    def add_recent_file(self, file_path: str, sheet_name: str):
        """
        Agregar o actualizar archivo reciente.
        
        Args:
            file_path (str): Ruta al archivo Excel
            sheet_name (str): Nombre de la última hoja seleccionada
        """
        # Normalizar path
        file_path = os.path.normpath(file_path)
        
        # Crear nuevo registro
        new_entry = {"path": file_path, "last_sheet": sheet_name}
        
        # Eliminar si ya existe
        self.config["recent_files"] = [
            f for f in self.config["recent_files"] 
            if f["path"] != file_path
        ]
        
        # Agregar al principio
        self.config["recent_files"].insert(0, new_entry)
        
        # Mantener solo los últimos N archivos
        self.config["recent_files"] = self.config["recent_files"][:self.config["max_recent_files"]]
        
        # Guardar cambios
        self.save_config()
        
    def get_recent_files(self) -> List[Dict[str, str]]:
        """
        Obtener lista de archivos recientes.
        
        Returns:
            List[Dict[str, str]]: Lista de diccionarios con path y última hoja
        """
        # Filtrar solo los archivos que aún existen
        valid_files = [
            f for f in self.config["recent_files"]
            if os.path.exists(f["path"])
        ]
        
        # Actualizar lista si se eliminaron archivos
        if len(valid_files) != len(self.config["recent_files"]):
            self.config["recent_files"] = valid_files
            self.save_config()
            
        return valid_files
        
    def get_last_sheet(self, file_path: str) -> Optional[str]:
        """
        Obtener última hoja seleccionada para un archivo.
        
        Args:
            file_path (str): Ruta al archivo Excel
            
        Returns:
            Optional[str]: Nombre de la última hoja seleccionada o None
        """
        file_path = os.path.normpath(file_path)
        for f in self.config["recent_files"]:
            if f["path"] == file_path:
                return f["last_sheet"]
        return None