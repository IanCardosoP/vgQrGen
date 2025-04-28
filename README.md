# Generador de Códigos QR para WiFi

Una aplicación Python para generar códigos QR para redes WiFi, con soporte para importación de archivos Excel y entrada manual.

## Características

- Genera códigos QR para redes WiFi con tipos de encriptación configurables
- Importa datos de red desde archivos Excel
- Agrega logotipos de propiedades a los códigos QR (VLEV, VDPF, etc.)
- Agrega texto de SSID y contraseña debajo de los códigos QR
- Vista previa de códigos QR antes de guardar
- Interfaz gráfica con pestañas de importación Excel y entrada manual

## Instalación

1. Clonar este repositorio
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Iniciar la Aplicación

```bash
python -m vgQRGen [--debug]
```

### Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas (los nombres de columnas son flexibles y se detectarán automáticamente):
- Número de habitación (ej., 1101A, 3506B)
- SSID
- Contraseña (opcional para redes abiertas)
- Tipo de encriptación (opcional, por defecto WPA2)
- Tipo de propiedad (opcional, para selección de logotipo)

### Características de la Interfaz Gráfica

#### Pestaña de Importación Excel
- Seleccionar archivo Excel
- Buscar números de habitación específicos
- Generar QR para una habitación o todas las habitaciones
- Vista previa de códigos QR generados

#### Pestaña de Entrada Manual
- Ingresar detalles de red manualmente
- Seleccionar tipo de encriptación y propiedad
- Vista previa y guardar códigos QR

### Características Comunes
- Abrir carpeta de códigos
- Ver último QR generado
- Vista previa de QR antes de guardar

## Estructura del Proyecto

```
vgQRGen/
├── __main__.py           # Punto de entrada de la aplicación
├── core/
│   ├── excel_manager.py  # Manejo de archivos Excel
│   └── qr_manager.py     # Generación de códigos QR
├── gui/
│   └── main_window.py    # Implementación de la interfaz gráfica
└── utils/
    └── logging_utils.py  # Configuración de registro
```

## Propiedades Soportadas

- VLEV/VLE (Villa Estancia)
- VDPF/VG/VDP (Villa Group)

## Dependencias

- openpyxl: Manejo de archivos Excel
- Pillow: Procesamiento de imágenes
- segno: Generación de códigos QR
- tqdm: Barras de progreso para procesamiento por lotes
