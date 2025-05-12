# Guía para publicar nuevas versiones

Este documento explica cómo publicar nuevas versiones de la aplicación vgQRGen utilizando GitHub Actions y Releases.

## Prerequisitos

- Tener acceso de escritura al repositorio en GitHub
- Git instalado en tu máquina local
- Cambios ya confirmados (commits) en la rama principal

## Proceso para publicar una nueva versión

1. **Actualiza el archivo CHANGELOG.md** con los detalles de los cambios en la nueva versión.

2. **Confirma tus cambios** en la rama principal:
   ```bash
   git add CHANGELOG.md
   git commit -m "Actualizar CHANGELOG para versión X.Y.Z"
   git push origin main
   ```

3. **Crea una nueva etiqueta (tag) con el número de versión**:
   ```bash
   git tag vX.Y.Z
   # Ejemplo: git tag v1.0.1
   ```

4. **Sube la etiqueta a GitHub**:
   ```bash
   git push origin vX.Y.Z
   # Ejemplo: git push origin v1.0.1
   ```

5. **Verifica el proceso automático**:
   - Navega a la pestaña "Actions" en el repositorio de GitHub
   - Deberías ver un flujo de trabajo "Build and Release" en ejecución
   - Espera a que el flujo de trabajo se complete (tomará algunos minutos)

6. **Verifica el release**:
   - Ve a la sección "Releases" en GitHub
   - Deberías ver la nueva versión publicada con:
     - El archivo ZIP de la aplicación
     - Notas de versión extraídas del workflow
     - El archivo README.md adjunto

## Formato de versiones

Seguimos el formato de [Versionado Semántico](https://semver.org/lang/es/):

- **X** (Mayor): Cambios incompatibles con versiones anteriores
- **Y** (Menor): Nuevas funcionalidades que mantienen compatibilidad
- **Z** (Parche): Correcciones de errores que mantienen compatibilidad

## Ejecución manual del workflow

Si necesitas ejecutar el proceso manualmente sin crear una etiqueta:

1. Ve a la pestaña "Actions" en GitHub
2. Selecciona el workflow "Build and Release"
3. Haz clic en "Run workflow"
4. Selecciona la rama y haz clic en "Run workflow"

Nota: El release creado de esta manera no tendrá un número de versión extraído de la etiqueta.
