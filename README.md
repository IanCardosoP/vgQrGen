# WiFi QR Code Generator

A Python application for generating QR codes for WiFi networks, with support for Excel file import and manual entry.

## Features

- Generate QR codes for WiFi networks with configurable encryption types
- Import network data from Excel files
- Add property logos to QR codes (VLEV, VDPF, etc.)
- Add SSID and password text below QR codes
- Preview QR codes before saving
- GUI interface with Excel import and manual entry tabs

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

```bash
python -m qr_generator [--debug]
```

### Excel File Format

The Excel file should contain the following columns (column names are flexible and will be auto-detected):
- Room number (e.g., 1101A, 3506B)
- SSID
- Password (optional for open networks)
- Encryption type (optional, defaults to WPA2)
- Property type (optional, for logo selection)

### GUI Features

#### Excel Import Tab
- Select Excel file
- Search for specific room numbers
- Generate QR for single room or all rooms
- Preview generated QR codes

#### Manual Entry Tab
- Enter network details manually
- Select encryption type and property
- Preview and save QR codes

### Common Features
- Open codes folder
- View last generated QR
- Preview QR before saving

## Project Structure

```
qr_generator/
├── __main__.py           # Application entry point
├── core/
│   ├── excel_manager.py  # Excel file handling
│   └── qr_manager.py     # QR code generation
├── gui/
│   └── main_window.py    # GUI implementation
└── utils/
    └── logging_utils.py  # Logging configuration
```

## Supported Properties

- VLEV/VLE (Villa Estancia)
- VDPF/VG/VDP (Villa Group)

## Dependencies

- openpyxl: Excel file handling
- Pillow: Image processing
- segno: QR code generation
- tqdm: Progress bars for batch processing
