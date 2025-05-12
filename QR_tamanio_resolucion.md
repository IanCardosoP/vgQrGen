# Modificar el tamaño y la resolución de los códigos QR generados

Esta documentación explica cómo cambiar el tamaño y la resolución de las imágenes de los códigos QR generados por el sistema, detallando las funciones y clases involucradas, y las consideraciones técnicas para lograrlo correctamente.

---

## Índice
- [Modificar el tamaño y la resolución de los códigos QR generados](#modificar-el-tamaño-y-la-resolución-de-los-códigos-qr-generados)
  - [Índice](#índice)
  - [Introducción](#introducción)
  - [Clases y funciones involucradas](#clases-y-funciones-involucradas)
  - [Parámetros clave para tamaño y resolución](#parámetros-clave-para-tamaño-y-resolución)
  - [Cómo modificar el tamaño del QR](#cómo-modificar-el-tamaño-del-qr)
  - [Cómo modificar la resolución final de la imagen](#cómo-modificar-la-resolución-final-de-la-imagen)
  - [Consideraciones adicionales](#consideraciones-adicionales)
  - [Ejemplo práctico](#ejemplo-práctico)
  - [Resumen](#resumen)

---

## Introducción

El sistema genera códigos QR para credenciales WiFi y los guarda como imágenes PNG. El tamaño y la resolución de estas imágenes pueden ajustarse para adaptarse a diferentes necesidades de impresión o visualización. Este tutorial te guía para modificar estos parámetros en el código fuente.

---

## Clases y funciones involucradas

Las siguientes clases y métodos están directamente relacionados con el tamaño y la resolución de los QR:

- **Clase `QRManager`** (`vgQRGen/core/qr_manager.py`):
  - `generate_wifi_qr(credentials)`
  - `add_text(qr_buffer, ssid, password)`
  - `save_qr(qr_buffer, filename, ssid, password)`

Estas funciones trabajan en conjunto para generar, modificar y guardar la imagen final del QR.

---

## Parámetros clave para tamaño y resolución

1. **Resolución inicial del QR**
   - En `generate_wifi_qr`, el parámetro `scale` de `qr.save()` determina la resolución base del QR generado.
     ```python
     qr.save(buffer, kind='png', scale=30, border=4)
     ```
   - Un valor mayor de `scale` genera un QR más grande y nítido.

2. **Tamaño del lienzo final**
   - En `save_qr`, el lienzo estándar es:
     ```python
     standardized_img = Image.new('RGB', (825, 1100), 'white')
     ```
   - Cambia estos valores para modificar el tamaño final de la imagen (en píxeles).

3. **Redimensionamiento del QR**
   - El QR se redimensiona para ajustarse al lienzo:
     ```python
     resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
     standardized_img.paste(resized_img, (x_pos, y_pos))
     ```
   - El cálculo de `new_width` y `new_height` depende de la proporción del QR y del área disponible.

4. **Tamaño del texto**
   - En `add_text`, el tamaño de fuente es proporcional al ancho del QR:
     ```python
     font_size = max(26, qr_width // 23)
     ```
   - Puedes ajustar el valor mínimo o el divisor para cambiar el tamaño del texto.

---

## Cómo modificar el tamaño del QR

1. **Aumentar o reducir el tamaño del QR generado**
   - Modifica el parámetro `scale` en `generate_wifi_qr`:
     ```python
     qr.save(buffer, kind='png', scale=30, border=4)
     # Ejemplo: scale=40 para un QR más grande
     ```

2. **Ajustar el área del QR en el lienzo final**
   - Cambia el cálculo de `qr_area_height` en `save_qr`:
     ```python
     qr_area_height = int(1100 * 0.7)  # 70% del alto total
     # Puedes aumentar el porcentaje para un QR más grande en la imagen final
     ```

3. **Modificar el tamaño del lienzo final**
   - Cambia las dimensiones de `standardized_img`:
     ```python
     standardized_img = Image.new('RGB', (ancho, alto), 'white')
     # Ejemplo: (1000, 1400)
     ```

---

## Cómo modificar la resolución final de la imagen

- La resolución final depende del tamaño del lienzo (`standardized_img`) y del QR redimensionado.
- Para mayor calidad de impresión, usa valores altos (por ejemplo, 2480x3508 para A4 a 300dpi).
- Asegúrate de que el parámetro `scale` en `generate_wifi_qr` sea suficientemente alto para evitar pixelación al redimensionar.

---

## Consideraciones adicionales

- **Proporción**: Mantén la proporción entre ancho y alto para evitar distorsión.
- **Texto**: Si cambias el tamaño del lienzo, ajusta también el tamaño del texto en `add_text`.
- **Impresión**: Para impresión profesional, considera usar resoluciones estándar (por ejemplo, A4 a 300dpi).
- **Pruebas**: Verifica visualmente los resultados tras cualquier cambio.

---

## Ejemplo práctico

Supón que quieres una imagen final de 1000x1400 píxeles y un QR que ocupe el 80% del alto:

1. En `save_qr`, cambia:
   ```python
   standardized_img = Image.new('RGB', (1000, 1400), 'white')
   qr_area_height = int(1400 * 0.8)
   ```
2. En `generate_wifi_qr`, aumenta el `scale` si el QR se ve borroso:
   ```python
   qr.save(buffer, kind='png', scale=40, border=4)
   ```
3. En `add_text`, ajusta el tamaño de fuente si el texto se ve pequeño:
   ```python
   font_size = max(32, qr_width // 20)
   ```

Guarda los cambios y prueba generando un nuevo QR para verificar el resultado.

---

## Resumen

- Modifica el tamaño del lienzo en `save_qr` para cambiar la resolución final.
- Ajusta el parámetro `scale` en `generate_wifi_qr` para la nitidez del QR.
- Ajusta el tamaño del texto en `add_text` para mantener la legibilidad.
- Realiza pruebas visuales tras cada cambio.

---


