from flask import Flask, render_template, request, redirect, url_for, flash
import pymongo
import os

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

@app.route('/')
def index():
    """Página principal - Lista todos los libros"""
    if libros is not None:
        todos_libros = list(libros.find())
        return render_template('index.html', libros=todos_libros)
    return "Error: No hay conexión a la base de datos"

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    """Agregar un nuevo libro"""
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            libro = {
                'id': request.form['id'],
                'titulo': request.form['titulo'],
                'cantidad_paginas': int(request.form['cantidad_paginas']),
                'editorial': request.form['editorial'],
                'isbn': request.form['isbn'],
                'costo_usd': float(request.form['costo_usd'])
            }
            
            # Verificar si el ID ya existe
            if libros.find_one({'id': libro['id']}) is not None:
                flash(f'Error: El ID {libro["id"]} ya existe', 'error')
            else:
                libros.insert_one(libro)
                flash('Libro agregado exitosamente', 'success')
                return redirect(url_for('index'))
                
        except ValueError:
            flash('Error: Verifica los tipos de datos (páginas y costo deben ser números)', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('agregar.html')

@app.route('/editar/<string:libro_id>', methods=['GET', 'POST'])
def editar(libro_id):
    """Editar un libro existente"""
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    libro = libros.find_one({'id': libro_id})
    
    if libro is None:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            nuevo_dato = {
                'titulo': request.form['titulo'],
                'cantidad_paginas': int(request.form['cantidad_paginas']),
                'editorial': request.form['editorial'],
                'isbn': request.form['isbn'],
                'costo_usd': float(request.form['costo_usd'])
            }
            
            # Verificar si el nuevo ID (si cambia) ya existe
            nuevo_id = request.form['id']
            if nuevo_id != libro_id:
                if libros.find_one({'id': nuevo_id}) is not None:
                    flash(f'Error: El ID {nuevo_id} ya existe', 'error')
                    return render_template('editar.html', libro=libro)
            
            libros.update_one(
                {'id': libro_id},
                {'$set': {**nuevo_dato, 'id': nuevo_id}}
            )
            flash('✅ Libro actualizado exitosamente', 'success')
            return redirect(url_for('index'))
            
        except ValueError:
            flash('Error: Verifica los tipos de datos', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('editar.html', libro=libro)

@app.route('/eliminar/<string:libro_id>')
def eliminar(libro_id):
    """Eliminar un libro"""
    if libros is None:
        flash('Error: No hay conexión a la base de datos', 'error')
        return redirect(url_for('index'))
    
    resultado = libros.delete_one({'id': libro_id})
    if resultado.deleted_count > 0:
        flash('Libro eliminado exitosamente', 'success')
    else:
        flash('Libro no encontrado', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)