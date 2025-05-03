"""
Módulo de Ventana Principal para la Aplicación Generadora de QR.

Este módulo implementa la interfaz gráfica de usuario principal para el generador de códigos QR,
proporcionando opciones para generar códigos QR desde archivos Excel o entrada manual.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from typing import Optional, Dict

from ..core.excel_manager import ExcelManager
from ..core.qr_manager import QRManager, WiFiCredentials
from ..utils.logging_utils import LogManager

logger = LogManager.get_logger(__name__)

def excel_column_to_index(column_letter: str) -> int:
    """
    Convertir letra de columna de Excel a índice de columna basado en cero.
    
    Args:
        column_letter (str): Letra de columna (por ejemplo, 'A', 'B', 'AA', etc.)
        
    Returns:
        int: Índice de columna basado en cero
        
    Ejemplos:
        'A' -> 0
        'B' -> 1
        'Z' -> 25
        'AA' -> 26
        'AB' -> 27
    """
    column_letter = column_letter.upper().strip()
    result = 0
    for i, char in enumerate(reversed(column_letter)):
        result += (ord(char) - ord('A') + 1) * (26 ** i)
    return result - 1

def index_to_excel_column(index: int) -> str:
    """
    Convertir índice de columna basado en cero a letra de columna de Excel.
    
    Args:
        index (int): Índice de columna basado en cero
        
    Returns:
        str: Letra de columna (por ejemplo, 'A', 'B', 'AA', etc.)
    """
    index += 1
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result

class SheetSelectionDialog(tk.Toplevel):
    """Diálogo para seleccionar hoja de Excel."""
    
    def __init__(self, parent, sheets: list):
        super().__init__(parent)
        self.title("Seleccionar Hoja")
        self.sheet_name = None
        
        # Centrar diálogo
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Selección de hoja
        ttk.Label(self, text="Seleccione una hoja:").pack(pady=10)
        self.sheet_var = tk.StringVar(value=sheets[0] if sheets else "")
        sheet_combo = ttk.Combobox(self, textvariable=self.sheet_var, values=sheets)
        sheet_combo.pack(pady=5)
        
        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)
        
    def _on_ok(self):
        self.sheet_name = self.sheet_var.get()
        self.destroy()
        
    def _on_cancel(self):
        self.destroy()

class ColumnSelectionDialog(tk.Toplevel):
    """Diálogo para seleccionar columnas de Excel manualmente."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Seleccionar Columnas")
        self.column_indices = None
        
        # Centrar diálogo
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Marco de selección de columnas
        frame = ttk.LabelFrame(self, text="Letras de Columnas", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Texto de ayuda
        help_text = "Ingrese letras de columnas de Excel (A, B, C, etc.)"
        ttk.Label(frame, text=help_text, font=("", 9, "italic")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        # Entradas de columnas
        self.columns = {}
        labels = {
            'room': 'Columna Número de Habitación *',
            'ssid': 'Columna SSID *',
            'password': 'Columna Contraseña',
            'encryption': 'Columna Encriptación',
            'property_type': 'Columna Propiedad'
        }
        
        row = 1
        for key, label in labels.items():
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=5)
            entry.grid(row=row, column=1, sticky=tk.W, pady=2)
            self.columns[key] = var
            row += 1
            
        # Ejemplo
        example_text = "Ejemplo: A para la primera columna, B para la segunda, etc.\nUse AA, AB, etc. para columnas después de Z"
        ttk.Label(frame, text=example_text, font=("", 8)).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )
        
        row += 1
        ttk.Label(frame, text="* Campos requeridos", font=("", 8, "italic")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=10
        )
        
        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)
        
    def _validate_column_letter(self, column: str) -> bool:
        """Validar formato de letra de columna de Excel."""
        if not column:
            return False
        return all(c.isalpha() for c in column.upper())
        
    def _on_ok(self):
        try:
            # Validar campos requeridos
            room = self.columns['room'].get().strip()
            ssid = self.columns['ssid'].get().strip()
            
            if not room or not ssid:
                messagebox.showerror(
                    "Error",
                    "Las columnas de Número de Habitación y SSID son requeridas"
                )
                return
                
            # Validar formato de letra de columna
            for key, var in self.columns.items():
                value = var.get().strip()
                if value and not self._validate_column_letter(value):
                    messagebox.showerror(
                        "Error",
                        f"Formato de letra de columna inválido para {key}: {value}\n"
                        "Por favor use solo letras (A-Z, AA-ZZ, etc.)"
                    )
                    return
            
            # Convertir letras a índices (basado en cero)
            self.column_indices = {
                'room': excel_column_to_index(room),
                'ssid': excel_column_to_index(ssid)
            }
            
            # Agregar columnas opcionales
            for key in ['password', 'encryption', 'property_type']:
                value = self.columns[key].get().strip()
                if value:
                    self.column_indices[key] = excel_column_to_index(value)
                    
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror(
                "Error",
                str(e) or "Formato de letra de columna inválido.\nPor favor use solo letras (A-Z, AA-ZZ, etc.)"
            )
            
    def _on_cancel(self):
        self.destroy()

class MainWindow:
    """Ventana principal para el generador de códigos QR."""
    
    def __init__(self):
        """Inicializar la ventana principal y sus componentes."""
        self.root = tk.Tk()
        self.root.title("Generador de QR de Wifi VillaGroup")
        self.root.geometry("900x500")  # Ventana inicial más grande
        
        # Establecer tamaño mínimo de la ventana
        # El ancho mínimo considera: columna izquierda (300px) + columna derecha con QR (300px) + padding
        # El alto mínimo considera: altura del QR (300px) + espacio para controles y padding
        self.root.minsize(900, 500)
        
        # Inicializar gestores
        self.qr_manager = QRManager()
        self.excel_manager = None
        
        # Configurar componentes de la UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar todos los componentes de la UI."""
        # Crear marco principal para las dos columnas
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,0))  # Ajustado padding vertical
        main_frame.grid_columnconfigure(0, weight=1)  # Columna izquierda expandible
        main_frame.grid_columnconfigure(1, weight=0)  # Columna derecha fija
        
        # Columna izquierda - Controles
        left_column = ttk.Frame(main_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Notebook para pestañas en la columna izquierda
        notebook = ttk.Notebook(left_column)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de Excel
        excel_frame = ttk.Frame(notebook)
        notebook.add(excel_frame, text="Importar Excel")
        self._setup_excel_tab(excel_frame)
        
        # Pestaña de entrada manual
        manual_frame = ttk.Frame(notebook)
        notebook.add(manual_frame, text="Entrada Manual")
        self._setup_manual_tab(manual_frame)
        
        # Columna derecha - Vista previa (ancho y alto fijo)
        right_column = ttk.Frame(main_frame, width=300, height=400)
        right_column.grid(row=0, column=1, sticky="n", padx=(5, 0))
        right_column.grid_propagate(False)  # Evita que el frame cambie de tamaño
        
        # Marco de vista previa con tamaño fijo inicial
        preview_frame = ttk.LabelFrame(right_column, text="Vista Previa QR", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para contener la imagen del QR
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=10)
        
        # Etiqueta para mostrar la configuración del QR
        self.config_label = ttk.Label(
            preview_frame,
            text="",
            justify=tk.LEFT,
            font=("", 8),
            wraplength=280  # Para permitir múltiples líneas si es necesario
        )
        self.config_label.pack(pady=(0, 10), padx=5)
        
        # Crear una imagen en blanco del tamaño deseado para establecer las dimensiones iniciales
        blank_image = Image.new('RGB', (300, 300), 'white')
        photo = ImageTk.PhotoImage(blank_image)
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo
        
        # Botones comunes en la parte inferior de la ventana principal
        self._setup_common_buttons()
        
    def _setup_common_buttons(self):
        """Configurar botones comunes para ambas pestañas."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)  # Cambiado a BOTTOM
        
        ttk.Button(button_frame, text="Abrir Carpeta de Códigos", 
                  command=self._open_codes_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abrir Último QR", 
                  command=self._open_last_qr).pack(side=tk.LEFT)
        
    def _setup_excel_tab(self, parent: ttk.Frame):
        """Configurar la pestaña de importación de Excel."""
        # Selección de archivo
        file_frame = ttk.LabelFrame(parent, text="Archivo Excel", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        file_content_frame = ttk.Frame(file_frame)
        file_content_frame.pack(fill=tk.X, expand=True)
        file_content_frame.grid_columnconfigure(0, weight=1)
        file_content_frame.grid_columnconfigure(1, weight=0)
        
        self.file_path = tk.StringVar()
        ttk.Entry(file_content_frame, textvariable=self.file_path, state="readonly").grid(row=0, column=0, sticky="ew", padx=5)
        ttk.Button(file_content_frame, text="Examinar", command=self._browse_excel).grid(row=0, column=1, padx=5)
        
        # Marco de opciones de Excel
        self.options_frame = ttk.LabelFrame(parent, text="Opciones de Excel", padding=5)
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Selección de hoja
        sheet_frame = ttk.Frame(self.options_frame)
        sheet_frame.pack(fill=tk.X, expand=True)
        sheet_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(sheet_frame, text="Hoja:").grid(row=0, column=0, sticky="w", padx=5)
        self.sheet_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.sheet_var, state="disabled")
        self.sheet_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.load_sheet_btn = ttk.Button(sheet_frame, text="Cargar Hoja", command=self._load_selected_sheet, state="disabled")
        self.load_sheet_btn.grid(row=0, column=2, padx=5)
        
        # Frame para selección de método de seguridad
        security_frame = ttk.Frame(self.options_frame)
        security_frame.pack(fill=tk.X, expand=True, pady=10)
        
        ttk.Label(security_frame, text="Método de Seguridad por Defecto:").pack(side=tk.LEFT, padx=5)
        
        # Variable y radio buttons para método de seguridad (siempre activos)
        self.security_var = tk.StringVar(value="WPA2")
        self.security_radios = []
        
        radio_frame = ttk.Frame(security_frame)
        radio_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        for security in ["WPA2", "WPA", "WEP", "nopass"]:
            radio = ttk.Radiobutton(
                radio_frame,
                text=security,
                variable=self.security_var,
                value=security
            )
            radio.pack(side=tk.LEFT, padx=10)
            self.security_radios.append(radio)
            
        # Etiqueta informativa de prioridad de seguridad
        self.security_priority_label = ttk.Label(
            self.options_frame,
            text="La prioridad en el método de seguridad la tiene el fichero cargado.",
            foreground="gray",
            font=("", 8, "italic")
        )
        self.security_priority_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        # Inicialmente ocultar la etiqueta
        self.security_priority_label.pack_forget()
        
        # Botón de selección manual de columnas
        self.manual_cols_btn = ttk.Button(
            self.options_frame,
            text="Configurar Columnas Manualmente",
            command=self._show_column_dialog,
            state="disabled"
        )
        self.manual_cols_btn.pack(pady=5)
        
        # Marco de búsqueda de habitación
        self.search_frame = ttk.LabelFrame(parent, text="Buscar Habitación", padding=5)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_content_frame = ttk.Frame(self.search_frame)
        search_content_frame.pack(fill=tk.X, expand=True)
        search_content_frame.grid_columnconfigure(0, weight=1)
        
        self.room_number = tk.StringVar()
        self.room_entry = ttk.Entry(search_content_frame, textvariable=self.room_number, state="disabled")
        self.room_entry.grid(row=0, column=0, sticky="ew", padx=5)
        
        button_frame = ttk.Frame(search_content_frame)
        button_frame.grid(row=0, column=1, sticky="e")
        
        self.generate_btn = ttk.Button(button_frame, text="Generar QR", 
                                     command=self._generate_room_qr, state="disabled")
        self.generate_btn.pack(side=tk.LEFT)
        
        self.generate_all_btn = ttk.Button(button_frame, text="Generar Todos", 
                                         command=self._generate_all_qr, state="disabled")
        self.generate_all_btn.pack(side=tk.LEFT, padx=5)
        
    def _browse_excel(self):
        """Abrir diálogo de archivo para seleccionar archivo Excel."""
        filename = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")]
        )
        if not filename:
            return
            
        self.file_path.set(filename)
        self.excel_manager = ExcelManager(filename)
        
        # Intentar cargar el libro
        success, error_msg = self.excel_manager.load_workbook()
        if not success:
            messagebox.showerror("Error", error_msg)
            self._reset_excel_ui()
            return
            
        # Habilitar y llenar selección de hoja
        sheets = self.excel_manager.get_sheet_names()
        self.sheet_combo['values'] = sheets
        self.sheet_combo.set(sheets[0] if sheets else "")
        self._enable_sheet_selection()
            
    def _enable_sheet_selection(self):
        """Habilitar controles de selección de hoja."""
        self.sheet_combo['state'] = 'readonly'
        self.load_sheet_btn['state'] = 'normal'
        
    def _load_selected_sheet(self):
        """Cargar la hoja seleccionada e intentar detectar columnas."""
        if not self.excel_manager:
            return
            
        sheet_name = self.sheet_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Por favor seleccione una hoja primero")
            return
            
        success, error_msg = self.excel_manager.set_active_sheet(sheet_name)
        if not success:
            messagebox.showerror("Error", error_msg)
            if "columnas" in error_msg.lower():
                self._enable_manual_column_selection()
            return
            
        # Habilitar controles de búsqueda de habitación
        self._enable_room_search()
        
        # Resetear a WPA2 por defecto al cargar una nueva hoja
        self.security_var.set("WPA2")
        
        # Mostrar etiqueta de prioridad si hay columna de seguridad
        if self.excel_manager.columns.encryption is not None:
            self.security_priority_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        else:
            self.security_priority_label.pack_forget()
            
    def _update_security_radio_state(self):
        """Actualizar seguridad por defecto al cargar una hoja."""
        # Reiniciar a WPA2 por defecto al cargar una nueva hoja
        self.security_var.set("WPA2")

    def _enable_manual_column_selection(self):
        """Habilitar selección manual de columnas."""
        self.manual_cols_btn['state'] = 'normal'
        
    def _enable_room_search(self):
        """Habilitar controles de búsqueda de habitación."""
        self.room_entry['state'] = 'normal'
        self.generate_btn['state'] = 'normal'
        self.generate_all_btn['state'] = 'normal'
        self.manual_cols_btn['state'] = 'normal'
        
    def _reset_excel_ui(self):
        """Restablecer controles de UI de Excel al estado inicial."""
        self.file_path.set("")
        self.sheet_combo.set("")
        self.sheet_combo['values'] = []
        self.sheet_combo['state'] = 'disabled'
        self.load_sheet_btn['state'] = 'disabled'
        self.manual_cols_btn['state'] = 'disabled'
        self.room_entry['state'] = 'disabled'
        self.generate_btn['state'] = 'disabled'
        self.generate_all_btn['state'] = 'disabled'
        self.room_number.set("")
        
    def _show_column_dialog(self):
        """Mostrar diálogo para selección manual de columnas."""
        dialog = ColumnSelectionDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.column_indices:
            if self.excel_manager.set_columns_manually(dialog.column_indices):
                messagebox.showinfo("Éxito", "Columnas configuradas exitosamente")
                self._enable_room_search()
                
                # Mostrar etiqueta de prioridad si se configuró columna de encryption
                if 'encryption' in dialog.column_indices:
                    self.security_priority_label.pack(fill=tk.X, padx=5, pady=(0, 5))
                else:
                    self.security_priority_label.pack_forget()
            else:
                messagebox.showerror("Error", "Error al configurar columnas")
                
    def _setup_manual_tab(self, parent: ttk.Frame):
        """Configurar la pestaña de entrada manual."""
        input_frame = ttk.LabelFrame(parent, text="Detalles de Red", padding=5)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # SSID
        ttk.Label(input_frame, text="SSID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_ssid = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.manual_ssid, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        # Contraseña
        ttk.Label(input_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_password = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.manual_password, width=30).grid(row=1, column=1, padx=5, pady=2)
        
        # Encriptación
        ttk.Label(input_frame, text="Encriptación:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_encryption = tk.StringVar(value="WPA2")
        ttk.Combobox(input_frame, textvariable=self.manual_encryption, 
                    values=["WPA", "WPA2", "WEP", "nopass"], 
                    state="readonly").grid(row=2, column=1, padx=5, pady=2)
        
        # Propiedad
        ttk.Label(input_frame, text="Propiedad:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_property = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.manual_property,
                    values=["VLE", "VDPF"],
                    state="readonly").grid(row=3, column=1, padx=5, pady=2)
        
        # Botón de generar
        ttk.Button(input_frame, text="Generar QR", 
                  command=self._generate_manual_qr).grid(row=4, column=0, columnspan=2, pady=10)
                  
    def _generate_room_qr(self):
        """Generar código QR para una habitación específica desde Excel."""
        if not self.excel_manager:
            messagebox.showerror("Error", "Por favor seleccione un archivo Excel primero")
            return
            
        room = self.room_number.get().strip()
        if not room:
            messagebox.showerror("Error", "Por favor ingrese un número de habitación")
            return
            
        try:
            credentials = self.excel_manager.get_room_data(room)
            if not credentials:
                messagebox.showerror("Error", f"Habitación {room} no encontrada o datos faltantes")
                return

            # Solo usar el valor de los radio buttons si no hay valor de encriptación en el Excel
            if credentials.encryption is None:
                credentials.encryption = self.security_var.get()

            self._generate_and_preview_qr(credentials)
        except Exception as e:
            logger.error(f"Error generando QR para la habitación {room}: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _generate_all_qr(self):
        """Generar códigos QR para todas las habitaciones en Excel."""
        if not self.excel_manager:
            messagebox.showerror("Error", "Por favor seleccione un archivo Excel primero")
            return
            
        try:
            credentials_list = self.excel_manager.get_all_rooms()
            if not credentials_list:
                messagebox.showinfo("Info", "No se encontraron habitaciones válidas en el archivo Excel")
                return
                
            # Procesar cada habitación individualmente
            selected_security = self.security_var.get()
            for cred in credentials_list:
                # Solo usar el valor seleccionado si no hay valor de encriptación en el Excel
                if cred.encryption is None:
                    cred.encryption = selected_security
                    
                self._generate_and_preview_qr(cred, show_preview=False)
                
            messagebox.showinfo("Éxito", 
                              f"Generados {len(credentials_list)} códigos QR en la carpeta de códigos")
        except Exception as e:
            logger.error(f"Error generando todos los QRs: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _generate_manual_qr(self):
        """Generar código QR desde entrada manual."""
        ssid = self.manual_ssid.get().strip()
        if not ssid:
            messagebox.showerror("Error", "El SSID es requerido")
            return
            
        credentials = WiFiCredentials(
            ssid=ssid,
            password=self.manual_password.get().strip(),
            encryption=self.manual_encryption.get(),
            property_type=self.manual_property.get()
        )
        
        self._generate_and_preview_qr(credentials)
        
    def _generate_and_preview_qr(self, credentials: WiFiCredentials, show_preview: bool = True):
        """Generar código QR y actualizar vista previa."""
        try:
            buffer = self.qr_manager.generate_wifi_qr(credentials)
            
            if credentials.property_type:
                buffer = self.qr_manager.add_logo(buffer, credentials.property_type)
                
            # Agregar texto de SSID y contraseña
            buffer = self.qr_manager.add_text(buffer, credentials.ssid, credentials.password or "")
            
            # Guardar QR
            self.last_qr_path = self.qr_manager.save_qr(buffer, f"qr_{credentials.ssid}")
            
            # Actualizar vista previa si es necesario
            if show_preview:
                self._update_preview(buffer)
                # Actualizar etiqueta de configuración
                config_text = f"SSID: {credentials.ssid}\n"
                if credentials.password:
                    config_text += f"Contraseña: {credentials.password}\n"
                config_text += f"Seguridad: {credentials.encryption}\n"
                if credentials.property_type:
                    config_text += f"Propiedad: {credentials.property_type}"
                self.config_label.configure(text=config_text)
                
        except Exception as e:
            logger.error(f"Error generando QR: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _update_preview(self, buffer):
        """Actualizar vista previa de QR en la UI."""
        try:
            image = Image.open(buffer)
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            
            # Actualizar vista previa en la pestaña actual
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
                    
        except Exception as e:
            logger.error(f"Error actualizando vista previa: {str(e)}")
            
    def _open_codes_folder(self):
        """Abrir la carpeta de códigos en el explorador de archivos del sistema."""
        try:
            os.startfile(self.qr_manager.output_dir)
        except Exception as e:
            logger.error(f"Error abriendo carpeta de códigos: {str(e)}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de códigos: {str(e)}")
            
    def _open_last_qr(self):
        """Abrir el último código QR generado."""
        if hasattr(self, 'last_qr_path') and os.path.exists(self.last_qr_path):
            try:
                os.startfile(self.last_qr_path)
            except Exception as e:
                logger.error(f"Error abriendo último QR: {str(e)}")
                messagebox.showerror("Error", f"No se pudo abrir el QR: {str(e)}")
        else:
            messagebox.showinfo("Info", "No se ha generado ningún código QR aún")
            
    def run(self):
        """Iniciar el bucle principal de la aplicación."""
        self.root.mainloop()