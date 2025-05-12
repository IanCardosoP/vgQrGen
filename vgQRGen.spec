# vgQRGen.spec
# Ejecuta: pyinstaller vgQRGen.spec

import os

# Asegurar que las carpetas existan
for folder in ['codes', 'logs']:
    os.makedirs(folder, exist_ok=True)

# Crear archivos placeholder (esto asegura que las carpetas no estén vacías)
placeholder_files = [
    ('codes', '.keep'),
    ('logs', '.keep')
]

for folder, filename in placeholder_files:
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('# Este archivo es para mantener la carpeta en el paquete')
        print(f"Creado archivo placeholder: {file_path}")

block_cipher = None

a = Analysis(
    ['vgqr_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('logos/*', 'logos'),
        ('codes/.keep', 'codes'),
        ('logs/.keep', 'logs'),
        ('QR_tamanio_resolucion.md', '.'),
        ('README.md', '.'),
        ('Logo_Set.md', '.'),
    ],
    hiddenimports=['openpyxl', 'et_xmlfile'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vgQRGen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vgQRGen'
)
