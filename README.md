# Generador de Códigos QR para WiFi

Una aplicación Python para generar códigos QR para redes WiFi, con soporte para importación de archivos Excel y entrada manual. Esta herramienta está diseñada para facilitar la creación masiva de códigos QR para configuraciones WiFi en propiedades hoteleras.

## Características

- Genera códigos QR para redes WiFi con tipos de encriptación configurables (WPA2, WPA, WEP, sin seguridad)
- Importa datos de red desde archivos Excel con detección automática o manual de columnas
- Guarda y restaura configuración por archivo y hoja de Excel (preferencias, columnas, opciones)
- Agrega logotipos de propiedades a los códigos QR (VLEV, VDPF, etc.)
- Agrega texto de SSID y contraseña debajo de los códigos QR para fácil referencia
- Vista previa de códigos QR antes de guardar (la previsualización es fiel al resultado final)
- Interfaz gráfica intuitiva con pestañas para diferentes modos de operación
- Sistema completo de registro (logs) para facilitar la depuración
- Recuerda últimos archivos y hojas utilizados
- Capacidad para generar QR individuales o por lotes

## Instalación

1. Clona este repositorio:
   ```bash
   git clone <url-del-repo>
   cd vgQrGen
   ```
2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```
   Asegúrate tener Python 3.9+ y pip actualizado.

   Dependencias principales:
   - openpyxl >= 3.1.5
   - Pillow >= 11.2.1
   - segno >= 1.6.6
   - et_xmlfile >= 2.0.0 (requerido por openpyxl)

## Uso

### Iniciar la Aplicación

```bash
python -m vgQRGen [--debug]
```

La opción `--debug` activa el registro detallado para facilitar la solución de problemas.

---

## Flujo para Generar Códigos QR desde Excel

1. **Selecciona la pestaña "Importar Excel" en la interfaz.**
2. **Selecciona el archivo Excel** (puedes elegir de recientes o examinar).
3. **Selecciona la hoja** a procesar. La app recordará la última hoja usada para ese archivo.
4. **(Opcional) Busca una habitación específica** usando el campo de búsqueda.
5. **Genera el QR:**
   - Puedes generar el QR de una habitación seleccionada o de todas (por lote).
   - El QR se previsualiza y se guada en el sistema..
   - Los QR se guardan en la carpeta `codes/` con nombres basados en habitación y propiedad.

### Configuración avanzada para administradores

1. **Desbloquear opciones avanzadas**
   - Click en el ícono del candado en la parte inferior izquierda.
   - Ingresa la contraseña de administrador: "Sierra, uniform, delta, Zero" (Sud0)
2. **Configura las columnas:**
   - La app detecta automáticamente las columnas clave (habitacion, SSID, contraseña, etc.).
   - Si la detección falla, puedes asignarlas manualmente (la configuración se guarda por archivo y hoja).
3. **Configura opciones de seguridad y propiedad:**
   - Puedes usar los valores del Excel o forzar un valor predeterminado (WPA2, VLEV, etc.).
   - La prioridad de los valores lo tiene siempre el fichero Excel, a menos que se desmarquen las casillas de verificación.
   - Las opciones seleccionadas se guardan y restauran automáticamente.



**Notas:**
- Toda la configuración (checkboxes, radios, columnas) se guarda automáticamente por archivo y hoja.
- El QR generado incluye el logo y el texto exactamente como se muestra en la previsualización.
- Si cambias de hoja o archivo, la configuración previa se restaura automáticamente.

---

## Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas (pueden tener nombres variados, la app detecta automáticamente):
- **Número de habitación** (obligatorio): Identificador único como 1101A, 3506B...
- **SSID** (obligatorio): Nombre de la red WiFi
- **Contraseña** (opcional): Para redes protegidas
- **Tipo de encriptación** (opcional): WPA2 (predeterminado), WPA, WEP, o nopass (sin seguridad)
- **Tipo de propiedad** (opcional): Para selección automática de logotipo

La aplicación detecta automáticamente los nombres de columnas basándose en palabras clave comunes en español e inglés. Si la detección automática falla, se puede configurar manualmente las columnas a través de la interfaz de administrador.

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

---

## Estructura del Proyecto

```
vgQRGen/
├── __main__.py           # Punto de entrada de la aplicación
├── core/
│   ├── excel_manager.py  # Manejo de archivos Excel y extracción de datos
│   └── qr_manager.py     # Generación y personalización de códigos QR
├── gui/
│   └── main_window.py    # Interfaz gráfica y lógica de interacción
├── utils/
│   ├── config_manager.py # Gestión robusta de configuración por archivo y hoja
│   ├── excel_utils.py    # Utilidades para conversión y manejo de columnas Excel
│   └── logging_utils.py  # Sistema de registro para depuración
├── logos/                # Carpeta con logotipos de propiedades
├── codes/                # Carpeta donde se guardan los códigos QR generados
├── logs/                 # Carpeta de archivos de registro
├── QR_tamanio_resolucion.md # Documentación para cambiar tamaño y resolución de QR
├── Logo_Set.md           # Documentación sobre logotipos
└── config.json           # Configuración persistente por archivo y hoja
```

---

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

## Compilar la Aplicación

Para generar un ejecutable Windows con PyInstaller:

```bash
pyinstaller vgQRGen.spec
```

El ejecutable se creará en la carpeta `dist/vgQRGen/`. Se incluirán automáticamente todos los archivos necesarios:
- Archivo de configuración
- Logotipos
- Documentación

Para distribuir la aplicación, simplemente comparte la carpeta `dist/vgQRGen` completa.

## Solución de Problemas

- Para editar el tamaño o resolución de los QR, consulta [QR_tamanio_resolucion.md](QR_tamanio_resolucion.md)
- Si los logotipos no aparecen, verifica que existan los archivos correspondientes en la carpeta "logos". Consulta [Logo_Set.md](Logo_Set.md) para información sobre actualizar los logotipos.
- Para problemas de detección de columnas en Excel, utiliza la opción "Configurar Columnas Manualmente" en la interfaz.
- Revisa los archivos de log en la carpeta "logs" para identificar errores específicos.
- Ejecuta la aplicación con la opción `--debug` para obtener información más detallada.


