"""
Módulo Generador y Gestor de Códigos QR.

Este módulo proporciona funcionalidad para generar y manipular códigos QR
para credenciales de redes WiFi.
"""

import os
from io import BytesIO
from dataclasses import dataclass
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import segno
from segno import helpers
from ..utils.logging_utils import LogManager

logger = LogManager.get_logger(__name__)

@dataclass
class WiFiCredentials:
    """Clase de datos para almacenar credenciales de red WiFi."""
    ssid: str
    password: Optional[str] = None
    encryption: str = "WPA2" # Valor por defecto. 
    property_type: Optional[str] = None

class QRManager:
    """Gestiona la generación y manipulación de códigos QR."""
    
    LOGO_PATHS = {
        "VLEV": "logos/VLEV.png",
        "VG": "logos/VDPF.png"
    }
    
    def __init__(self, output_dir: str = "codes"):
        """
        Inicializar Gestor QR.
        
        Args:
            output_dir (str): Directorio para almacenar códigos QR generados
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_wifi_qr(self, credentials: WiFiCredentials) -> BytesIO:
        """
        Generar un código QR para credenciales WiFi.
        
        Args:
            credentials (WiFiCredentials): Credenciales de red WiFi
            
        Returns:
            BytesIO: Buffer conteniendo la imagen del código QR
        """
        try:
            logger.info(f"Generando código QR para SSID: {credentials.ssid}")
            logger.debug(f"Detalles - Encriptación: {credentials.encryption}, Propiedad: {credentials.property_type}")
            
            # Generar cadena de configuración WiFi
            wifi_config = helpers.make_wifi_data(
                ssid=credentials.ssid,
                password=credentials.password,
                security=credentials.encryption if credentials.encryption != "nopass" else None,
                hidden=False
            )
            
            # Crear código QR
            qr = segno.make(wifi_config, error='H')
            logger.debug("Código QR generado con nivel de corrección 'H'")
            
            # Guardar en buffer
            buffer = BytesIO()
            qr.save(buffer, kind='png', scale=10)
            buffer.seek(0)
            
            logger.info("Código QR generado exitosamente")
            return buffer
            
        except Exception as e:
            logger.error(f"Error generando código QR: {str(e)}", exc_info=True)
            raise
            
    def add_logo(self, qr_buffer: BytesIO, property_type: str) -> BytesIO:
        """
        Agregar un logotipo al centro del código QR.
        
        Args:
            qr_buffer (BytesIO): Buffer conteniendo la imagen del código QR
            property_type (str): Identificador de propiedad para selección de logotipo
            
        Returns:
            BytesIO: Buffer conteniendo el código QR modificado
        """
        try:
            # Normalizar y validar tipo de propiedad
            property_type = self._normalize_property_type(property_type)
            if not property_type or property_type not in self.LOGO_PATHS:
                logger.warning(f"Tipo de propiedad inválido: {property_type}")
                return qr_buffer
                
            logo_path = self.LOGO_PATHS[property_type]
            if not os.path.exists(logo_path):
                logger.error(f"Archivo de logo no encontrado: {logo_path}")
                return qr_buffer
                
            # Abrir imágenes
            qr_img = Image.open(qr_buffer).convert('RGBA')
            logo_img = Image.open(logo_path).convert('RGBA')
            
            # Calcular tamaño del logo (25% del código QR)
            logo_size = min(qr_img.size) // 3.7
            # 4 = 25% del tamaño del QR (ideal)
            # 3.5 = 28.5% del tamaño del QR (tamaño recomendado)
            # 3 = 33% del tamaño del QR (máximo recomendado)
            logo_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calcular posición para centrado
            x_pos = (qr_img.size[0] - logo_img.size[0]) // 2
            y_pos = (qr_img.size[1] - logo_img.size[1]) // 2
            
            # Crear máscara para bordes suaves
            mask = logo_img.split()[3]
            
            # Pegar logo
            qr_img.paste(logo_img, (x_pos, y_pos), mask)
            
            # Guardar resultado
            output = BytesIO()
            qr_img.save(output, format='PNG')
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Error agregando logo al QR: {str(e)}")
            return qr_buffer
            
    def add_text(self, qr_buffer: BytesIO, ssid: str, password: Optional[str] = None) -> BytesIO:
        """
        Agregar texto de SSID y contraseña debajo del código QR.
        
        Args:
            qr_buffer (BytesIO): Buffer conteniendo la imagen del código QR
            ssid (str): SSID de la red
            password (Optional[str]): Contraseña de la red
            
        Returns:
            BytesIO: Buffer conteniendo el código QR modificado
        """
        try:
            qr_img = Image.open(qr_buffer)
            width, height = qr_img.size
            
            # Crear nueva imagen con espacio para texto
            new_height = height + 60  # Agregar 60px para texto
            new_img = Image.new('RGB', (width, new_height), 'white')
            new_img.paste(qr_img, (0, 0))
            
            # Configurar fuente
            try:
                font = ImageFont.truetype("calibrib.ttf", 26)
            except:
                font = ImageFont.load_default()
                
            draw = ImageDraw.Draw(new_img)
            
            # Agregar texto SSID
            text = f"SSID: {ssid}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (width - text_width) / 2
            draw.text((x_pos, height + 5), text, font=font, fill="black")
            
            # Agregar texto de contraseña si se proporciona
            if password:
                text = f"Password: {password}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x_pos = (width - text_width) / 2
                draw.text((x_pos, height + 30), text, font=font, fill="black")
            
            # Guardar resultado
            output = BytesIO()
            new_img.save(output, format='PNG')
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Error agregando texto al QR: {str(e)}")
            return qr_buffer
            
    def save_qr(self, qr_buffer: BytesIO, filename: str) -> str:
        """
        Guardar el código QR en un archivo.
        
        Args:
            qr_buffer (BytesIO): Buffer conteniendo la imagen del código QR
            filename (str): Nombre para el archivo de salida
            
        Returns:
            str: Ruta al archivo guardado
        """
        try:
            if not filename.endswith('.png'):
                filename += '.png'
                
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'wb') as f:
                f.write(qr_buffer.getvalue())
                
            logger.info(f"Código QR guardado en: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error guardando código QR: {str(e)}")
            raise
            
    @staticmethod
    def _normalize_property_type(property_type: Optional[str]) -> Optional[str]:
        """
        Normalizar tipo de propiedad a formato estándar.
        
        Args:
            property_type (Optional[str]): Tipo de propiedad a normalizar
            
        Returns:
            Optional[str]: Tipo de propiedad normalizado o None si es inválido
        """
        if not property_type:
            return None
            
        property_type = property_type.upper().strip()
        if property_type in ('VLEV', 'VLE'):
            return 'VLEV'
        elif property_type in ('VDPF', 'VG', 'VDP'):
            return 'VG'
        elif property_type in ('SIN LOGO', 'NONE', 'NO LOGO'):
            return None
        return None