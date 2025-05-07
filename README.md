# Generador de Códigos QR para WiFi

Una aplicación Python para generar códigos QR para redes WiFi, con soporte para importación de archivos Excel y entrada manual. Esta herramienta está diseñada para facilitar la creación masiva de códigos QR para configuraciones WiFi en propiedades hoteleras.

## Características

- Genera códigos QR para redes WiFi con tipos de encriptación configurables (WPA2, WPA, WEP, sin seguridad)
- Importa datos de red desde archivos Excel con detección automática de columnas
- Agrega logotipos de propiedades a los códigos QR (VLEV, VDPF, etc.)
- Agrega texto de SSID y contraseña debajo de los códigos QR para fácil referencia
- Vista previa de códigos QR antes de guardar
- Interfaz gráfica intuitiva con pestañas para diferentes modos de operación
- Sistema completo de registro (logs) para facilitar la depuración
- Recuerda últimos archivos y hojas utilizados
- Capacidad para generar QR individuales o por lotes

## Instalación

1. Clonar este repositorio
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

O alternativamente, instalar las dependencias individualmente:
```bash
pip install openpyxl>=3.1.5 Pillow>=11.2.1 segno>=1.6.6 tqdm>=4.67.1 colorama>=0.4.6 et_xmlfile>=2.0.0
```

## Uso

### Iniciar la Aplicación

```bash
python -m vgQRGen [--debug]
```

La opción `--debug` activa el registro detallado para facilitar la solución de problemas.

### Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas:
- **Número de habitación** (obligatorio): Identificador único como 1101A, 3506B
- **SSID** (obligatorio): Nombre de la red WiFi
- **Contraseña** (opcional): Para redes protegidas
- **Tipo de encriptación** (opcional): WPA2 (predeterminado), WPA, WEP, o nopass (sin seguridad)
- **Tipo de propiedad** (opcional): Para selección automática de logotipo

La aplicación detecta automáticamente los nombres de columnas basándose en palabras clave comunes en español e inglés. Si la detección automática falla, se puede configurar manualmente las columnas a través de la interfaz.

```python
# Palabras clave para auto-detectar encabezados de columnas
    COLUMN_KEYWORDS = {
        'room': ['room', 'habitacion', 'habitación', 'number', 'número', 'hab', 'cuarto', 'villa'],
        'ssid': ['ssid', 'network', 'red', 'wifi', 'nombre', 'name', 'net'],
        'password': ['password', 'contraseña', 'pass', 'key', 'clave', 'pwd', 'contrasena'],
        'encryption': ['security', 'encryption', 'seguridad', 'encriptación', 'type', 'tipo', 'encriptacion'],
        'property': ['property', 'propiedad', 'hotel', 'region', 'zona', 'lugar', 'site']
    }
```

### Características de la Interfaz Gráfica

#### Pestaña "Importar Excel"
- **Selección de archivo**: Examinar o seleccionar de archivos recientes
- **Selección de hoja**: Elegir la hoja de cálculo a utilizar
- **Configuración de seguridad**: 
  - Opción para usar seguridad definida en Excel o valor predeterminado
  - Radio buttons para seleccionar tipo de seguridad predeterminada
- **Configuración de propiedad**:
  - Opción para usar propiedad definida en Excel o valor predeterminado
  - Radio buttons para seleccionar tipo de propiedad predeterminada
- **Configuración manual de columnas**: En caso de fallar la detección automática
- **Búsqueda de habitación**: Campo para buscar habitaciones específicas
- **Generación de QR**: Botones para generar código QR para una habitación o todas

#### Pestaña "Entrada Manual"
- **Entrada de credenciales**:
  - Campos para SSID y contraseña
  - Selección de tipo de seguridad
  - Selección de propiedad para el logotipo
- **Generación de QR**: Botón para generar código QR con los datos ingresados

#### Área de Vista Previa (común a ambas pestañas)
- Vista previa del código QR generado
- Información de configuración (SSID, contraseña, seguridad, propiedad)

#### Funciones Comunes
- **Abrir Carpeta de Códigos**: Abre el explorador de archivos en la carpeta donde se guardan los QR
- **Abrir Último QR**: Abre directamente el último código QR generado

## Consideraciones Importantes

- Los códigos QR generados se guardan automáticamente en la carpeta "codes" con nombres basados en la habitación o en "manual" para entradas manuales
- El sistema de logs guarda información detallada en la carpeta "logs" con archivos nombrados por fecha y hora
- Para generar QR masivos, utilice el botón "Generar Todos" en la pestaña Excel
- Las credenciales WiFi guardadas en los QR son compatibles con la mayoría de los dispositivos modernos

## Estructura del Proyecto

```
vgQRGen/
├── __main__.py           # Punto de entrada de la aplicación
├── core/
│   ├── excel_manager.py  # Manejo de archivos Excel y extracción de datos
│   └── qr_manager.py     # Generación y personalización de códigos QR
├── gui/
│   └── main_window.py    # Implementación de la interfaz gráfica de usuario
└── utils/
    ├── config_manager.py # Gestión de configuración persistente
    ├── excel_utils.py    # Utilidades para conversión de columnas Excel
    └── logging_utils.py  # Sistema de registro para depuración

/logos/                   # Carpeta con logotipos de propiedades
/codes/                   # Carpeta donde se guardan los códigos QR generados
/logs/                    # Carpeta de archivos de registro
```

## Propiedades Soportadas

- **VLEV/VLE**: Villa Estancia (logo correspondiente)
- **VDPF/VG/VDP**: Villa Group (logo correspondiente)
- **Sin Logo**: Opción para generar QR sin logotipo

## Dependencias

- **openpyxl**: Lectura y procesamiento de archivos Excel
- **Pillow**: Manipulación de imágenes para QR con logos y texto
- **segno**: Generación de códigos QR de alta calidad
- **tqdm**: Barras de progreso para procesamiento por lotes
- **colorama**: Formateo de salidas de texto en consola
- **et_xmlfile**: Dependencia interna de openpyxl

## Solución de Problemas

- Si los logotipos no aparecen, verificar que existan los archivos correspondientes en la carpeta "logos"
  - Ver fichero [Logo_Set.md](Logo_Set.md) para información sobre actualizar los logotipos. 
- Para problemas de detección de columnas en Excel, utilizar la opción "Configurar Columnas Manualmente"
- Revisar los archivos de log en la carpeta "logs" para identificar errores específicos
- Ejecutar la aplicación con la opción `--debug` para obtener información más detallada

## Licencia

Consultar el archivo LICENSE para detalles sobre la licencia del proyecto.
