
```md
# Gestión de logotipos en QRManager

En la aplicación, la clase `QRManager` en el archivo `qr_manager.py` es la que determina qué imagen se usa como logotipo para cada caso.

## Funcionamiento

### Definición de rutas de logotipos
```python
LOGO_PATHS = {
    "VLEV": "logos/VLEV.png",
    "VG": "logos/VDPF.png"
}
```

### Método `_normalize_property_type`
Este método estático normaliza los diferentes nombres de propiedades a un formato estándar:

```python
@staticmethod
def _normalize_property_type(property_type: Optional[str]) -> Optional[str]:
    """Normalizar tipo de propiedad a formato estándar."""
    if not property_type:
        return None
        
    property_type = property_type.upper().strip()
    if property_type in ('VLEV', 'VLE'):
        return 'VLEV'
    elif property_type in ('VDPF', 'VG', 'VDP'):
        return 'VG'
    elif property_type in ('SIN LOGO', 'NONE', 'NO LOGO'):
        return None
    return None
```

### Método `add_logo`
Este método aplica el logotipo correspondiente al código QR basándose en el tipo de propiedad normalizado:

```python
def add_logo(self, qr_buffer: BytesIO, property_type: str) -> BytesIO:
    # Normalizar y validar tipo de propiedad
    property_type = self._normalize_property_type(property_type)
    if not property_type or property_type not in self.LOGO_PATHS:
        logger.warning(f"Tipo de propiedad inválido: {property_type}")
        return qr_buffer
        
    logo_path = self.LOGO_PATHS[property_type]
    # ... código para agregar el logo al QR ...
```

## Flujo del proceso

1. Se recibe un tipo de propiedad (ej. `"VLE"`, `"VDPF"`, etc.).
2. Se normaliza a uno de los tipos estándar (`"VLEV"` o `"VG"`).
3. Se busca la ruta del archivo de imagen correspondiente en el diccionario `LOGO_PATHS`.
4. Si se encuentra una ruta válida, se aplica ese logotipo al código QR.

## Agregar un nuevo logotipo

Para añadir una nueva propiedad con su logotipo:

1. **Añadir la ruta del nuevo logotipo** al diccionario `LOGO_PATHS`.
2. **Actualizar el método** `_normalize_property_type` para reconocer el nuevo tipo de propiedad.
```
