"""
Logging Utility Module.

This module provides centralized logging configuration for the QR generator application.
"""

import os
import logging
import datetime
from typing import Optional

class LogManager:
    """Manages application-wide logging configuration."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: str = "logs", debug: bool = False):
        """
        Initialize logging configuration.
        
        Args:
            log_dir (str): Directory to store log files
            debug (bool): Whether to enable debug logging
        """
        # Skip if already initialized
        if LogManager._initialized:
            return
            
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('vgQrGen')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        
        # File handler
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
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        LogManager._initialized = True
        
        # Initial log entries
        self.logger.info("Logging system initialized")
        if debug:
            self.logger.debug("Debug logging enabled")
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name (Optional[str]): Logger name for module-specific logging
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._initialized:
            cls()
        return logging.getLogger(name if name else 'vgQrGen')