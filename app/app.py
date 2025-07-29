from flask import Flask, render_template, request, redirect, url_for, flash
from config import config
import cv2
import numpy as np
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui' # ¡IMPORTANTE! Cambia esto por una clave secreta real y segura

UPLOAD_FOLDER = 'app/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para detectar coordenadas de una plantilla vacía con agrupamiento adaptativo
def generate_coords_from_empty_template(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Error al cargar la imagen para detección de coordenadas."

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # --- PARÁMETROS DE HoughCircles: Estos son un buen punto de partida, pero pueden necesitar ajuste fino ---
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,     
        minDist=15, 
        param1=50,  
        param2=20,  
        minRadius=5, 
        maxRadius=20 
    )

    if circles is None or len(circles[0]) < 10: 
        return None, f"Se detectaron muy pocos círculos ({0 if circles is None else len(circles[0])}). Ajusta minRadius, maxRadius o param2 de HoughCircles."

    circles = np.uint16(np.around(circles[0]))

    # Paso 1: Agrupar círculos por "fila" (tolerancia en Y)
    circles_sorted_by_y = sorted(circles, key=lambda c: c[1]) 

    rows_of_circles = []
    current_row = []
    
    ROW_Y_TOLERANCE = 15 

    if circles_sorted_by_y:
        current_row.append(circles_sorted_by_y[0])
        for i in range(1, len(circles_sorted_by_y)):
            if abs(circles_sorted_by_y[i][1] - current_row[-1][1]) < ROW_Y_TOLERANCE:
                current_row.append(circles_sorted_by_y[i])
            else:
                rows_of_circles.append(current_row)
                current_row = [circles_sorted_by_y[i]]
        rows_of_circles.append(current_row) 

    rectangles_coor = []

    # Paso 2: Dentro de cada fila, agrupar círculos en conjuntos de 4 (A,B,C,D) dinámicamente
    for row in rows_of_circles:
        row_sorted_by_x = sorted(row, key=lambda c: c[0]) 

        if len(row_sorted_by_x) < 4: 
            continue

        x_distances = []
        for i in range(len(row_sorted_by_x) - 1):
            x_distances.append(row_sorted_by_x[i+1][0] - row_sorted_by_x[i][0])
        
        filtered_x_distances = [d for d in x_distances if d < 2 * np.median(x_distances) if np.median(x_distances) > 0]
        
        if not filtered_x_distances: 
            continue

        avg_x_distance = np.median(filtered_x_distances) 
        
        GROUP_X_TOLERANCE_FACTOR = 1.5 

        current_group_of_4 = []
        for i in range(len(row_sorted_by_x)):
            if not current_group_of_4:
                current_group_of_4.append(row_sorted_by_x[i])
            else:
                last_in_group_x = current_group_of_4[-1][0]
                current_circle_x = row_sorted_by_x[i][0]

                if (current_circle_x - last_in_group_x) < (avg_x_distance * GROUP_X_TOLERANCE_FACTOR):
                    current_group_of_4.append(row_sorted_by_x[i])
                else:
                    if len(current_group_of_4) == 4:
                        rectangles_coor.append(current_group_of_4) 
                    current_group_of_4 = [row_sorted_by_x[i]] 

        if len(current_group_of_4) == 4:
            rectangles_coor.append(current_group_of_4)


    final_rectangles = []
    if not rectangles_coor:
        return None, "No se pudieron agrupar círculos en conjuntos de 4 para formar preguntas. Revisa la calidad de tu plantilla o ajusta ROW_Y_TOLERANCE."

    for group_of_4_circles in rectangles_coor:
        xs = [c[0] for c in group_of_4_circles]
        ys = [c[1] for c in group_of_4_circles]
        rs = [c[2] for c in group_of_4_circles]

        min_x_group = min(xs)
        max_x_group = max(xs)
        min_y_group = min(ys)
        max_y_group = max(ys)
        max_r_group = max(rs)

        x1 = max(0, min_x_group - max_r_group - 5) 
        y1 = max(0, min_y_group - max_r_group - 5)
        x2 = min(img.shape[1], max_x_group + max_r_group + 5)
        y2 = min(img.shape[0], max_y_group + max_r_group + 5)

        if x2 > x1 and y2 > y1:
            final_rectangles.append({
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2)
            })

    def sort_rects(rects):
        col_groups = {}
        col_grouping_threshold = 100 
        for r in rects:
            col_key = round(r['x1'] / col_grouping_threshold) * col_grouping_threshold
            if col_key not in col_groups:
                col_groups[col_key] = []
            col_groups[col_key].append(r)
        
        sorted_rects = []
        for key in sorted(col_groups.keys()):
            sorted_rects.extend(sorted(col_groups[key], key=lambda r: r['y1']))
        return sorted_rects

    final_rectangles = sort_rects(final_rectangles)

    if len(final_rectangles) > 0:
        return final_rectangles, None
    else:
        return None, "No se pudieron generar coordenadas finales de rectángulos. Esto puede ser debido a fallas en el agrupamiento o cálculos."

@app.route('/upload_empty_template', methods=['GET', 'POST'])
def upload_empty_template():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nombre de archivo vacío.', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            coords_generated, error_msg = generate_coords_from_empty_template(filepath)
            os.remove(filepath)

            if coords_generated:
                coords_file_path = 'app/static/json/coords.json'
                os.makedirs(os.path.dirname(coords_file_path), exist_ok=True)
                with open(coords_file_path, 'w') as f:
                    json.dump(coords_generated, f)
                flash('Coordenadas generadas y guardadas en coords.json exitosamente.', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error al generar coordenadas de plantilla vacía: {error_msg}', 'error')
                return redirect(request.url)
    return render_template('upload_template.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    results_file_path = 'app/static/json/results.json'
    os.makedirs(os.path.dirname(results_file_path), exist_ok=True)

    if not os.path.exists(results_file_path):
        with open(results_file_path, 'w') as f:
            json.dump([], f)

    coords_file_path = 'app/static/json/coords.json'
    if not os.path.exists(coords_file_path):
        flash('Error: No se encontró el archivo de coordenadas (coords.json). Por favor, sube una hoja de plantilla vacía primero para generarlo.', 'error')
        current_results = []
        try:
            with open(results_file_path, 'r') as f:
                current_results = json.load(f)
        except json.JSONDecodeError:
            pass
        return render_template('index.html', results=current_results)

    try:
        with open(coords_file_path, 'r') as f:
            coords = json.load(f)
    except json.JSONDecodeError:
        flash('Error: El archivo coords.json está corrupto. Por favor, genera uno nuevo con una plantilla vacía.', 'error')
        coords = []
        current_results = []
        return render_template('index.html', results=current_results)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo de examen.', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nombre de archivo vacío.', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            img_to_process = cv2.imread(filepath)
            if img_to_process is None:
                os.remove(filepath)
                flash('Error al cargar la imagen del examen. Asegúrate de que es una imagen válida.', 'error')
                return redirect(request.url)

            for i, coord in enumerate(coords, start=1):
                x1 = int(coord['x1'])
                y1 = int(coord['y1'])
                x2 = int(coord['x2'])
                y2 = int(coord['y2'])

                if y1 >= img_to_process.shape[0] or y2 > img_to_process.shape[0] or x1 >= img_to_process.shape[1] or x2 > img_to_process.shape[1] or \
                   y1 < 0 or y2 < 0 or x1 < 0 or x2 < 0 or y1 >= y2 or x1 >= x2:
                    print(f"Coordenadas inválidas para la pregunta {i}: {coord}")
                    results.append({'pregunta': i, 'respuesta': 'Error/Fuera de rango'})
                    continue

                cut = img_to_process[y1:y2, x1:x2]
                if cut.shape[0] == 0 or cut.shape[1] == 0:
                    print(f"Recorte vacío para la pregunta {i}: {coord}")
                    results.append({'pregunta': i, 'respuesta': 'Error/Recorte Vacío'})
                    continue

                h, w = cut.shape[:2]
                if w < 4:
                    print(f"Ancho de recorte insuficiente para pregunta {i}")
                    results.append({'pregunta': i, 'respuesta': 'Error/Ancho insuficiente'})
                    continue

                sub_cuts = [
                    ('A', cut[:, 0:w//4]),
                    ('B', cut[:, w//4:w//2]),
                    ('C', cut[:, w//2:(3*w)//4]),
                    ('D', cut[:, (3*w)//4:w])
                ]
                max_marked_rate = 0 
                selection = None

                for label, sub in sub_cuts:
                    if sub.shape[0] == 0 or sub.shape[1] == 0:
                        continue
                    
                    gray_sub = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
                    
                    # --- CAMBIO CLAVE AQUÍ: Umbralización adaptativa para detectar marcas de color independiente ---
                    # cv2.ADAPTIVE_THRESH_GAUSSIAN_C: Calcula el umbral como la media ponderada de los vecinos.
                    # blockSize: Tamaño de la vecindad. Debe ser impar. Ajusta según el tamaño de la burbuja y la calidad de la imagen.
                    # C: Constante que se resta de la media. Ajusta para hacer el umbral más o menos estricto.
                    thresholded = cv2.adaptiveThreshold(
                        gray_sub, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2 # <-- AJUSTA blockSize (ej. 11, 13, 15) y C (ej. 2, 3, 5)
                    ) 
                    
                    marked_pixels = cv2.countNonZero(thresholded)
                    total_pixels = sub.shape[0] * sub.shape[1]
                    
                    if total_pixels == 0: 
                        marked_rate = 0
                    else:
                        marked_rate = marked_pixels / total_pixels

                    if marked_rate > max_marked_rate:
                        max_marked_rate = marked_rate
                        selection = label

                # --- Umbral de detección de respuesta (0.05 es un buen punto de partida) ---
                if selection is not None and max_marked_rate > 0.05:
                    results.append({'pregunta': i, 'respuesta': selection})
                else:
                    results.append({'pregunta': i, 'respuesta': 'None'})

            with open(results_file_path, 'w') as f:
                json.dump(results, f)

            os.remove(filepath)
            flash('Examen evaluado exitosamente.', 'success')
            return redirect(url_for('index', _anchor='results'))

    current_results = []
    try:
        with open(results_file_path, 'r') as f:
            current_results = json.load(f)
    except json.JSONDecodeError:
        pass
    
    return render_template('index.html', results=current_results)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)