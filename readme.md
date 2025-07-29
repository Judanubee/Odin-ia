# Odin-IA: Evaluador de Exámenes de Opción Múltiple

Odin-IA es una aplicación web sencilla construida con Flask y OpenCV que permite la evaluación automática de hojas de examen de opción múltiple. El sistema funciona en dos fases: primero, "aprende" la estructura de una hoja de examen a partir de una plantilla vacía, y luego utiliza esa estructura para evaluar exámenes rellenados, detectando las respuestas marcadas independientemente del color (usando umbralización adaptativa).

## Requisitos

* Python 3.x
* pip (gestor de paquetes de Python)

## Instalación

1.  **Clona o descarga este repositorio.**
2.  **Navega al directorio `Odin-ia/app`** en tu terminal o línea de comandos.
3.  **Instala las dependencias necesarias** usando pip:
    ```bash
    pip install Flask opencv-python numpy
    ```

## Estructura de Carpetas

Asegúrate de que tu proyecto tiene la siguiente estructura de carpetas:
Aquí tienes el contenido completo del archivo README.md listo para que lo copies y pegues.

Markdown

# Odin-IA: Evaluador de Exámenes de Opción Múltiple

Odin-IA es una aplicación web sencilla construida con Flask y OpenCV que permite la evaluación automática de hojas de examen de opción múltiple. El sistema funciona en dos fases: primero, "aprende" la estructura de una hoja de examen a partir de una plantilla vacía, y luego utiliza esa estructura para evaluar exámenes rellenados, detectando las respuestas marcadas independientemente del color (usando umbralización adaptativa).

## Requisitos

* Python 3.x
* pip (gestor de paquetes de Python)

## Instalación

1.  **Clona o descarga este repositorio.**
2.  **Navega al directorio `Odin-ia/app`** en tu terminal o línea de comandos.
3.  **Instala las dependencias necesarias** usando pip:
    ```bash
    pip install Flask opencv-python numpy
    ```

## Estructura de Carpetas

Asegúrate de que tu proyecto tiene la siguiente estructura de carpetas:

Odin-ia/
├── app/
│   ├── app.py                      # Lógica principal de la aplicación Flask
│   ├── config.py                   # Configuración de Flask
│   ├── templates/
│   │   ├── index.html              # Página principal para evaluación de exámenes
│   │   └── upload_template.html    # Página para subir hojas de plantilla
│   ├── static/
│   │   ├── img/                    # Aquí puedes guardar imágenes de ejemplo (opcional)
│   │   │   ├── 1.jpg
│   │   │   ├── circles.jpg
│   │   │   └── rectangles.jpg
│   │   └── json/
│   │       ├── coords.json         # Este archivo será generado/usado por la app (¡IMPORTANTE!)
│   │       └── results.json        # Este archivo almacena los últimos resultados
│   └── uploads/                    # <--- ¡CREA ESTA CARPETA SI NO EXISTE! Aquí se guardan temporalmente las imágenes subidas

**¡Importante!** Crea la carpeta `Odin-ia/app/uploads/` si no existe. La aplicación la usará para guardar temporalmente las imágenes subidas.

## Ejecución del Proyecto

1.  Abre tu terminal o línea de comandos.
2.  Navega hasta la carpeta `Odin-ia/app`:
    ```bash
    cd ruta/a/tu/carpeta/Odin-ia/app
    ```
3.  Ejecuta la aplicación Flask:
    ```bash
    python app.py
    ```
4.  Abre tu navegador web y ve a la dirección que te muestra la terminal (usualmente `http://127.0.0.1:5000/`).

## Flujo de Trabajo para la Evaluación de Exámenes

El proceso de evaluación consta de dos pasos principales:

### Paso 1: Generar Coordenadas de Plantilla (SÓLO una vez por cada formato de hoja)

Este paso es crucial para que el sistema "entienda" el diseño de tu hoja de examen. Debes realizarlo **una vez por cada nuevo formato de hoja** que quieras evaluar.

1.  **Prepara tu hoja de plantilla vacía:**
    * Utiliza una hoja de examen **completamente vacía** (sin ninguna marca de respuesta).
    * Asegúrate de que la hoja esté bien iluminada, sin sombras y con buen contraste.
    * Toma una foto o escanea la hoja con buena resolución. Los formatos JPG, JPEG, PNG, GIF son aceptados.

2.  **Sube la plantilla:**
    * En la página principal de la aplicación (`http://127.0.0.1:5000/`), haz clic en el enlace "Ir a Subir Plantilla".
    * Selecciona tu imagen de la plantilla vacía y haz clic en "Generar Coordenadas".

3.  **Verifica la Generación de Coordenadas:**
    * Si todo sale bien, verás un mensaje de "Coordenadas generadas y guardadas en coords.json exitosamente." y serás redirigido a la página principal.
    * Si aparece un error como "No se detectaron círculos" o "No se pudieron agrupar círculos en conjuntos de 4", significa que los parámetros de detección o agrupamiento en `app.py` no son los adecuados para tu plantilla. Consulta la sección **"Solución de Problemas: Ajuste de Parámetros"** a continuación.

Una vez que `coords.json` se haya generado con éxito para tu tipo de hoja, ya no necesitarás repetir este paso para ese mismo formato.

### Paso 2: Evaluar Hojas de Examen Rellenadas

Una vez que tengas el archivo `coords.json` generado para tu formato de hoja, puedes subir tus exámenes resueltos.

1.  **Prepara tu hoja de examen rellenada:**
    * Utiliza una hoja de examen del **mismo formato** que la plantilla utilizada en el Paso 1.
    * Asegúrate de que las marcas de respuesta sean claras. El sistema ahora es más robusto al color de la marca (lápiz, tinta negra/azul) gracias a la umbralización adaptativa.
    * La hoja debe estar bien iluminada y escaneada/fotografiada con buena calidad.

2.  **Sube el examen:**
    * En la página principal (`http://127.0.0.1:5000/`), en la sección "Paso 2: Evaluar Hoja de Examen", selecciona tu imagen de examen rellenado.
    * Haz clic en "Evaluar Hoja de Examen".

3.  **Visualiza los Resultados:**
    * El sistema procesará la imagen y mostrará los "Incisos Seleccionados" (las respuestas detectadas por pregunta) en la misma página.
    * Los resultados también se guardan en `app/static/json/results.json`.

## Solución de Problemas: Ajuste de Parámetros

Si encuentras errores o la detección no es precisa, especialmente durante el Paso 1 (Generar Coordenadas de Plantilla), necesitarás ajustar los parámetros en el archivo `app/app.py`. Los parámetros críticos están dentro de la función `generate_coords_from_empty_template`.

**Parámetros de `cv2.HoughCircles`:**

Controlan cómo se detectan los círculos (burbujas) en la imagen.

* `minDist`: Distancia mínima entre los centros de los círculos detectados. Si se detectan burbujas superpuestas o demasiados círculos falsos, aumenta este valor.
* `param2`: Umbral del acumulador para los centros de los círculos. Un valor **más bajo** detectará más círculos (incluso ruido), uno **más alto** detectará menos (solo los más claros). Si no detecta suficientes círculos, bájalo. Si detecta mucho ruido, súbelo.
* `minRadius` / `maxRadius`: Rango de tamaño (en píxeles) de los círculos que el algoritmo buscará. **Mide el radio aproximado de tus burbujas en la imagen y ajusta estos valores en consecuencia.** Si no detecta círculos, amplía este rango.

**Parámetros de Agrupamiento y Umbralización:**

Controlan cómo se organizan los círculos detectados en preguntas y cómo se detectan las marcas.

* `ROW_Y_TOLERANCE`: Tolerancia en el eje Y para considerar que las burbujas están en la misma fila de pregunta. Ajústalo si las filas de tus preguntas son muy irregulares o cercanas.
* `col_grouping_threshold` (valor `100` en el código): Umbral para agrupar rectángulos en columnas verticales. Si tienes varias columnas de preguntas, y el orden de los resultados es incorrecto, ajusta este valor.
* `cv2.adaptiveThreshold` (`blockSize`, `C`):
    * `blockSize` (ej. `11`): Tamaño de la vecindad de píxeles para calcular el umbral local. **Debe ser un número impar.** Ajusta según el tamaño de las marcas y la variación de iluminación.
    * `C` (ej. `2`): Constante que se resta de la media. Un valor más alto hace el umbral más estricto (solo marcas muy oscuras). Un valor más bajo lo hace más laxo (detecta marcas más claras).

**Proceso de Ajuste:**

1.  Cambia un parámetro a la vez en `app/app.py`.
2.  Guarda el archivo.
3.  Reinicia la aplicación Flask (`Ctrl+C` y `python app.py`).
4.  Sube tu imagen de plantilla vacía y observa el resultado.