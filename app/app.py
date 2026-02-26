from flask import Flask, render_template, request, redirect, url_for, flash
import pymongo
import os
import re
import isbnlib

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Conexión a MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:password@mongodb:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'biblioteca')

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    libros = db['libros']
    print("Conectado a MongoDB")
except Exception as e:
    print(f"Error conectando a MongoDB: {e}")
    libros = None

# Funciones de validacion --------------------------

def validar_id(id_str):
    id_str = id_str.strip()
    if not id_str:
        return False, "El ID no puede estar vacío"

    try:
        id = int(id_str)
        
        if id <= 0:
            return False, "El ID debe ser mayor a 0"
        
        return True, id
    except ValueError:
        return False, "El ID debe ser un número entero"

def validar_titulo(titulo):
    titulo = titulo.strip()
    if not titulo:
        return False, "El título no puede estar vacio"
    
    return True, titulo

def validar_paginas(paginas_str):
    paginas_str = paginas_str.strip()
    if not paginas_str:
        return False, "La cantidad de páginas no puede estar vacía"
    
    try:
        paginas = int(paginas_str)
        
        if paginas <= 0:
            return False, "La cantidad de páginas debe ser mayor a 0"
        
        return True, paginas
    except ValueError:
        return False, "La cantidad de páginas debe ser un número entero"

def validar_editorial(editorial):
    editorial = editorial.strip()
    if not editorial:
        return True, "La editorial no puede estar vacia"
    
    return True, editorial

def validar_isbn(isbn):
    isbn = isbn.strip()
    if not isbn:
        return True, "El ISBN no puede estar vacio"
    
    isbn = isbn.replace('-', '').replace(' ', '').replace('.', '')  # Limpiar guiones, espacios o puntos
    
    # Validar solo caracteres permitidos (dígitos y X)
    if not re.match(r'^[0-9X]+$', isbn):
        return False, "El ISBN solo puede contener números y la letra X (en ISBN-10)"
    
    # Validar con isbnlib
    if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn):
        return True, isbn
    else:
        return False, "El ISBN no es válido (debe ser ISBN-10 o ISBN-13)"

def validar_costo(costo_str):
    costo_str = costo_str.strip()
    if not costo_str:
        return False, "El costo no puede estar vacío"
    
    try:
        costo = float(costo_str)
        
        if costo < 0:
            return False, "El costo no puede ser negativo"
        costo = round(costo, 2)
        
        return True, costo
    except ValueError:
        return False, "El costo debe ser un número válido (ej: 29.99)"

def validaciones(datos):
    # Valida los campos y devuelve diccionario con datos limpios o errores

    errores = []
    datos_limpios = {}
    
    # ID
    valido, resultado = validar_id(datos.get('id', ''))
    if not valido:
        errores.append(f"ID: {resultado}")
    else:
        datos_limpios['id'] = resultado
    
    # Titulo
    valido, resultado = validar_titulo(datos.get('titulo', ''))
    if not valido:
        errores.append(f"Título: {resultado}")
    else:
        datos_limpios['titulo'] = resultado
    
    # Paginas
    valido, resultado = validar_paginas(datos.get('cantidad_paginas', ''))
    if not valido:
        errores.append(f"Páginas: {resultado}")
    else:
        datos_limpios['cantidad_paginas'] = resultado
    
    # Editorial
    valido, resultado = validar_editorial(datos.get('editorial', ''))
    if not valido:
        errores.append(f"Editorial: {resultado}")
    else:
        datos_limpios['editorial'] = resultado
    
    # ISBN
    valido, resultado = validar_isbn(datos.get('isbn', ''))
    if not valido:
        errores.append(f"ISBN: {resultado}")
    else:
        datos_limpios['isbn'] = resultado
    
    # Costo
    valido, resultado = validar_costo(datos.get('costo_usd', ''))
    if not valido:
        errores.append(f"Costo: {resultado}")
    else:
        datos_limpios['costo_usd'] = resultado
    
    return errores, datos_limpios

# Rutas de la aplicacion --------------------------------

@app.route('/')
def index():
    if libros is not None:
        todos_libros = list(libros.find())
        
        # Verificar si hay mensaje de alerta en la URL
        alerta = request.args.get('alerta', '')
        mensaje = request.args.get('mensaje', '')
        
        return render_template('index.html', 
                             libros=todos_libros,
                             alerta=alerta,
                             mensaje=mensaje)
    return "Error: No hay conexión a la base de datos"

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Validaciones
        errores, datos_limpios = validaciones(request.form)
        
        if errores:
            # Mostrar los errores
            for error in errores:
                flash(f'{error}', 'error')
            return render_template('agregar.html', datos_previos=request.form)
        
        # Verificar si el ID ya existe
        if libros.find_one({'id': datos_limpios['id']}) is not None:
            flash(f'Error: El ID {datos_limpios["id"]} ya existe', 'error')
            return render_template('agregar.html', datos_previos=request.form)
        
        # Verificar si el ISBN ya esta cargado
        if libros.find_one({'isbn': datos_limpios['isbn']}) is not None:
            flash(f'Error: El ISBN {datos_limpios["isbn"]} ya esta cargado', 'error')
            return render_template('agregar.html', datos_previos=request.form)
        
        # Insertar libro con datos limpios
        try:
            libros.insert_one(datos_limpios)
            return redirect(url_for('index', 
                                  alerta='success', 
                                  mensaje='Libro agregado exitosamente'))
        except Exception as e:
            flash(f'Error al guardar: {str(e)}', 'error')
            return render_template('agregar.html', datos_previos=request.form)
    
    return render_template('agregar.html')

@app.route('/editar/<string:libro_id>', methods=['GET', 'POST'])
def editar(libro_id):
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    libro = libros.find_one({'id': int(libro_id)})
    
    if libro is None:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Validaciones
        errores, datos_limpios = validaciones(request.form)
        
        if errores:
            # Mostrar los errores
            for error in errores:
                flash(f'{error}', 'error')
            return render_template('editar.html', libro=libro, datos_previos=request.form)

        # Verificar si el nuevo ID (si cambio) ya existe
        nuevo_id = datos_limpios['id']
        if nuevo_id != int(libro_id):
            if libros.find_one({'id': nuevo_id}) is not None:
                flash(f'Error: El ID {nuevo_id} ya existe', 'error')
                return render_template('editar.html', libro=libro, datos_previos=request.form)
        
        # Actualizar libro
        try:
            libros.update_one(
                {'id': int(libro_id)},
                {'$set': datos_limpios}
            )
            return redirect(url_for('index',
                                  alerta='success', 
                                  mensaje='Libro actualizado exitosamente'))
        except Exception as e:
            flash(f'Error al actualizar: {str(e)}', 'error')
            return render_template('editar.html', libro=libro, datos_previos=request.form)
    
    return render_template('editar.html', libro=libro)

@app.route('/eliminar/<string:libro_id>')
def eliminar(libro_id):
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    resultado = libros.delete_one({'id': int(libro_id)})
    if resultado.deleted_count > 0:
        return redirect(url_for('index', 
                              alerta='success', 
                              mensaje='Libro eliminado'))
    else:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)