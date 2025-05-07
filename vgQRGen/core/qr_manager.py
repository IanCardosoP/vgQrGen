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
        "VDPF": "logos/VDPF.png"
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
            
            # Guardar en buffer con escala aumentada para mayor resolución
            buffer = BytesIO()
            qr.save(buffer, kind='png', scale=30, border=4)
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
            
            # Ya no necesitamos agregar espacio para texto aquí, se agregará en el método save_qr
            # en el lienzo vertical de 825x1275
            
            # Configurar fuente con un tamaño proporcional a la imagen final
            font_size = 36  # Tamaño de fuente mayor para la imagen vertical
            try:
                font = ImageFont.truetype("calibrib.ttf", font_size)
            except:
                try:
                    # Intentar con una fuente alternativa
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # En lugar de modificar el QR, vamos a devolver los datos que necesitamos
            # para que el método save_qr los coloque en la posición correcta
            
            # Guardamos la imagen del QR tal cual está
            output = BytesIO()
            qr_img.save(output, format='PNG')
            output.seek(0)
            
            # El texto se agregará en save_qr
            return output
            
        except Exception as e:
            logger.error(f"Error preparando QR para texto: {str(e)}")
            return qr_buffer
            
    def save_qr(self, qr_buffer: BytesIO, filename: str, ssid: str = "", password: Optional[str] = None) -> str:
        """
        Guardar el código QR en un archivo.
        
        Args:
            qr_buffer (BytesIO): Buffer conteniendo la imagen del código QR
            filename (str): Nombre para el archivo de salida
            ssid (str): SSID de la red para añadir como texto
            password (Optional[str]): Contraseña de la red para añadir como texto
            
        Returns:
            str: Ruta al archivo guardado
        """
        try:
            if not filename.endswith('.png'):
                filename += '.png'
                
            output_path = os.path.join(self.output_dir, filename)
            
            # Abrir la imagen del buffer
            img = Image.open(qr_buffer)
            
            # Crear un nuevo lienzo blanco con el tamaño estandarizado vertical (825x1275)
            standardized_img = Image.new('RGB', (825, 1100), 'white')
            
            # Redimensionar proporcionalmente el QR para que quepa en el lienzo
            # pero respetando su relación de aspecto original
            img_width, img_height = img.size
            
            # Calcular dimensiones para el área principal del QR (manteniendo proporción)
            # Usaremos aproximadamente 2/3 del alto para el QR
            target_qr_height = 825  # Misma anchura que el lienzo
            qr_area_height = int(1275 * 0.7)  # 70% del alto total para el área del QR
            
            if img_width / img_height > 825 / qr_area_height:  # Si el QR es más ancho proporcionalmente
                new_width = 825
                new_height = int(img_height * (new_width / img_width))
            else:  # Si el QR es más alto proporcionalmente
                new_height = qr_area_height
                new_width = int(img_width * (new_height / img_height))
                
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Calcular posición para centrar el QR en la parte superior del lienzo
            x_pos = (825 - new_width) // 2
            y_pos = 50  # Margen superior de 50px
            
            # Pegar la imagen redimensionada en el lienzo centrado
            standardized_img.paste(resized_img, (x_pos, y_pos))
            
            # Añadir texto con información WiFi en la parte inferior
            if ssid:
                # Configurar fuente
                font_size = 40  # Tamaño de fuente mayor para la imagen vertical
                try:
                    font = ImageFont.truetype("calibrib.ttf", font_size)
                except:
                    try:
                        # Intentar con una fuente alternativa
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                draw = ImageDraw.Draw(standardized_img)
                
                # Posición base para el texto (justo debajo del QR)
                text_y_pos = y_pos + new_height + 10 # Modificar espaciado entre QR y texto (reduce para menos espacio)
                
                # Agregar texto SSID
                text = f"SSID: {ssid}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x_text_pos = (825 - text_width) / 2
                draw.text((x_text_pos, text_y_pos), text, font=font, fill="black")
                
                # Agregar texto de contraseña si se proporciona
                if password:
                    text = f"Password: {password}"
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    x_text_pos = (825 - text_width) / 2
                    draw.text((x_text_pos, text_y_pos + font_size + 5), text, font=font, fill="black")
            
            # Guardar la imagen estandarizada
            standardized_img.save(output_path, format='PNG')
            
            logger.info(f"Código QR guardado en: {output_path} con resolución estandarizada vertical de 825x1275")
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
        elif property_type in ('VDPF', 'VG', 'VDP', 'FLAMINGOS', 'Flamingos'):
            return 'VDPF'
        elif property_type in ('SIN LOGO', 'NONE', 'NO LOGO'):
            return None
        return None