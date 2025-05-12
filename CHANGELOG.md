# Historial de cambios

Todas las modificaciones notables de este proyecto serán documentadas en este archivo.

## [1.0.0] - 2025-05-12

### Características iniciales
- Generación de códigos QR para redes WiFi con tipos de encriptación configurables
- Importación de datos desde archivos Excel con detección automática de columnas
- Vista previa de códigos QR antes de guardar
- Personalización con logos de propiedades (VLEV, VDPF)
- Inclusión de texto SSID y contraseña debajo del código QR
- Interfaz gráfica con pestañas para diferentes modos de operación
- Sistema de registro (logs) para facilitar la depuración

### Mejoras
- Optimización a formato PNG-8 para mejorar eficiencia y velocidad
- Corrección de problemas de indentación en el código
- Configuración para compilación con PyInstaller
- Sistema para manejo de rutas en desarrollo y entorno empaquetado

### Correcciones
- Arreglo del problema de indentación en qr_manager.py para mostrar correctamente el texto de contraseña
- Optimización del formato de imagen para mejor eficiencia
