"""
Main Window Module for QR Generator Application.

This module implements the main graphical user interface for the QR code generator,
providing options to generate QR codes from Excel files or manual input.
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
    Convert Excel column letter to zero-based column index.
    
    Args:
        column_letter (str): Column letter (e.g., 'A', 'B', 'AA', etc.)
        
    Returns:
        int: Zero-based column index
        
    Examples:
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
    Convert zero-based column index to Excel column letter.
    
    Args:
        index (int): Zero-based column index
        
    Returns:
        str: Column letter (e.g., 'A', 'B', 'AA', etc.)
    """
    index += 1
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result

class SheetSelectionDialog(tk.Toplevel):
    """Dialog for selecting Excel sheet."""
    
    def __init__(self, parent, sheets: list):
        super().__init__(parent)
        self.title("Select Sheet")
        self.sheet_name = None
        
        # Center dialog
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Sheet selection
        ttk.Label(self, text="Select a sheet:").pack(pady=10)
        self.sheet_var = tk.StringVar(value=sheets[0] if sheets else "")
        sheet_combo = ttk.Combobox(self, textvariable=self.sheet_var, values=sheets)
        sheet_combo.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT)
        
    def _on_ok(self):
        self.sheet_name = self.sheet_var.get()
        self.destroy()
        
    def _on_cancel(self):
        self.destroy()

class ColumnSelectionDialog(tk.Toplevel):
    """Dialog for manually selecting Excel columns."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Select Columns")
        self.column_indices = None
        
        # Center dialog
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Column selection frame
        frame = ttk.LabelFrame(self, text="Column Letters", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Help text
        help_text = "Enter Excel column letters (A, B, C, etc.)"
        ttk.Label(frame, text=help_text, font=("", 9, "italic")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        # Column inputs
        self.columns = {}
        labels = {
            'room': 'Room Number Column *',
            'ssid': 'SSID Column *',
            'password': 'Password Column',
            'encryption': 'Encryption Column',
            'property_type': 'Property Column'
        }
        
        row = 1
        for key, label in labels.items():
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=5)
            entry.grid(row=row, column=1, sticky=tk.W, pady=2)
            self.columns[key] = var
            row += 1
            
        # Example
        example_text = "Example: A for first column, B for second, etc.\nUse AA, AB, etc. for columns after Z"
        ttk.Label(frame, text=example_text, font=("", 8)).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )
        
        row += 1
        ttk.Label(frame, text="* Required fields", font=("", 8, "italic")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=10
        )
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.LEFT)
        
    def _validate_column_letter(self, column: str) -> bool:
        """Validate Excel column letter format."""
        if not column:
            return False
        return all(c.isalpha() for c in column.upper())
        
    def _on_ok(self):
        try:
            # Validate required fields
            room = self.columns['room'].get().strip()
            ssid = self.columns['ssid'].get().strip()
            
            if not room or not ssid:
                messagebox.showerror(
                    "Error",
                    "Room and SSID columns are required"
                )
                return
                
            # Validate column letter format
            for key, var in self.columns.items():
                value = var.get().strip()
                if value and not self._validate_column_letter(value):
                    messagebox.showerror(
                        "Error",
                        f"Invalid column letter format for {key}: {value}\n"
                        "Please use letters only (A-Z, AA-ZZ, etc.)"
                    )
                    return
            
            # Convert letters to indices (zero-based)
            self.column_indices = {
                'room': excel_column_to_index(room),
                'ssid': excel_column_to_index(ssid)
            }
            
            # Add optional columns
            for key in ['password', 'encryption', 'property_type']:
                value = self.columns[key].get().strip()
                if value:
                    self.column_indices[key] = excel_column_to_index(value)
                    
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror(
                "Error",
                str(e) or "Invalid column letter format.\nPlease use letters only (A-Z, AA-ZZ, etc.)"
            )
            
    def _on_cancel(self):
        self.destroy()

class MainWindow:
    """Main application window for QR code generator."""
    
    def __init__(self):
        """Initialize the main window and its components."""
        self.root = tk.Tk()
        self.root.title("WiFi QR Generator")
        self.root.geometry("800x600")
        
        # Initialize managers
        self.qr_manager = QRManager()
        self.excel_manager = None
        
        # Setup UI components
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup all UI components."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Excel tab
        excel_frame = ttk.Frame(notebook)
        notebook.add(excel_frame, text="Excel Import")
        self._setup_excel_tab(excel_frame)
        
        # Manual input tab
        manual_frame = ttk.Frame(notebook)
        notebook.add(manual_frame, text="Manual Input")
        self._setup_manual_tab(manual_frame)
        
        # Common buttons
        self._setup_common_buttons()
        
    def _setup_excel_tab(self, parent: ttk.Frame):
        """Setup the Excel import tab."""
        # File selection
        file_frame = ttk.LabelFrame(parent, text="Excel File", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=50, state="readonly").pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse", command=self._browse_excel).pack(side=tk.LEFT)
        
        # Excel options frame
        self.options_frame = ttk.LabelFrame(parent, text="Excel Options", padding=5)
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sheet selection
        sheet_frame = ttk.Frame(self.options_frame)
        sheet_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sheet_frame, text="Sheet:").pack(side=tk.LEFT, padx=5)
        self.sheet_var = tk.StringVar()
        self.sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.sheet_var, state="disabled", width=40)
        self.sheet_combo.pack(side=tk.LEFT, padx=5)
        self.load_sheet_btn = ttk.Button(sheet_frame, text="Load Sheet", command=self._load_selected_sheet, state="disabled")
        self.load_sheet_btn.pack(side=tk.LEFT, padx=5)
        
        # Manual column selection button (initially disabled)
        self.manual_cols_btn = ttk.Button(
            self.options_frame, 
            text="Set Columns Manually", 
            command=self._show_column_dialog,
            state="disabled"
        )
        self.manual_cols_btn.pack(pady=5)
        
        # Room search frame (initially disabled)
        self.search_frame = ttk.LabelFrame(parent, text="Search Room", padding=5)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.room_number = tk.StringVar()
        self.room_entry = ttk.Entry(self.search_frame, textvariable=self.room_number, width=20, state="disabled")
        self.room_entry.pack(side=tk.LEFT, padx=5)
        
        self.generate_btn = ttk.Button(self.search_frame, text="Generate QR", 
                                     command=self._generate_room_qr, state="disabled")
        self.generate_btn.pack(side=tk.LEFT)
        
        self.generate_all_btn = ttk.Button(self.search_frame, text="Generate All", 
                                         command=self._generate_all_qr, state="disabled")
        self.generate_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Preview
        self.preview_label = ttk.Label(parent, text="QR Preview")
        self.preview_label.pack(pady=10)
        
    def _browse_excel(self):
        """Open file dialog to select Excel file."""
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filename:
            return
            
        self.file_path.set(filename)
        self.excel_manager = ExcelManager(filename)
        
        # Try to load the workbook
        success, error_msg = self.excel_manager.load_workbook()
        if not success:
            messagebox.showerror("Error", error_msg)
            self._reset_excel_ui()
            return
            
        # Enable and populate sheet selection
        sheets = self.excel_manager.get_sheet_names()
        self.sheet_combo['values'] = sheets
        self.sheet_combo.set(sheets[0] if sheets else "")
        self._enable_sheet_selection()
            
    def _enable_sheet_selection(self):
        """Enable sheet selection controls."""
        self.sheet_combo['state'] = 'readonly'
        self.load_sheet_btn['state'] = 'normal'
        
    def _load_selected_sheet(self):
        """Load the selected sheet and attempt to detect columns."""
        if not self.excel_manager:
            return
            
        sheet_name = self.sheet_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Please select a sheet first")
            return
            
        success, error_msg = self.excel_manager.set_active_sheet(sheet_name)
        if not success:
            messagebox.showerror("Error", error_msg)
            if "columns" in error_msg.lower():
                self._enable_manual_column_selection()
            return
            
        # Enable room search controls
        self._enable_room_search()
        
    def _enable_manual_column_selection(self):
        """Enable manual column selection."""
        self.manual_cols_btn['state'] = 'normal'
        
    def _enable_room_search(self):
        """Enable room search controls."""
        self.room_entry['state'] = 'normal'
        self.generate_btn['state'] = 'normal'
        self.generate_all_btn['state'] = 'normal'
        self.manual_cols_btn['state'] = 'normal'
        
    def _reset_excel_ui(self):
        """Reset Excel UI controls to initial state."""
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
        """Show dialog for manual column selection."""
        dialog = ColumnSelectionDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.column_indices:
            if self.excel_manager.set_columns_manually(dialog.column_indices):
                messagebox.showinfo("Success", "Columns set successfully")
                self._enable_room_search()
            else:
                messagebox.showerror("Error", "Failed to set columns")
                
    def _setup_manual_tab(self, parent: ttk.Frame):
        """Setup the manual input tab."""
        input_frame = ttk.LabelFrame(parent, text="Network Details", padding=5)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # SSID
        ttk.Label(input_frame, text="SSID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_ssid = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.manual_ssid, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        # Password
        ttk.Label(input_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_password = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.manual_password, width=30).grid(row=1, column=1, padx=5, pady=2)
        
        # Encryption
        ttk.Label(input_frame, text="Encryption:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_encryption = tk.StringVar(value="WPA2")
        ttk.Combobox(input_frame, textvariable=self.manual_encryption, 
                    values=["WPA", "WPA2", "WEP", "nopass"], 
                    state="readonly").grid(row=2, column=1, padx=5, pady=2)
        
        # Property
        ttk.Label(input_frame, text="Property:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.manual_property = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.manual_property,
                    values=["VLEV", "VLE", "VDPF", "VG", "VDP"],
                    state="readonly").grid(row=3, column=1, padx=5, pady=2)
        
        # Generate button
        ttk.Button(input_frame, text="Generate QR", 
                  command=self._generate_manual_qr).grid(row=4, column=0, columnspan=2, pady=10)
                  
        # Preview
        self.manual_preview_label = ttk.Label(parent, text="QR Preview")
        self.manual_preview_label.pack(pady=10)
        
    def _setup_common_buttons(self):
        """Setup buttons common to both tabs."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Open Codes Folder", 
                  command=self._open_codes_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Last QR", 
                  command=self._open_last_qr).pack(side=tk.LEFT)
        
    def _generate_room_qr(self):
        """Generate QR code for specific room from Excel."""
        if not self.excel_manager:
            messagebox.showerror("Error", "Please select an Excel file first")
            return
            
        room = self.room_number.get().strip()
        if not room:
            messagebox.showerror("Error", "Please enter a room number")
            return
            
        try:
            credentials = self.excel_manager.get_room_data(room)
            if credentials:
                self._generate_and_preview_qr(credentials)
            else:
                messagebox.showerror("Error", f"Room {room} not found or missing data")
        except Exception as e:
            logger.error(f"Error generating QR for room {room}: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _generate_all_qr(self):
        """Generate QR codes for all rooms in Excel."""
        if not self.excel_manager:
            messagebox.showerror("Error", "Please select an Excel file first")
            return
            
        try:
            credentials_list = self.excel_manager.get_all_rooms()
            if not credentials_list:
                messagebox.showinfo("Info", "No valid rooms found in Excel file")
                return
                
            for cred in credentials_list:
                self._generate_and_preview_qr(cred, show_preview=False)
                
            messagebox.showinfo("Success", 
                              f"Generated {len(credentials_list)} QR codes in the codes folder")
        except Exception as e:
            logger.error(f"Error generating all QRs: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _generate_manual_qr(self):
        """Generate QR code from manual input."""
        ssid = self.manual_ssid.get().strip()
        if not ssid:
            messagebox.showerror("Error", "SSID is required")
            return
            
        credentials = WiFiCredentials(
            ssid=ssid,
            password=self.manual_password.get().strip(),
            encryption=self.manual_encryption.get(),
            property_type=self.manual_property.get()
        )
        
        self._generate_and_preview_qr(credentials)
        
    def _generate_and_preview_qr(self, credentials: WiFiCredentials, show_preview: bool = True):
        """Generate QR code and update preview."""
        try:
            buffer = self.qr_manager.generate_wifi_qr(credentials)
            
            if credentials.property_type:
                buffer = self.qr_manager.add_logo(buffer, credentials.property_type)
                
            # Add SSID and password text
            buffer = self.qr_manager.add_text(buffer, credentials.ssid, credentials.password or "")
            
            # Save QR
            self.last_qr_path = self.qr_manager.save_qr(buffer, f"qr_{credentials.ssid}")
            
            # Update preview if needed
            if show_preview:
                self._update_preview(buffer)
                
        except Exception as e:
            logger.error(f"Error generating QR: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def _update_preview(self, buffer):
        """Update QR preview in UI."""
        try:
            image = Image.open(buffer)
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            
            # Update preview in current tab
            if self.root.focus_get():
                if str(self.root.focus_get()).startswith(str(self.preview_label)):
                    self.preview_label.configure(image=photo)
                    self.preview_label.image = photo
                else:
                    self.manual_preview_label.configure(image=photo)
                    self.manual_preview_label.image = photo
                    
        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}")
            
    def _open_codes_folder(self):
        """Open the codes folder in system file explorer."""
        try:
            os.startfile(self.qr_manager.output_dir)
        except Exception as e:
            logger.error(f"Error opening codes folder: {str(e)}")
            messagebox.showerror("Error", f"Could not open codes folder: {str(e)}")
            
    def _open_last_qr(self):
        """Open the last generated QR code."""
        if hasattr(self, 'last_qr_path') and os.path.exists(self.last_qr_path):
            try:
                os.startfile(self.last_qr_path)
            except Exception as e:
                logger.error(f"Error opening last QR: {str(e)}")
                messagebox.showerror("Error", f"Could not open QR: {str(e)}")
        else:
            messagebox.showinfo("Info", "No QR code has been generated yet")
            
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()