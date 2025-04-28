"""
QR Code Generator and Manager Module.

This module provides functionality for generating and manipulating QR codes
for WiFi network credentials.
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
    """Data class for storing WiFi network credentials."""
    ssid: str
    password: Optional[str] = None
    encryption: str = "WPA2"
    property_type: Optional[str] = None

class QRManager:
    """Manages QR code generation and manipulation."""
    
    SUPPORTED_PROPERTIES = {"VLEV", "VLE", "VDPF", "VG", "VDP"}
    LOGO_PATHS = {
        "VLEV": "logos/VLEV.png",
        "VG": "logos/VDPF.png"
    }
    
    def __init__(self, output_dir: str = "codes"):
        """
        Initialize QR Manager.
        
        Args:
            output_dir (str): Directory to store generated QR codes
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_wifi_qr(self, credentials: WiFiCredentials) -> BytesIO:
        """
        Generate a QR code for WiFi credentials.
        
        Args:
            credentials (WiFiCredentials): WiFi network credentials
            
        Returns:
            BytesIO: Buffer containing the QR code image
        """
        try:
            # Generate WiFi configuration string
            wifi_config = helpers.make_wifi_data(
                ssid=credentials.ssid,
                password=credentials.password,
                security=credentials.encryption if credentials.encryption != "nopass" else None,
                hidden=False
            )
            
            # Create QR code
            qr = segno.make(wifi_config, error='H')
            
            # Save to buffer
            buffer = BytesIO()
            qr.save(buffer, kind='png', scale=10)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise
            
    def add_logo(self, qr_buffer: BytesIO, property_type: str) -> BytesIO:
        """
        Add a logo to the center of the QR code.
        
        Args:
            qr_buffer (BytesIO): Buffer containing the QR code image
            property_type (str): Property identifier for logo selection
            
        Returns:
            BytesIO: Buffer containing the modified QR code
        """
        try:
            # Normalize and validate property type
            property_type = self._normalize_property_type(property_type)
            if not property_type or property_type not in self.LOGO_PATHS:
                logger.warning(f"Invalid property type: {property_type}")
                return qr_buffer
                
            logo_path = self.LOGO_PATHS[property_type]
            if not os.path.exists(logo_path):
                logger.error(f"Logo file not found: {logo_path}")
                return qr_buffer
                
            # Open images
            qr_img = Image.open(qr_buffer).convert('RGBA')
            logo_img = Image.open(logo_path).convert('RGBA')
            
            # Calculate logo size (25% of QR code)
            logo_size = min(qr_img.size) // 4
            logo_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position for center placement
            x_pos = (qr_img.size[0] - logo_img.size[0]) // 2
            y_pos = (qr_img.size[1] - logo_img.size[1]) // 2
            
            # Create mask for smooth edges
            mask = logo_img.split()[3]
            
            # Paste logo
            qr_img.paste(logo_img, (x_pos, y_pos), mask)
            
            # Save result
            output = BytesIO()
            qr_img.save(output, format='PNG')
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Error adding logo to QR: {str(e)}")
            return qr_buffer
            
    def add_text(self, qr_buffer: BytesIO, ssid: str, password: Optional[str] = None) -> BytesIO:
        """
        Add SSID and password text below the QR code.
        
        Args:
            qr_buffer (BytesIO): Buffer containing the QR code image
            ssid (str): Network SSID
            password (Optional[str]): Network password
            
        Returns:
            BytesIO: Buffer containing the modified QR code
        """
        try:
            qr_img = Image.open(qr_buffer)
            width, height = qr_img.size
            
            # Create new image with space for text
            new_height = height + 60  # Add 60px for text
            new_img = Image.new('RGB', (width, new_height), 'white')
            new_img.paste(qr_img, (0, 0))
            
            # Configure font
            try:
                font = ImageFont.truetype("calibrib.ttf", 22)
            except:
                font = ImageFont.load_default()
                
            draw = ImageDraw.Draw(new_img)
            
            # Add SSID text
            text = f"SSID: {ssid}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (width - text_width) / 2
            draw.text((x_pos, height + 5), text, font=font, fill="black")
            
            # Add password text if provided
            if password:
                text = f"Pass: {password}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x_pos = (width - text_width) / 2
                draw.text((x_pos, height + 30), text, font=font, fill="black")
            
            # Save result
            output = BytesIO()
            new_img.save(output, format='PNG')
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Error adding text to QR: {str(e)}")
            return qr_buffer
            
    def save_qr(self, qr_buffer: BytesIO, filename: str) -> str:
        """
        Save the QR code to a file.
        
        Args:
            qr_buffer (BytesIO): Buffer containing the QR code image
            filename (str): Name for the output file
            
        Returns:
            str: Path to the saved file
        """
        try:
            if not filename.endswith('.png'):
                filename += '.png'
                
            output_path = os.path.join(self.output_dir, filename)
            
            with open(output_path, 'wb') as f:
                f.write(qr_buffer.getvalue())
                
            logger.info(f"QR code saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving QR code: {str(e)}")
            raise
            
    @staticmethod
    def _normalize_property_type(property_type: Optional[str]) -> Optional[str]:
        """
        Normalize property type to standard format.
        
        Args:
            property_type (Optional[str]): Property type to normalize
            
        Returns:
            Optional[str]: Normalized property type or None if invalid
        """
        if not property_type:
            return None
            
        property_type = property_type.upper().strip()
        if property_type in ('VLEV', 'VLE'):
            return 'VLEV'
        elif property_type in ('VDPF', 'VG', 'VDP'):
            return 'VG'
        return None