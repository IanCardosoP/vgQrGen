import argparse
import sys
import segno
import os
import openpyxl
from io import BytesIO
from typing import Optional, Tuple
import tqdm
from PIL import Image, ImageDraw, ImageFont
from segno import helpers

# Configuración global
DEFAULT_SOURCE_FILE = "source.xlsx"
# DEFAULT_SOURCE_FILE = r"C:\Users\Ian Cardoso\OneDrive - Villagroup\VPFL & VLE - Documents\Sistemas - Sistemas FLM\Informacion de hotel\VLE\mapeo actualizado  del 2024.xlsx"
DEFAULT_SHEET_NAME = "ANTENAS ARUBA ESTANCIA 2025"
DEFAULT_SECURITY = "WPA2"


def main():
    # Configuración de argumentos
    parser = argparse.ArgumentParser(
        description="Script generador de QR para Wifi. Usa un único parámetro para ejecutar diferentes funcionalidades."
    )
    parser.add_argument(
        "habitacion", nargs="?", type=str,
        help="Especifica la habitación, ejemplo: 1102A."
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Generar para todas las habitaciones disponibles."
    )
    parser.add_argument(
        "--new", action="store_true",
        help="Formulario para crear una nueva habitación."
    )

    args = parser.parse_args()
    argumentos = sum([bool(args.habitacion), args.all, args.new])

    if argumentos > 1:
        print("Error: Solo puedes usar un argumento a la vez.")
        return 1

    try:
        if args.habitacion:
            print(f"Buscando habitación {args.habitacion}...")
            wb, sheet = load_source_file()
            if not sheet:
                return 1
                
            ssid, password = search_for_room(args.habitacion, sheet)
            if ssid and password:
                output_path = generar_qr(ssid, password, DEFAULT_SECURITY)
                print(f"Código QR generado exitosamente: {output_path}")
            else:
                return 1
                
        elif args.all:
            print("Iterando hoja y generando para todas las habitaciones...")
            wb, sheet = load_source_file()
            if sheet:
                generar_todo(sheet, DEFAULT_SECURITY)
                
        elif args.new:
            print("Generando QR para nueva red.")
            ssid = leer_ssid()
            security = leer_seguridad()
            password = leer_pass()
            output_path = generar_qr(ssid, password, security)
            print(f"Código QR generado exitosamente: {output_path}")
            
        else:
            mostrar_ayuda()
            
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return 1
        
    return 0

def mostrar_ayuda():
    print("Uso:")
    print("  python vgQrGen.py [habitacion] | --all | --new")
    print("Ejemplos:")
    print("  python vgQrGen.py 1102A       # Buscar y generar para habitación específica")
    print("  python vgQrGen.py --all       # Generar QR para todas las habitaciones")
    print("  python vgQrGen.py --new       # Generar QR para nueva habitación")
    print("\nUsa --help para más información.")
        
def load_source_file(
    file_path: str = DEFAULT_SOURCE_FILE, 
    sheet_name: str = DEFAULT_SHEET_NAME,
    data_only: bool = True
) -> Tuple[Optional[openpyxl.Workbook], Optional[openpyxl.worksheet.worksheet.Worksheet]]:
    """
    Carga un archivo Excel y devuelve el workbook y la hoja especificada.
    
    Args:
        file_path (str): Ruta del archivo Excel. Por defecto usa DEFAULT_SOURCE_FILE.
        sheet_name (str): Nombre de la hoja a cargar. Por defecto usa DEFAULT_SHEET_NAME.
        data_only (bool): Si True, carga solo valores (no fórmulas). Por defecto True.   
    Returns:
        tuple: (Workbook, Worksheet) o (None, None) si hay error.
    
    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si la hoja no existe en el workbook.
    """
    try:
        # Validación básica de parámetros
        if not file_path or not isinstance(file_path, str):
            raise ValueError("La ruta del archivo debe ser una cadena no vacía")
            
        if not sheet_name or not isinstance(sheet_name, str):
            raise ValueError("El nombre de la hoja debe ser una cadena no vacía")

        # Cargar workbook
        wb = openpyxl.load_workbook(file_path, data_only=data_only)
        
        # Verificar que la hoja existe
        if sheet_name not in wb.sheetnames:
            available_sheets = ", ".join(wb.sheetnames)
            raise ValueError(
                f"Hoja '{sheet_name}' no encontrada. Hojas disponibles: {available_sheets}"
            )
        
        sheet = wb[sheet_name]
        return wb, sheet
        
    except FileNotFoundError as fnf_error:
        print(f"Error: Archivo no encontrado - {fnf_error}")
        return None, None
    except ValueError as val_error:
        print(f"Error de valor: {val_error}")
        return None, None
    except openpyxl.utils.exceptions.InvalidFileException as file_error:
        print(f"Error: Archivo Excel inválido - {file_error}")
        return None, None
    except Exception as e:
        print(f"Error inesperado al cargar el archivo: {str(e)}")
        return None, None

def search_for_room(habitacion, sheet):
    """Busca los datos WiFi para una habitación en el Excel.
    
    Args:
        habitacion (str): Nombre/número de la habitación a buscar
        
    Returns:
        tuple: (ssid, password) o (None, None) si no se encuentra
    """
    if not habitacion or not isinstance(habitacion, str):
        print("Error: El parámetro habitación debe ser una cadena no vacía")
        return None, None

    try:
        for fila in sheet.iter_rows(min_row=2, max_row=sheet.max_row, 
                                 min_col=1, max_col=15, values_only=True):
            if str(fila[0]).strip().upper() == str(habitacion).strip().upper():
                password = fila[11]  # Columna L
                ssid = fila[14]     # Columna O
                
                # Validar que los valores no estén vacíos
                if ssid and password:
                    return str(ssid).strip(), str(password).strip()
                
        print(f"No se encontró la habitación '{habitacion}' o faltan datos")
        return None, None

    except Exception as e:
        print(f"Error al buscar en el archivo Excel: {str(e)}")
        return None, None
   
def generar_qr(ssid, password, security):
    """
    Genera un código QR para conexión WiFi con el SSID y password debajo
    
    Args:
        ssid (str): Nombre de la red WiFi
        password (str): Contraseña de la red
        security (str): Tipo de seguridad (WEP, WPA, WPA2, nopass)
        
    Returns:
        str: Ruta del archivo generado
        
    Raises:
        ValueError: Si los parámetros no son válidos
        Exception: Si hay error al generar la imagen
    """
    # Validar parámetros
    if not ssid or not isinstance(ssid, str):
        raise ValueError("SSID debe ser una cadena no vacía")
    
    if security not in ('WEP', 'WPA', 'WPA2', 'nopass'):
        raise ValueError("Seguridad debe ser WEP, WPA, WPA2 o nopass")
    
    if security != 'nopass' and (not password or not isinstance(password, str)):
        raise ValueError("Password es requerido para redes seguras")
    
    try:
        # Crear configuración WiFi
        wifi_config = helpers.make_wifi(
            ssid=ssid, 
            password=password if security != 'nopass' else None, 
            security=security
        )
        
        # Crear directorio si no existe
        os.makedirs("codes", exist_ok=True)
        
        # Generar QR y guardarlo en un buffer
        buffer = BytesIO()
        wifi_config.save(buffer, kind='png', scale=10)
        buffer.seek(0)
        
        # Cargar el QR como imagen PIL
        img_qr = Image.open(buffer)
        width, height = img_qr.size
        
        # Crear nueva imagen con espacio para texto
        text_height = 60  # Altura para el texto
        new_img = Image.new('RGB', (width, height + text_height), 'white')
        new_img.paste(img_qr, (0, 0))
        
        # Configurar texto
        draw = ImageDraw.Draw(new_img)
        try:
            # Intentar usar fuente calibri o similar
            font_path = "calibrib.ttf"  # 'calibri.ttf' es la versión en negrita de calibri
            font = ImageFont.truetype(font_path, 22)
        except:
            # Usar fuente por defecto si no se encuentra la especificada
            font = ImageFont.load_default()
        
        # Texto a mostrar
        texto_superior = f"SSID: {ssid}"
        texto_inferior = f"Contraseña: {password}" if security != 'nopass' else "Red abierta (sin contraseña)"
        
        # Calcular posiciones centradas
        text_width = draw.textlength(texto_superior, font=font)
        x_pos = (width - text_width) / 2
        y_pos = height - 20 
        draw.text((x_pos, y_pos), texto_superior, font=font, fill="black")
        
        text_width = draw.textlength(texto_inferior, font=font)
        x_pos = (width - text_width) / 2
        y_pos = height + 5
        draw.text((x_pos, y_pos), texto_inferior, font=font, fill="black")
        
        # Guardar imagen final
        output_path = f"codes/{ssid}.png"
        new_img.save(output_path)
        
        return output_path
        
    except Exception as e:
        print(f"Error al generar código QR: {e}")
        raise

def cerrar():
    sys.exit(0)
      
def generar_todo(hoja, security: str = DEFAULT_SECURITY, col_room: int = 0, 
                col_password: int = 11, col_ssid: int = 14) -> None:
    """Genera códigos QR para todas las habitaciones en una hoja Excel.
    
    Args:
        hoja: Objeto de hoja Excel (openpyxl)
        security: Tipo de seguridad WiFi (WPA/WEP/nopass)
        col_room: Índice columna habitación (0-based)
        col_password: Índice columna contraseña (0-based)
        col_ssid: Índice columna SSID (0-based)
        
    Raises:
        ValueError: Si no hay datos válidos o parámetros incorrectos
    """
    # Validación de parámetros
    if not hoja:
        raise ValueError("El objeto hoja no puede ser None")
    
    if security not in ("WPA", "WEP", "WPA2", "nopass"):
        raise ValueError("Security debe ser WPA, WEP o nopass")
    
    # Obtener filas válidas (no None y con SSID)
    try:
        filas_validas = [
            fila for fila in hoja.iter_rows(min_row=2, values_only=True)
            if fila[col_room] is not None and fila[col_ssid] is not None
        ]
    except Exception as e:
        raise RuntimeError(f"Error al leer datos del Excel: {str(e)}") from e
    
    if not filas_validas:
        print("Advertencia: No se encontraron filas válidas para procesar")
        return

    # Procesamiento con barra de progreso
    errores = 0
    with tqdm.tqdm(filas_validas, desc="Generando QR WiFi", unit="habitación") as barra:
        for fila in barra:
            try:
                room = str(fila[col_room]).strip()
                ssid = str(fila[col_ssid]).strip()
                password = str(fila[col_password]).strip() if fila[col_password] else None
                
                # Validar datos mínimos
                if not ssid:
                    barra.write(f"Advertencia: SSID vacío para habitación {room}")
                    continue
                    
                if security != "nopass" and not password:
                    barra.write(f"Advertencia: Contraseña vacía para {ssid} (habitación {room})")
                    continue
                
                # Generar QR
                generar_qr(ssid=ssid, password=password, security=security)
                barra.set_postfix(habitación=room, estado="OK")
                
            except Exception as e:
                errores += 1
                barra.write(f"Error procesando {room if 'room' in locals() else 'fila'}: {str(e)}")
                barra.set_postfix(habitación=room, estado="ERROR")
                continue
    
    # Resumen final
    print(f"\nProceso completado. Habitaciones procesadas: {len(filas_validas)-errores}, Errores: {errores}")

def leer_ssid() -> str:
    """Solicita y retorna el SSID"""
    ssid = input("Introduce el SSID: ").strip()
    while not ssid:
        print("El SSID no puede estar vacío")
        ssid = input("Introduce el SSID: ").strip()
    return ssid

def leer_seguridad() -> str:
    """Solicita y retorna el tipo de seguridad"""
    security = input("Introduce el tipo de seguridad (WPA/WPA2/WEP/nopass) [WPA2]: ").strip() or "WPA2"
    while security not in ("WPA", "WPA2", "WEP", "nopass"):
        print("Tipo de seguridad no válido")
        security = input("Introduce el tipo de seguridad (WPA/WPA2/WEP/nopass) [WPA2]: ").strip() or "WPA2"
    return security

def leer_pass() -> str:
    """Solicita y retorna la contraseña"""
    return input("Introduce la contraseña: ").strip()

if __name__ == "__main__":
    sys.exit(main())