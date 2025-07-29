from flask import Flask, render_template, request
from config import config 
import cv2
import numpy as np 
import json 

app = Flask(__name__)
ruta_i_64 = ('app/static/img/1.jpg')




@app.route('/')
def index(): 
    
    #parte 1: dibujar circulos para detectar donde iran los cuadrados, para esto
    #se uso una imagen donde estan marcadas todas las (a) en la hoja de respuestas
    img = cv2.imread(ruta_i_64)
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(
        gray, 
        cv2.HOUGH_GRADIENT, 
        dp=1, 
        minDist=20, 
        param1=20, 
        param2=25, 
        minRadius=5, 
        maxRadius=15)        
    
    circles_blue = []
    # variable donde se guardan las coordenadas de los rectangulos
    rectangles_coor = []

    if circles is not None:
        circles = np.uint16(np.around(circles[0]))
        for x,y,r in circles:
            cut = img[y-r:y+r, x-r:x+r]
            if cut.shape[0] == 0 or cut.shape[1] == 0:
                continue
            
            
            hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)
            low_blue = (90, 50, 50)
            up_blue = (140, 255, 255)
            mask = cv2.inRange(hsv, low_blue, up_blue)
            blue_rate = cv2.countNonZero(mask)/(cut.shape[0]*cut.shape[1])
                
            if blue_rate > 0.2:
                circles_blue.append((x, y, r))
                cv2.circle(img, (x, y), r, (0, 0, 255), 2)  # rojo BGR  
                cv2.imwrite('app/static/img/circles.jpg', img)
                #parte 2: aqui se guardan las coordenadas por primera vez de los incisos (a) para ubicar los rectangulos manualmente
        
                  #coordenadas para los rectangulos, solo se uso una vez para dibujar los rectangulos
                x1 = int(x - r - 7)
                y1 = int(y - r - 2)
                x2 = int(x + r + 110)
                y2 = int(y + r + 2)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
                rectangles_coor.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
            
                continue
            
                    #dibujar los rectangulos desde las coordenadas guardadas anteriormente
            with open ('app/static/json/coords.json', 'r') as f:
                coords = json.load(f)
                for coord in coords:
                    x1 = int(coord['x1'])
                    y1 = int(coord['y1'])   
                    x2 = int(coord['x2'])
                    y2 = int(coord['y2'])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
                    cv2.imwrite('app/static/img/rectangles.jpg', img)
               
        # se aplica un sort para guardar las coordenadas en orden
        #esto solamente se usa una vez para ordenar y guardar las coordenadas de los rectangulos
        def sort_by_column_y(rects):
            def x_group(x): return round(x / 10) * 10
            return sorted(rects, key=lambda r: (x_group(r['x1']), r['y1']))
        rectangles_coor = sort_by_column_y(rectangles_coor)
        
            # aqui se guardan las coordenadas de los rectangulos en un archivo json
        with open('app/static/json/coords.json', 'w') as f:
            json.dump(rectangles_coor, f)
            
            # Dibujar los rectángulos ordenados
        for coord in rectangles_coor:
            x1 = int(coord['x1'])
            y1 = int(coord['y1'])   
            x2 = int(coord['x2'])
            y2 = int(coord['y2'])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.imwrite('app/static/img/rectangles.jpg', img)
    '''
    
    #parte 3: 
    
    results = []
    with open ('app/static/json/coords.json', 'r') as f:
            coords = json.load(f)
    for i, coord in enumerate(coords, start=1):
        x1 = int(coord['x1'])
        y1 = int(coord['y1'])   
        x2 = int(coord['x2'])
        y2 = int(coord['y2'])
                
        cut = img[y1:y2, x1:x2]
        h, w = cut.shape[:2]
        
        sub_cuts = [
            ('A', cut[:, 0:w//4]),               # Primer cuarto (izquierda)
            ('B', cut[:, w//4:w//2]),            # Segundo cuarto
            ('C', cut[:, w//2:(3*w)//4]),        # Tercer cuarto
            ('D', cut[:, (3*w)//4:w])            # Último cuarto (derecha)
        ]   
        max_blue = 0
        selection = None
        
        for label, sub in sub_cuts:
            hsv = cv2.cvtColor(sub, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, (90, 50, 50), (140, 255, 255))
            blue_rate = cv2.countNonZero(mask) / (sub.shape[0]*sub.shape[1])
            
            if blue_rate > max_blue:
                max_blue = blue_rate
                selection = label
            
        if selection is not None:
            results.append({'pregunta': i, 'respuesta': selection})
        else:
            results.append({'pregunta': i, 'respuesta': 'None'})
                
    with open('app/static/json/results.json', 'w') as f:
        json.dump(results, f)
    
    return  results

if __name__ == '__main__':
    app.run(debug=True) 