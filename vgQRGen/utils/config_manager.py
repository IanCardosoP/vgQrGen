"""
Módulo para manejar la configuración persistente de la aplicación.
"""

import os
import json
from typing import Dict, List, Optional, Any
from .logging_utils import LogManager
from .path_utils import resource_path

logger = LogManager.get_logger(__name__)

class ConfigManager:
    """Gestiona la configuración persistente de la aplicación."""
    
    # Estructura predeterminada para el archivo de configuración
    DEFAULT_CONFIG = {
        "recent_files": [],  # Lista de diccionarios {path: str, last_sheet: str}
        "max_recent_files": 5,  # Máximo número de archivos recientes a recordar
        "sheet_configs": {}  # Configuraciones por hoja {file_path+sheet_name: config}
    }
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializar gestor de configuración.
        
        Args:
            config_file (str): Nombre del archivo de configuración
        """
        self.config_file = resource_path(config_file)
        
        # Verificar y asegurar que el archivo de configuración exista con la estructura adecuada
        self._ensure_config_file()
        
        # Cargar la configuración
        self.config = self._load_config()
        
    def _ensure_config_file(self):
        """
        Asegurar que el archivo de configuración exista y tenga la estructura básica.
        Si no existe, lo crea con los valores predeterminados.
        """
        # Verificar si el archivo existe
        if not os.path.exists(self.config_file):
            logger.info(f"Archivo de configuración '{self.config_file}' no encontrado. Creando uno nuevo...")
            try:
                # Asegurar que el directorio exista
                directory = os.path.dirname(self.config_file)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    logger.debug(f"Directorio creado para archivo de configuración: {directory}")
                
                # Crear el archivo con la configuración predeterminada
                self._write_default_config()
                logger.info(f"Archivo de configuración '{self.config_file}' creado exitosamente")
            except Exception as e:
                logger.error(f"Error al crear archivo de configuración: {str(e)}")
    
    def _write_default_config(self):
        """Escribir la configuración predeterminada al archivo de configuración."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=4)
        
    def _load_config(self) -> dict:
        """
        Cargar configuración desde archivo. Si el archivo está corrupto o no tiene
        la estructura correcta, restaura la configuración predeterminada.
        
        Returns:
            dict: Configuración cargada o predeterminada
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    try:
                        loaded_config = json.load(f)
                        
                        # Verificar que sea un diccionario válido
                        if not isinstance(loaded_config, dict):
                            logger.warning("El archivo de configuración no contiene un objeto JSON válido. Restaurando configuración predeterminada.")
                            return self.DEFAULT_CONFIG.copy()
                        
                        # Asegurar que todas las propiedades existan
                        config_modified = False
                        for key, value in self.DEFAULT_CONFIG.items():
                            if key not in loaded_config:
                                loaded_config[key] = value
                                config_modified = True
                                logger.debug(f"Agregada sección faltante '{key}' a la configuración")
                        
                        # Si se agregó alguna propiedad, guardar la configuración actualizada
                        if config_modified:
                            self.config = loaded_config
                            self.save_config()
                            logger.info("Archivo de configuración actualizado con secciones faltantes")
                        
                        return loaded_config
                    except json.JSONDecodeError:
                        logger.error("Error al decodificar el archivo JSON. Restaurando configuración predeterminada.")
                        # Hacer backup del archivo corrupto
                        if os.path.getsize(self.config_file) > 0:
                            backup_file = f"{self.config_file}.bak"
                            try:
                                import shutil
                                shutil.copy2(self.config_file, backup_file)
                                logger.info(f"Se ha creado una copia de seguridad del archivo corrupto: {backup_file}")
                            except Exception as e:
                                logger.error(f"No se pudo crear copia de seguridad: {str(e)}")
                        
                        # Restaurar configuración predeterminada
                        self._write_default_config()
                        return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error inesperado al cargar configuración: {str(e)}")
        
        # Si hay algún problema o el archivo no existe, devolver configuración predeterminada
        return self.DEFAULT_CONFIG.copy()
        
    def save_config(self):
        """Guardar configuración actual en archivo."""
        try:
            # Asegurar que la configuración tenga todas las secciones necesarias
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in self.config:
                    self.config[key] = value
                    logger.debug(f"Agregada sección faltante '{key}' antes de guardar configuración")
            
            # Guardar configuración
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.debug("Configuración guardada exitosamente")
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
        
    def _get_sheet_key(self, file_path: str, sheet_name: str) -> str:
        """
        Generar clave única para identificar una hoja específica.
        
        Args:
            file_path (str): Ruta al archivo Excel
            sheet_name (str): Nombre de la hoja
            
        Returns:
            str: Clave única para la hoja
        """
        file_path = os.path.normpath(file_path)
        return f"{file_path}::{sheet_name}"
        
    def save_sheet_config(self, file_path: str, sheet_name: str, config_data: Dict[str, Any]):
        """
        Guardar configuración específica para una hoja.
        
        Args:
            file_path (str): Ruta al archivo Excel
            sheet_name (str): Nombre de la hoja
            config_data (Dict[str, Any]): Datos de configuración a guardar
        """
        sheet_key = self._get_sheet_key(file_path, sheet_name)
        
        # Asegurar que la sección sheet_configs existe
        if "sheet_configs" not in self.config:
            self.config["sheet_configs"] = {}
            
        # Guardar configuración
        self.config["sheet_configs"][sheet_key] = config_data
        
        # Guardar cambios inmediatamente
        self.save_config()
        logger.debug(f"Configuración guardada para hoja '{sheet_name}' en '{file_path}'")
        
    def get_sheet_config(self, file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Obtener configuración específica para una hoja.
        
        Args:
            file_path (str): Ruta al archivo Excel
            sheet_name (str): Nombre de la hoja
            
        Returns:
            Dict[str, Any]: Datos de configuración de la hoja o diccionario vacío
        """
        sheet_key = self._get_sheet_key(file_path, sheet_name)
        
        # Asegurar que la sección sheet_configs existe
        if "sheet_configs" not in self.config:
            self.config["sheet_configs"] = {}
            
        # Retornar configuración o diccionario vacío si no existe
        return self.config["sheet_configs"].get(sheet_key, {})