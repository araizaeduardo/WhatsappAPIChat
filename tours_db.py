"""
Base de datos de tours y paquetes turísticos usando SQLite.
"""

import sqlite3
import json
import os

# Ruta a la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'tours.db')

# Tours iniciales para cargar en la base de datos si está vacía
INITIAL_TOURS = [
    {
        "id": "T001",
        "name": "Tour por Cancún",
        "description": "Disfruta de las hermosas playas de Cancún con este paquete todo incluido.",
        "duration": "7 días / 6 noches",
        "price": 12500,
        "currency": "MXN",
        "includes": ["Hotel 5 estrellas", "Desayunos", "Traslados", "Tour a Chichen Itzá"],
        "location": "Cancún, México",
        "availability": "Todo el año",
        "tags": ["playa", "caribe", "méxico", "cancún", "todo incluido"]
    },
    {
        "id": "T002",
        "name": "Aventura en Los Cabos",
        "description": "Experimenta la emoción de Los Cabos con actividades acuáticas y paisajes impresionantes.",
        "duration": "5 días / 4 noches",
        "price": 9800,
        "currency": "MXN",
        "includes": ["Hotel 4 estrellas", "Desayunos", "Tour en catamárán", "Snorkel"],
        "location": "Los Cabos, México",
        "availability": "Todo el año",
        "tags": ["playa", "pacífico", "méxico", "los cabos", "aventura"]
    },
    {
        "id": "T003",
        "name": "Ciudad de México Cultural",
        "description": "Conoce la riqueza cultural e histórica de la Ciudad de México.",
        "duration": "4 días / 3 noches",
        "price": 5600,
        "currency": "MXN",
        "includes": ["Hotel céntrico", "Desayunos", "Tour por el Centro Histórico", "Visita a Teotihuacán"],
        "location": "Ciudad de México, México",
        "availability": "Todo el año",
        "tags": ["ciudad", "cultura", "méxico", "cdmx", "historia", "arqueología"]
    },
    {
        "id": "T004",
        "name": "Maravillas de Oaxaca",
        "description": "Descubre la magia, tradiciones y gastronomía de Oaxaca.",
        "duration": "6 días / 5 noches",
        "price": 7800,
        "currency": "MXN",
        "includes": ["Hotel boutique", "Desayunos", "Tour gastronómico", "Visita a Monte Albán"],
        "location": "Oaxaca, México",
        "availability": "Todo el año",
        "tags": ["cultura", "gastronomía", "méxico", "oaxaca", "artesanías"]
    },
    {
        "id": "T005",
        "name": "Riviera Maya Todo Incluido",
        "description": "Relájate en las paradisíacas playas de la Riviera Maya con todo incluido.",
        "duration": "7 días / 6 noches",
        "price": 15200,
        "currency": "MXN",
        "includes": ["Resort 5 estrellas", "Todo incluido", "Acceso a parques Xcaret", "Cenotes"],
        "location": "Riviera Maya, México",
        "availability": "Todo el año",
        "tags": ["playa", "caribe", "méxico", "riviera maya", "todo incluido", "xcaret"]
    }
]

def init_db():
    """
    Inicializa la base de datos y crea las tablas necesarias si no existen.
    """
    # Verificar si el archivo de base de datos existe
    db_exists = os.path.exists(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de tours si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tours (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        duration TEXT NOT NULL,
        price REAL NOT NULL,
        currency TEXT NOT NULL,
        includes TEXT NOT NULL,
        location TEXT NOT NULL,
        availability TEXT NOT NULL,
        tags TEXT NOT NULL
    )
    ''')
    
    # Si la base de datos no existía o la tabla está vacía, cargar los tours iniciales
    cursor.execute('SELECT COUNT(*) FROM tours')
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Cargando tours iniciales en la base de datos...")
        for tour in INITIAL_TOURS:
            cursor.execute('''
            INSERT INTO tours (id, name, description, duration, price, currency, includes, location, availability, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tour['id'],
                tour['name'],
                tour['description'],
                tour['duration'],
                tour['price'],
                tour['currency'],
                json.dumps(tour['includes']),
                tour['location'],
                tour['availability'],
                json.dumps(tour['tags'])
            ))
            print(f"Tour añadido: {tour['name']}")
    
    conn.commit()
    conn.close()
    
    # Verificar si la inicialización fue exitosa
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tours')
    count = cursor.fetchone()[0]
    print(f"Total de tours en la base de datos: {count}")
    conn.close()

# Inicializar la base de datos al importar el módulo
init_db()

def get_all_tours():
    """
    Obtiene todos los tours disponibles.
    
    Returns:
        list: Lista de todos los tours
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tours')
    tours_data = cursor.fetchall()
    
    tours = []
    for tour in tours_data:
        # Convertir el objeto Row a un diccionario para acceder por nombre de columna
        tour_dict = dict(tour)
        tours.append({
            'id': tour_dict['id'],
            'name': tour_dict['name'],
            'description': tour_dict['description'],
            'duration': tour_dict['duration'],
            'price': tour_dict['price'],
            'currency': tour_dict['currency'],
            'includes': json.loads(tour_dict['includes']),
            'location': tour_dict['location'],
            'availability': tour_dict['availability'],
            'tags': json.loads(tour_dict['tags'])
        })
    
    conn.close()
    return tours

def search_tours(query):
    """
    Busca tours que coincidan con la consulta.
    
    Args:
        query (str): Consulta de búsqueda
        
    Returns:
        list: Lista de tours que coinciden con la consulta
    """
    query = query.lower()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar en nombre, descripción y ubicación usando LIKE
    cursor.execute('''
    SELECT * FROM tours WHERE 
    LOWER(name) LIKE ? OR 
    LOWER(description) LIKE ? OR 
    LOWER(location) LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    tours_data = cursor.fetchall()
    results = []
    
    for tour in tours_data:
        # Convertir el objeto Row a un diccionario para acceder por nombre de columna
        tour_row = dict(tour)
        # Convertir a diccionario
        tour_dict = {
            'id': tour_row['id'],
            'name': tour_row['name'],
            'description': tour_row['description'],
            'duration': tour_row['duration'],
            'price': tour_row['price'],
            'currency': tour_row['currency'],
            'includes': json.loads(tour_row['includes']),
            'location': tour_row['location'],
            'availability': tour_row['availability'],
            'tags': json.loads(tour_row['tags'])
        }
        
        # Verificar también en las etiquetas (ya que están almacenadas como JSON)
        tags = tour_dict['tags']
        if any(query in tag.lower() for tag in tags):
            # Si aún no está en los resultados, añadirlo
            if not any(r['id'] == tour_dict['id'] for r in results):
                results.append(tour_dict)
        else:
            # Si ya está en los resultados por la búsqueda SQL, no hacer nada
            # Si no está en los resultados, verificar si debería estar
            if not any(r['id'] == tour_dict['id'] for r in results):
                results.append(tour_dict)
    
    conn.close()
    return results

def get_tour_by_id(tour_id):
    """
    Obtiene un tour por su ID.
    
    Args:
        tour_id (str): ID del tour
        
    Returns:
        dict: Tour encontrado o None si no existe
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tours WHERE id = ?', (tour_id,))
    tour = cursor.fetchone()
    
    if tour:
        # Convertir el objeto Row a un diccionario para acceder por nombre de columna
        tour_row = dict(tour)
        tour_dict = {
            'id': tour_row['id'],
            'name': tour_row['name'],
            'description': tour_row['description'],
            'duration': tour_row['duration'],
            'price': tour_row['price'],
            'currency': tour_row['currency'],
            'includes': json.loads(tour_row['includes']),
            'location': tour_row['location'],
            'availability': tour_row['availability'],
            'tags': json.loads(tour_row['tags'])
        }
        conn.close()
        return tour_dict
    
    conn.close()
    return None

def format_tour_info(tour):
    """
    Formatea la información de un tour para mostrarla en un mensaje.
    
    Args:
        tour (dict): Información del tour
        
    Returns:
        str: Mensaje formateado
    """
    includes = "\n".join([f"  - {item}" for item in tour["includes"]])
    
    return (
        f"*{tour['name']}*\n\n"
        f"{tour['description']}\n\n"
        f"📅 *Duración:* {tour['duration']}\n"
        f"📍 *Ubicación:* {tour['location']}\n"
        f"💰 *Precio:* ${tour['price']} {tour['currency']}\n"
        f"📅 *Disponibilidad:* {tour['availability']}\n\n"
        f"✅ *Incluye:*\n{includes}\n\n"
        f"🔍 *ID del tour:* {tour['id']}\n\n"
        f"Para reservar este tour, responde con 'reservar {tour['id']}'"
    )

# Funciones CRUD para el panel de administración

def add_tour(tour_data):
    """
    Añade un nuevo tour a la base de datos.
    
    Args:
        tour_data (dict): Datos del tour a añadir
        
    Returns:
        bool: True si se añadió correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Generar un nuevo ID si no se proporciona
        if 'id' not in tour_data or not tour_data['id']:
            # Obtener el último ID y generar uno nuevo
            cursor.execute('SELECT id FROM tours ORDER BY id DESC LIMIT 1')
            last_id = cursor.fetchone()
            if last_id:
                # Extraer el número y aumentarlo en 1
                num = int(last_id[0][1:]) + 1
                tour_data['id'] = f"T{num:03d}"
            else:
                tour_data['id'] = "T001"
        
        cursor.execute('''
        INSERT INTO tours (id, name, description, duration, price, currency, includes, location, availability, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tour_data['id'],
            tour_data['name'],
            tour_data['description'],
            tour_data['duration'],
            tour_data['price'],
            tour_data['currency'],
            json.dumps(tour_data['includes']),
            tour_data['location'],
            tour_data['availability'],
            json.dumps(tour_data['tags'])
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al añadir tour: {str(e)}")
        return False

def update_tour(tour_id, tour_data):
    """
    Actualiza un tour existente en la base de datos.
    
    Args:
        tour_id (str): ID del tour a actualizar
        tour_data (dict): Nuevos datos del tour
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE tours SET 
            name = ?,
            description = ?,
            duration = ?,
            price = ?,
            currency = ?,
            includes = ?,
            location = ?,
            availability = ?,
            tags = ?
        WHERE id = ?
        ''', (
            tour_data['name'],
            tour_data['description'],
            tour_data['duration'],
            tour_data['price'],
            tour_data['currency'],
            json.dumps(tour_data['includes']),
            tour_data['location'],
            tour_data['availability'],
            json.dumps(tour_data['tags']),
            tour_id
        ))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar tour: {str(e)}")
        return False

def delete_tour(tour_id):
    """
    Elimina un tour de la base de datos.
    
    Args:
        tour_id (str): ID del tour a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tours WHERE id = ?', (tour_id,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar tour: {str(e)}")
        return False
