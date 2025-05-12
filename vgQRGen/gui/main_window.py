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
import subprocess
import sys

from ..core.excel_manager import ExcelManager
from ..core.qr_manager import QRManager, WiFiCredentials
from ..utils.logging_utils import LogManager
from ..utils.config_manager import ConfigManager
from ..utils.excel_utils import excel_column_to_index, index_to_excel_column

logger = LogManager.get_logger(__name__)

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
    
    def __init__(self, parent, initial_columns=None):
        super().__init__(parent)
        self.title("Seleccionar Columnas")
        self.column_indices = None
        self.initial_columns = initial_columns or {}
        
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
            initial_value = ""
            # Si tenemos un valor inicial para esta columna, convertirlo a letra de Excel
            if key in self.initial_columns and self.initial_columns[key] is not None:
                initial_value = index_to_excel_column(self.initial_columns[key])
            var = tk.StringVar(value=initial_value)
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

class PasswordDialog(tk.Toplevel):
    """Diálogo para ingresar contraseña de administrador."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Autenticación")
        self.success = False
        
        # Centrar diálogo
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Centrar el diálogo respecto a la ventana principal
        self.update_idletasks()  # Actualizar para obtener dimensiones reales
        width = self.winfo_width()
        height = self.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mensaje
        ttk.Label(
            main_frame, 
            text="Ingrese la contraseña de administrador\npara modificar configuraciones avanzadas:",
            justify=tk.CENTER
        ).pack(pady=10)
        
        # Entrada de contraseña
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*")
        password_entry.pack(fill=tk.X, pady=5)
        password_entry.focus_set()  # Establecer foco en la entrada
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Aceptar", command=self._on_accept).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)
        
        # Vincular Enter para aceptar
        self.bind("<Return>", lambda e: self._on_accept())
        
    def _on_accept(self):
        if self.password_var.get() == "Sud0":
            self.success = True
            self.destroy()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")
            self.password_var.set("")
            
    def _on_cancel(self):
        self.destroy()

class MainWindow:
    """Ventana principal para el generador de códigos QR."""
    
    def __init__(self):
        """Inicializar la ventana principal y sus componentes."""
        # Obtener logger para esta clase
        self.logger = LogManager.get_logger(__name__)
        self.logger.info("Inicializando ventana principal")
        
        self.root = tk.Tk()
        self.root.title("Generador de QR Wifi VillaGroup")
        self.root.geometry("950x500")  # Ventana inicial más grande (incrementada en 35px)
        
        # Establecer tamaño mínimo de la ventana
        # El ancho mínimo considera: columna izquierda (300px) + columna derecha con QR (300px) + padding
        # El alto mínimo considera: altura del QR (300px) + espacio para controles y padding
        self.root.minsize(935, 500)
        
        # Crear estilo para los switches
        self._setup_styles()
        
        # Variable para controlar si se ha desbloqueado la configuración avanzada
        self.admin_unlocked = False
        
        # Inicializar gestores
        try:
            self.qr_manager = QRManager()
            self.excel_manager = None
            self.config_manager = ConfigManager()
            self.logger.debug("Gestores inicializados correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar gestores: {str(e)}")
            messagebox.showerror("Error de inicialización", f"Error al inicializar componentes: {str(e)}")
        
        # Variables para los toggles de seguridad y propiedad
        self.use_excel_security = tk.BooleanVar(value=True)
        self.use_excel_property = tk.BooleanVar(value=True)
        self.logger.debug(f"Variables de toggles inicializadas: security={self.use_excel_security.get()}, property={self.use_excel_property.get()}")
        
        # Configurar componentes de la UI
        self._setup_ui()
        
        # Cargar último archivo si existe
        self._load_last_file()
        
        # Asegurar que las opciones de Excel estén deshabilitadas por defecto
        self._toggle_admin_controls(False)
        
        self.logger.info("Ventana principal inicializada correctamente")
        
    def _setup_styles(self):
        """Configurar estilos personalizados para la UI."""
        style = ttk.Style()
        
        # Estilo para los switches (checkbuttons con aspecto de interruptor)
        # Usamos un checkbutton pero le damos aspecto de interruptor con colores
        style.configure("Switch.TCheckbutton", 
                        indicatorsize=20,  # Tamaño del indicador
                        padding=5,
                        background="#f0f0f0")  # Padding alrededor del switch

    def _load_last_file(self):
        """Cargar el último archivo Excel usado."""
        recent_files = self.config_manager.get_recent_files()
        if recent_files:
            last_file = recent_files[0]
            self._load_excel_file(last_file["path"])

    def _load_excel_file(self, filename: str):
        """Cargar un archivo Excel específico."""
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
        
        # Intentar seleccionar última hoja usada
        last_sheet = self.config_manager.get_last_sheet(filename)
        if last_sheet and last_sheet in sheets:
            self.sheet_combo.set(last_sheet)
        else:
            self.sheet_combo.set(sheets[0] if sheets else "")
            
        self._enable_sheet_selection()
        
        # Actualizar lista de archivos recientes inmediatamente
        self._update_recent_files_list()

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
        self.excel_frame = excel_frame  # Guardar referencia para el método _toggle_admin_controls
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
        
        # Botón de candado en la esquina inferior derecha
        self.lock_button = ttk.Button(button_frame, text="🔒", width=3, 
                            command=self._toggle_admin_mode)
        self.lock_button.pack(side=tk.RIGHT, padx=5)
        
    def _setup_excel_tab(self, parent: ttk.Frame):
        """Configurar la pestaña de importación de Excel."""
        # Selección de archivo
        file_frame = ttk.LabelFrame(parent, text="Archivo Excel", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        file_content_frame = ttk.Frame(file_frame)
        file_content_frame.pack(fill=tk.X, expand=True)
        file_content_frame.grid_columnconfigure(1, weight=1)  # La columna del combobox se expande
        file_content_frame.grid_columnconfigure(2, weight=0)  # La columna del botón no se expande
        
        # Etiqueta "Libro:" + combobox + botón "Examinar"
        ttk.Label(file_content_frame, text="Libro:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.file_path = tk.StringVar()
        self.file_combo = ttk.Combobox(
            file_content_frame, 
            textvariable=self.file_path, 
            state="readonly"
        )
        self.file_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.file_combo.bind('<<ComboboxSelected>>', self._on_file_selected)
        
        # Actualizar valores del Combobox con archivos recientes
        self._update_recent_files_list()
        
        ttk.Button(file_content_frame, text="Examinar", command=self._browse_new_excel).grid(row=0, column=2, padx=5)

        # Selección de hoja
        sheet_frame = ttk.Frame(file_frame)
        sheet_frame.pack(fill=tk.X, expand=True, pady=5)
        sheet_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(sheet_frame, text="Hoja:").grid(row=0, column=0, sticky="w", padx=5)
        self.sheet_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.sheet_var, state="disabled")
        self.sheet_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.load_sheet_btn = ttk.Button(sheet_frame, text="Cargar Hoja", command=self._load_selected_sheet, state="disabled")
        self.load_sheet_btn.grid(row=0, column=2, padx=5)

        # Marco de opciones de Excel
        self.options_frame = ttk.LabelFrame(parent, text="Opciones de Excel", padding=5)
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Frame para opciones de seguridad y propiedad
        options_container = ttk.Frame(self.options_frame)
        options_container.pack(fill=tk.X, expand=True, pady=10)

        # Frame para selección de método de seguridad con toggle switch
        security_frame = ttk.Frame(options_container)
        security_frame.pack(fill=tk.X, expand=True, pady=(0,10))
        
        # Frame para el switch de seguridad
        security_switch_frame = ttk.Frame(security_frame)
        security_switch_frame.pack(fill=tk.X, expand=True, side=tk.TOP, pady=(0,5))
        
        # Switch para usar seguridad del Excel
        ttk.Label(security_switch_frame, text="Obtener el Tipo de Seguridad de Excel:").pack(side=tk.LEFT, padx=5)
        security_switch = ttk.Checkbutton(
            security_switch_frame,
            variable=self.use_excel_security,
            text="",
            style="Switch.TCheckbutton",
            command=self._update_security_switch_state
        )
        security_switch.pack(side=tk.LEFT, padx=5)
        
        # Etiqueta que cambia según el estado del switch
        self.security_switch_label = ttk.Label(
            security_switch_frame,
            text="ON - Los valores de seguridad en Excel, tienen preferencia.",
            font=("", 8, "italic"),
            foreground="green"
        )
        self.security_switch_label.pack(side=tk.LEFT, padx=5)
        
        # Frame para los radio buttons de seguridad
        security_radios_frame = ttk.Frame(security_frame)
        security_radios_frame.pack(fill=tk.X, expand=True, side=tk.TOP)
        
        ttk.Label(security_radios_frame, text="Tipo de Seguridad por Defecto:").pack(side=tk.LEFT, padx=5)
        
        # Variable y radio buttons para método de seguridad
        self.security_var = tk.StringVar(value="WPA2")
        # Añadir trace a la variable para guardar configuración al cambiar
        self.security_var.trace_add("write", lambda *args: self._save_sheet_config())
        self.security_radios = []
        
        radio_frame = ttk.Frame(security_radios_frame)
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
            
        # Frame para selección de propiedad con toggle switch
        property_frame = ttk.Frame(options_container)
        property_frame.pack(fill=tk.X, expand=True)
        
        # Frame para el switch de propiedad
        property_switch_frame = ttk.Frame(property_frame)
        property_switch_frame.pack(fill=tk.X, expand=True, side=tk.TOP, pady=(0,5))
        
        # Switch para usar propiedad del Excel
        ttk.Label(property_switch_frame, text="Obtener la Propiedad desde el Excel:").pack(side=tk.LEFT, padx=5)
        property_switch = ttk.Checkbutton(
            property_switch_frame,
            variable=self.use_excel_property,
            text="",
            style="Switch.TCheckbutton",
            command=self._update_property_switch_state
        )
        property_switch.pack(side=tk.LEFT, padx=5)
        
        # Etiqueta que cambia según el estado del switch
        self.property_switch_label = ttk.Label(
            property_switch_frame,
            text="ON - Los valores de propiedad en Excel, tienen preferencia.",
            font=("", 8, "italic"),
            foreground="green"
        )
        self.property_switch_label.pack(side=tk.LEFT, padx=5)
        
        # Frame para los radio buttons de propiedad
        property_radios_frame = ttk.Frame(property_frame)
        property_radios_frame.pack(fill=tk.X, expand=True, side=tk.TOP)
        
        ttk.Label(property_radios_frame, text="Propiedad por Defecto:").pack(side=tk.LEFT, padx=5)
        
        # Variable y radio buttons para propiedad
        self.property_var = tk.StringVar(value="VDPF")
        # Añadir trace a la variable para guardar configuración al cambiar
        self.property_var.trace_add("write", lambda *args: self._save_sheet_config())
        self.property_radios = []
        
        property_radio_frame = ttk.Frame(property_radios_frame)
        property_radio_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        for property_type in ["VLE", "VDPF", "Sin Logo"]:
            radio = ttk.Radiobutton(
                property_radio_frame,
                text=property_type,
                variable=self.property_var,
                value=property_type
            )
            radio.pack(side=tk.LEFT, padx=10)
            self.property_radios.append(radio)
            
        # Mensaje informativo para configuración manual
        self.manual_config_label = ttk.Label(
            self.options_frame,
            text="Puede configurar las columnas manualmente para detectar los valores de seguridad y propiedad",
            foreground="gray",
            font=("", 8, "italic")
        )
        self.manual_config_label.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        # Inicialmente ocultar el mensaje informativo
        self.manual_config_label.pack_forget()
        
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
        # Vincular Enter para generar QR de la habitación
        self.room_entry.bind('<Return>', lambda e: self._generate_room_qr())
        
        button_frame = ttk.Frame(search_content_frame)
        button_frame.grid(row=0, column=1, sticky="e")
        
        self.generate_btn = ttk.Button(button_frame, text="Generar QR", 
                                     command=self._generate_room_qr, state="disabled")
        self.generate_btn.pack(side=tk.LEFT)
        
        self.generate_all_btn = ttk.Button(button_frame, text="Generar Todos", 
                                         command=self._generate_all_qr, state="disabled")
        self.generate_all_btn.pack(side=tk.LEFT, padx=5)
        
    def _browse_new_excel(self):
        """Abrir diálogo para seleccionar nuevo archivo Excel."""
        filename = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self._load_excel_file(filename)
            
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
            return
        
        # Si llegamos aquí, la hoja se cargó correctamente y las columnas se detectaron
        # Guardar la hoja en la configuración
        file_path = self.file_path.get()
        self.config_manager.add_recent_file(file_path, sheet_name)
        
        # Cargar la configuración guardada para esta hoja si existe
        self._load_sheet_config(file_path, sheet_name)
        
        # Habilitar la búsqueda de habitación y mostrar mensaje informativo
        self._enable_room_search()
        self.manual_config_label.pack(fill=tk.X, padx=5, pady=(5, 2))
        
    def _save_sheet_config(self):
        """Guardar la configuración actual de la hoja."""
        if not self.excel_manager or not self.excel_manager.sheet:
            self.logger.debug("No se puede guardar la configuración: No hay hoja activa")
            return
            
        file_path = self.file_path.get()
        sheet_name = self.sheet_var.get()
        
        if not file_path or not sheet_name:
            self.logger.debug("No se puede guardar la configuración: No hay archivo o hoja seleccionada")
            return
        
        # Verificar si ya existe configuración para esta hoja
        existing_config = self.config_manager.get_sheet_config(file_path, sheet_name)
        
        # Recopilar la configuración actual
        config_data = {
            # Estado de los checkboxes
            "use_excel_security": self.use_excel_security.get(),
            "use_excel_property": self.use_excel_property.get(),
            
            # Valores de los radio buttons
            "security_type": self.security_var.get(),
            "property_type": self.property_var.get(),
            
            # Columnas asignadas (si existen)
            "columns": {}
        }
        
        # Guardar información de columnas si están configuradas
        if self.excel_manager.columns:
            columns_config = {
                "room": self.excel_manager.columns.room,
                "ssid": self.excel_manager.columns.ssid
            }
            
            if hasattr(self.excel_manager.columns, 'password') and self.excel_manager.columns.password is not None:
                columns_config["password"] = self.excel_manager.columns.password
                
            if hasattr(self.excel_manager.columns, 'encryption') and self.excel_manager.columns.encryption is not None:
                columns_config["encryption"] = self.excel_manager.columns.encryption
                
            if hasattr(self.excel_manager.columns, 'property_type') and self.excel_manager.columns.property_type is not None:
                columns_config["property_type"] = self.excel_manager.columns.property_type
                
            config_data["columns"] = columns_config
            config_data["columns_detected"] = self.excel_manager.columns_detected
        
        # Unir con configuración existente (preservando cualquier campo que no estemos actualizando)
        if existing_config:
            for key, value in existing_config.items():
                if key not in config_data:
                    config_data[key] = value
        
        # Guardar configuración
        self.config_manager.save_sheet_config(file_path, sheet_name, config_data)
        self.logger.debug(f"Configuración guardada para hoja '{sheet_name}' en archivo '{file_path}'")
        
    def _load_sheet_config(self, file_path: str, sheet_name: str):
        """Cargar la configuración guardada para una hoja específica."""
        config_data = self.config_manager.get_sheet_config(file_path, sheet_name)
        if not config_data:
            self.logger.debug(f"No hay configuración guardada para hoja '{sheet_name}'")
            return
        
        self.logger.info(f"Cargando configuración guardada para hoja '{sheet_name}'")
            
        # Aplicar configuración de checkboxes si existe
        if "use_excel_security" in config_data:
            self.use_excel_security.set(config_data["use_excel_security"])
            self._update_security_switch_state(save_config=False)  # No guardar para evitar ciclo
            
        if "use_excel_property" in config_data:
            self.use_excel_property.set(config_data["use_excel_property"])
            self._update_property_switch_state(save_config=False)  # No guardar para evitar ciclo
            
        # Aplicar configuración de radio buttons si existe
        if "security_type" in config_data:
            self.security_var.set(config_data["security_type"])
            
        if "property_type" in config_data:
            self.property_var.set(config_data["property_type"])
            
        # Aplicar configuración de columnas si existe y no se han detectado automáticamente
        if "columns" in config_data and config_data["columns"] and not self.excel_manager.columns_detected:
            # Verificar que la configuración tiene las columnas requeridas
            if "room" in config_data["columns"] and "ssid" in config_data["columns"]:
                self.excel_manager.set_columns_manually(config_data["columns"])
                self.logger.debug("Columnas personalizadas aplicadas desde configuración guardada")
                
        self.logger.debug(f"Configuración cargada exitosamente para hoja '{sheet_name}'")
        
    def _update_security_switch_state(self, save_config=True):
        """Actualizar estado de los controles según la opción de obtener seguridad desde Excel."""
        if self.use_excel_security.get():
            # Está activado - Cambiar etiqueta a ON
            self.security_switch_label.config(
                text="ON - Los valores de seguridad en Excel, tienen preferencia.",
                foreground="green"
            )
            # Ya no desactivamos los radio buttons, permanecen activos
            for radio in self.security_radios:
                radio['state'] = 'normal'
        else:
            # Está desactivado - Cambiar etiqueta a OFF
            self.security_switch_label.config(
                text="OFF - Se usará el tipo seleccionado por defecto.",
                foreground="gray"
            )
            # Activar radio buttons de seguridad
            for radio in self.security_radios:
                radio['state'] = 'normal'
                
        # Guardar la configuración actualizada si se solicita
        if save_config:
            self._save_sheet_config()
    
    def _update_property_switch_state(self, save_config=True):
        """Actualizar estado de los controles según la opción de obtener propiedad desde Excel."""
        if self.use_excel_property.get():
            # Está activado - Cambiar etiqueta a ON
            self.property_switch_label.config(
                text="ON - Los valores de propiedad en Excel, tienen preferencia.",
                foreground="green"
            )
            # Ya no desactivamos los radio buttons, permanecen activos
            for radio in self.property_radios:
                radio['state'] = 'normal'
        else:
            # Está desactivado - Cambiar etiqueta a OFF
            self.property_switch_label.config(
                text="OFF - Se usará la propiedad seleccionada por defecto.",
                foreground="gray"
            )
            # Activar radio buttons de propiedad
            for radio in self.property_radios:
                radio['state'] = 'normal'
                
        # Guardar la configuración actualizada si se solicita
        if save_config:
            self._save_sheet_config()
    
    def _setup_manual_tab(self, parent: ttk.Frame):
        """Configurar la pestaña de entrada manual de credenciales WiFi."""
        # Marco para entrada de credenciales
        cred_frame = ttk.LabelFrame(parent, text="Credenciales WiFi", padding=5)
        cred_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Contenedor para entradas
        form_frame = ttk.Frame(cred_frame)
        form_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        form_frame.columnconfigure(1, weight=1)  # La columna de entradas se expande
        
        # SSID
        ttk.Label(form_frame, text="SSID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.manual_ssid = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.manual_ssid).grid(
            row=0, column=1, sticky="ew", padx=5, pady=2
        )
        
        # Contraseña
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.manual_password = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.manual_password).grid(
            row=1, column=1, sticky="ew", padx=5, pady=2
        )
        
        # Tipo de seguridad
        security_frame = ttk.LabelFrame(parent, text="Tipo de Seguridad", padding=5)
        security_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Variable y radio buttons para método de seguridad
        self.manual_security_var = tk.StringVar(value="WPA2")
        security_radio_frame = ttk.Frame(security_frame)
        security_radio_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        for security in ["WPA2", "WPA", "WEP", "nopass"]:
            ttk.Radiobutton(
                security_radio_frame,
                text=security,
                variable=self.manual_security_var,
                value=security
            ).pack(side=tk.LEFT, padx=10)
        
        # Logo/Propiedad
        property_frame = ttk.LabelFrame(parent, text="Propiedad", padding=5)
        property_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Variable y radio buttons para propiedad
        self.manual_property_var = tk.StringVar(value="VDPF")
        property_radio_frame = ttk.Frame(property_frame)
        property_radio_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        for property_type in ["VLE", "VDPF", "Sin Logo"]:
            ttk.Radiobutton(
                property_radio_frame,
                text=property_type,
                variable=self.manual_property_var,
                value=property_type
            ).pack(side=tk.LEFT, padx=10)
            
        # Botón de generación
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Generar QR", 
            command=self._generate_manual_qr
        ).pack(side=tk.RIGHT, padx=5)
        
    def _generate_manual_qr(self):
        """Generar QR desde datos ingresados manualmente."""
        # Validar SSID (requerido)
        ssid = self.manual_ssid.get().strip()
        if not ssid:
            messagebox.showerror("Error", "El SSID es obligatorio")
            return
            
        # Obtener otros valores
        password = self.manual_password.get().strip() or None
        security = self.manual_security_var.get()
        property_type = self.manual_property_var.get()
        
        if property_type == "Sin Logo":
            property_type = None
            
        # Crear credenciales WiFi
        credentials = WiFiCredentials(
            ssid=ssid,
            password=password,
            encryption=security if security != "nopass" else None,
            property_type=property_type
        )
        
        # Generar QR
        self._generate_and_show_qr(credentials, ssid)
        
    def _generate_and_show_qr(self, credentials: WiFiCredentials, filename_prefix: str = "qr"):
        """
        Generar un código QR y mostrarlo en la interfaz.
        
        Args:
            credentials (WiFiCredentials): Credenciales de WiFi para el QR
            filename_prefix (str): Prefijo para el nombre del archivo guardado (normalmente el SSID)
        """
        try:
            # Generar QR básico
            qr_buffer = self.qr_manager.generate_wifi_qr(credentials)
            
            # Agregar logo si hay propiedad
            if credentials.property_type:
                qr_buffer = self.qr_manager.add_logo(qr_buffer, credentials.property_type)
                
            # Agregar texto al buffer
            qr_buffer = self.qr_manager.add_text(qr_buffer, credentials.ssid, credentials.password)
            
            # Asegurarse de que el buffer se resetea para leer desde el principio
            qr_buffer.seek(0)
            
            # Abrir la imagen para mostrarla
            qr_img = Image.open(qr_buffer)
            
            # Obtener dimensiones del área de visualización
            preview_width = 300  # Ancho fijo del área de previsualización
            preview_height = 300  # Alto fijo del área de previsualización
            
            # Redimensionar manteniendo la proporción solo para la visualización
            img_width, img_height = qr_img.size
            ratio = min(preview_width/img_width, preview_height/img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            
            # Crear una imagen redimensionada solo para la visualización
            display_img = qr_img.resize(new_size, Image.LANCZOS)
            
            # Crear un fondo blanco del tamaño del área de visualización
            background = Image.new('RGB', (preview_width, preview_height), 'white')
            
            # Calcular posición para centrar la imagen redimensionada
            offset = ((preview_width - new_size[0]) // 2, (preview_height - new_size[1]) // 2)
            
            # Pegar la imagen redimensionada en el fondo blanco
            background.paste(display_img, offset)
            
            # Mostrar en la interfaz
            photo = ImageTk.PhotoImage(background)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
            
            # Actualizar etiqueta de configuración
            config_text = f"SSID: {credentials.ssid}\n"
            if credentials.password:
                config_text += f"Contraseña: {credentials.password}\n"
            config_text += f"Seguridad: {credentials.encryption or 'Sin encriptación'}\n"
            if credentials.property_type:
                config_text += f"Propiedad: {credentials.property_type}"
            
            self.config_label.configure(text=config_text)
            
            # Guardar QR en archivo (usando el buffer original sin redimensionar)
            sanitized_ssid = ''.join(c for c in credentials.ssid if c.isalnum() or c in '_- ')
            
            # Definir el nombre del archivo según el tipo de logo
            if credentials.property_type == 'VLEV' or credentials.property_type == 'VLE':
                filename = f"VLE_{sanitized_ssid}.png"
            elif credentials.property_type == 'VDPF' or credentials.property_type == 'Flamingos':
                filename = f"VDPF_{sanitized_ssid}.png"
            else:
                # Sin logo o cualquier otro caso
                filename = f"WIFI_{sanitized_ssid}.png"
            
            # Guardar la imagen final con los mismos datos (texto ya incluido en el buffer)
            self.last_qr_path = self.qr_manager.save_qr(
                qr_buffer, 
                filename, 
                ssid=credentials.ssid, 
                password=credentials.password
            )
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando código QR: {str(e)}")
            logger.error(f"Error en _generate_and_show_qr: {str(e)}")
            return False
            
    def _generate_room_qr(self):
        """Generar código QR para la habitación especificada."""
        room = self.room_number.get().strip()
        if not room:
            messagebox.showerror("Error", "Por favor ingrese un número de habitación")
            return
            
        if not self.excel_manager or not self.excel_manager.sheet:
            messagebox.showerror("Error", "No hay hoja de Excel cargada")
            return
            
        credentials = self.excel_manager.get_room_data(room)
        if not credentials:
            messagebox.showerror("Error", f"No se encontró la habitación {room}")
            return
            
        # Reemplazar valores según configuración
        if not self.use_excel_security.get() or not credentials.encryption:
            credentials.encryption = self.security_var.get()
            
        if not self.use_excel_property.get() or not credentials.property_type:
            property_val = self.property_var.get()
            credentials.property_type = None if property_val == "Sin Logo" else property_val
            
        # Generar QR
        self._generate_and_show_qr(credentials, f"{room}")
            
    def _generate_all_qr(self):
        """Generar códigos QR para todas las habitaciones."""
        if not self.excel_manager or not self.excel_manager.sheet:
            messagebox.showerror("Error", "No hay hoja de Excel cargada")
            return
        
        all_rooms = self.excel_manager.get_all_rooms()
        if not all_rooms:
            messagebox.showerror("Error", "No se encontraron habitaciones en la hoja seleccionada")
            return
        
        # Diálogo de confirmación avanzada
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("Confirmar generación masiva")
        confirm_dialog.grab_set()
        confirm_dialog.resizable(False, False)
        
        label = ttk.Label(
            confirm_dialog, 
            text=f"Se generarán {len(all_rooms)} códigos QR. Este proceso no se puede cancelar. \n\nPara continuar, escriba exactamente: Generar Todo",
            justify=tk.LEFT,
            wraplength=350
        )
        label.pack(padx=20, pady=(20, 10))
        
        entry_var = tk.StringVar()
        entry = ttk.Entry(confirm_dialog, textvariable=entry_var, width=25, font=("", 12))
        entry.pack(pady=(0, 10))
        entry.focus_set()
        
        button_frame = ttk.Frame(confirm_dialog)
        button_frame.pack(pady=(0, 15))
        
        confirmed = {'value': False}
        
        def on_confirm():
            if entry_var.get().strip() == "Generar Todo":
                confirmed['value'] = True
                confirm_dialog.destroy()
            else:
                messagebox.showerror("Confirmación requerida", "Debe escribir exactamente: Generar Todo para continuar.", parent=confirm_dialog)
                entry.focus_set()
        
        def on_cancel():
            confirm_dialog.destroy()
        
        confirm_btn = ttk.Button(button_frame, text="Confirmar", command=on_confirm)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancelar", command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        confirm_dialog.bind('<Return>', lambda e: on_confirm())
        confirm_dialog.bind('<Escape>', lambda e: on_cancel())
        
        self.root.wait_window(confirm_dialog)
        if not confirmed['value']:
            return
        
        # Diálogo de progreso/cancelación
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Generando códigos QR")
        progress_dialog.grab_set()
        progress_dialog.resizable(False, False)
        ttk.Label(progress_dialog, text="Generando códigos QR, por favor espere...", font=("", 11)).pack(padx=20, pady=(20, 10))
        progress_var = tk.StringVar(value="0 / {}".format(len(all_rooms)))
        progress_label = ttk.Label(progress_dialog, textvariable=progress_var, font=("", 10))
        progress_label.pack(pady=(0, 10))
        cancel_flag = {'cancel': False}
        def on_cancel_progress():
            cancel_flag['cancel'] = True
            progress_dialog.destroy()
        cancel_btn = ttk.Button(progress_dialog, text="Cancelar", command=on_cancel_progress)
        cancel_btn.pack(pady=(0, 15))
        progress_dialog.protocol("WM_DELETE_WINDOW", on_cancel_progress)
        self.root.update()  # Cambiado de update_idletasks() a update() para permitir eventos
        
        count = 0
        for idx, room_data in enumerate(all_rooms, 1):
            if cancel_flag['cancel']:
                break
            # Reemplazar valores según configuración
            if not self.use_excel_security.get() or not room_data.encryption:
                room_data.encryption = self.security_var.get()
            if not self.use_excel_property.get() or not room_data.property_type:
                property_val = self.property_var.get()
                room_data.property_type = None if property_val == "Sin Logo" else property_val
            # Generar QR (usando nombre de habitación como prefijo de archivo)
            room_name = room_data.ssid.replace(" ", "_")
            if self._generate_and_show_qr(room_data, room_name):
                count += 1
            progress_var.set(f"{idx} / {len(all_rooms)}")
            self.root.update()  # Cambiado de update_idletasks() a update() para permitir eventos
        progress_dialog.destroy()
        if cancel_flag['cancel']:
            messagebox.showinfo("Cancelado", f"Operación cancelada. Se generaron {count} códigos QR antes de cancelar.")
        elif count > 0:
            messagebox.showinfo("Éxito", f"Se generaron {count} códigos QR")
        else:
            messagebox.showerror("Error", "No se pudo generar ningún código QR")
            
    def _open_codes_folder(self):
        """Abrir carpeta donde se guardan los códigos QR generados."""
        folder_path = os.path.abspath(self.qr_manager.output_dir)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        # Usar el comando correcto según la plataforma
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {str(e)}")
            
    def _open_last_qr(self):
        """Abrir el último código QR generado."""
        if hasattr(self, 'last_qr_path') and os.path.exists(self.last_qr_path):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(self.last_qr_path)
                elif os.name == 'posix':  # macOS, Linux
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', self.last_qr_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', self.last_qr_path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")
        else:
            messagebox.showinfo("Información", "No hay código QR generado recientemente")
            
    def _update_recent_files_list(self):
        """Actualizar lista de archivos recientes en el combobox."""
        recent_files = self.config_manager.get_recent_files()
        files = [f["path"] for f in recent_files]
        self.file_combo['values'] = files
        
    def _on_file_selected(self, event):
        """Manejar selección de archivo en el combobox."""
        filename = self.file_path.get()
        if filename:
            self._load_excel_file(filename)
            
    def _show_column_dialog(self):
        """Mostrar diálogo para selección manual de columnas."""
        if not self.excel_manager:
            return
            
        # Usar valores actuales de columnas como iniciales, si existen
        initial_columns = None
        if self.excel_manager.columns:
            initial_columns = {
                'room': self.excel_manager.columns.room,
                'ssid': self.excel_manager.columns.ssid
            }
            if hasattr(self.excel_manager.columns, 'password') and self.excel_manager.columns.password is not None:
                initial_columns['password'] = self.excel_manager.columns.password
            if hasattr(self.excel_manager.columns, 'encryption') and self.excel_manager.columns.encryption is not None:
                initial_columns['encryption'] = self.excel_manager.columns.encryption
            if hasattr(self.excel_manager.columns, 'property_type') and self.excel_manager.columns.property_type is not None:
                initial_columns['property_type'] = self.excel_manager.columns.property_type
        
        # Mostrar diálogo
        dialog = ColumnSelectionDialog(self.root, initial_columns)
        self.root.wait_window(dialog)
        
        # Si se seleccionaron columnas, aplicarlas
        if dialog.column_indices:
            if self.excel_manager.set_columns_manually(dialog.column_indices):
                self._enable_room_search()
                # Guardar configuración después de asignar columnas manualmente
                self._save_sheet_config()
                messagebox.showinfo("Éxito", "Columnas configuradas correctamente")
                self.logger.debug("Columnas configuradas manualmente y guardadas en configuración")
            else:
                messagebox.showerror("Error", "No se pudieron configurar las columnas")
                
    def _enable_room_search(self):
        """Habilitar controles de búsqueda de habitación."""
        self.room_entry['state'] = 'normal'
        self.generate_btn['state'] = 'normal'
        self.generate_all_btn['state'] = 'normal'
        self.manual_cols_btn['state'] = 'normal'
        
    def _reset_excel_ui(self):
        """Resetear elementos de UI relacionados con Excel a su estado inicial."""
        self.excel_manager = None
        self.sheet_combo['values'] = []
        self.sheet_combo.set("")
        self.sheet_combo['state'] = 'disabled'
        self.load_sheet_btn['state'] = 'disabled'
        self.room_entry['state'] = 'disabled'
        self.room_entry.delete(0, tk.END)
        self.generate_btn['state'] = 'disabled'
        self.generate_all_btn['state'] = 'disabled'
        self.manual_cols_btn['state'] = 'disabled'

    def _toggle_admin_mode(self):
        """Alternar entre modo bloqueado/desbloqueado de opciones administrativas."""
        # Verificar si ya está desbloqueado
        if hasattr(self, 'admin_unlocked') and self.admin_unlocked:
            # Si ya está desbloqueado, bloquear directamente
            self.admin_unlocked = False
            self._toggle_admin_controls(False)
            self.lock_button.config(text="🔒")
            self.logger.info("Opciones de administrador deshabilitadas")
            return
            
        # Mostrar diálogo de contraseña
        dialog = PasswordDialog(self.root)
        self.root.wait_window(dialog)
        
        # Si la contraseña fue correcta, habilitar controles
        if dialog.success:
            self.admin_unlocked = True
            self._toggle_admin_controls(True)
            self.lock_button.config(text="🔓")
            messagebox.showinfo("Acceso concedido", "Opciones de administrador habilitadas")
            self.logger.info("Opciones de administrador habilitadas")
        else:
            self.admin_unlocked = False
            self._toggle_admin_controls(False)
            self.lock_button.config(text="🔒")
            self.logger.debug("Intento fallido de acceso a opciones de administrador")
    
    def _toggle_admin_controls(self, enabled: bool):
        """Habilitar o deshabilitar controles de administrador."""
        
        if hasattr(self, 'options_frame'):
            if enabled:
                # Si está habilitado, mostrar el frame de opciones y ocultar el frame de autenticación
                if hasattr(self, 'auth_required_frame'):
                    self.auth_required_frame.pack_forget()
                self.options_frame.pack(fill=tk.X, padx=5, pady=5)
                self.logger.debug("Panel de opciones de Excel visible")
            else:
                # Si está deshabilitado, ocultar el frame de opciones y mostrar un mensaje
                self.options_frame.pack_forget()
                
                # Crear frame de aviso de autenticación requerida si no existe
                if not hasattr(self, 'auth_required_frame'):
                    self.auth_required_frame = ttk.LabelFrame(self.excel_frame, text="Opciones de Excel", padding=5)
                    
                    message_frame = ttk.Frame(self.auth_required_frame)
                    message_frame.pack(fill=tk.X, expand=True, pady=10)
                    
                    # Icono de candado
                    lock_label = ttk.Label(message_frame, text="🔒", font=("", 20))
                    lock_label.pack(pady=(5, 10))
                    
                    # Mensaje informativo
                    message_label = ttk.Label(
                        message_frame,
                        text="Configuración protegida",
                        font=("", 11, "bold")
                    )
                    message_label.pack(pady=(0, 5))
                    
                    # Mensaje de instrucción
                    instruction_label = ttk.Label(
                        message_frame,
                        text="Haga clic en el botón de candado en la parte inferior\npara desbloquear las opciones avanzadas.",
                        justify=tk.CENTER
                    )
                    instruction_label.pack(pady=(0, 10))
                
                # Mostrar el frame de autenticación
                self.auth_required_frame.pack(fill=tk.X, padx=5, pady=5)
                self.logger.debug("Panel de opciones de Excel oculto")
                
    def run(self):
        """Iniciar la aplicación."""
        self.root.mainloop()