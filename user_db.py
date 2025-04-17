"""
Módulo para gestionar usuarios y autenticación.
"""

import sqlite3
import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta

# Ruta a la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    """
    Inicializa la base de datos de usuarios y crea las tablas necesarias si no existen.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de usuarios si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # Crear tabla de sesiones si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Verificar si hay algún usuario administrador
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    count = cursor.fetchone()[0]
    
    # Si no hay usuarios administradores, crear uno por defecto
    if count == 0:
        # Crear un usuario administrador por defecto
        create_user(
            username="admin",
            password="admin123",  # Esta contraseña debe cambiarse después del primer inicio de sesión
            email="admin@example.com",
            role="admin"
        )
        print("Usuario administrador creado con éxito.")
        print("Usuario: admin")
        print("Contraseña: admin123")
        print("¡IMPORTANTE! Cambie esta contraseña después del primer inicio de sesión.")
    
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    """
    Genera un hash seguro para la contraseña utilizando PBKDF2.
    
    Args:
        password (str): Contraseña a hashear
        salt (str, optional): Salt para el hash. Si no se proporciona, se genera uno nuevo.
        
    Returns:
        tuple: (password_hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Usar PBKDF2 con SHA-256, 100,000 iteraciones
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    
    return key, salt

def create_user(username, password, email, role="user"):
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano
        email (str): Correo electrónico
        role (str, optional): Rol del usuario (admin, staff, user)
        
    Returns:
        int: ID del usuario creado o None si hubo un error
    """
    try:
        # Generar hash y salt para la contraseña
        password_hash, salt = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insertar el nuevo usuario
        cursor.execute('''
        INSERT INTO users (username, password_hash, salt, email, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            username,
            password_hash,
            salt,
            email,
            role,
            datetime.now().isoformat()
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    except Exception as e:
        print(f"Error al crear usuario: {str(e)}")
        return None

def verify_user(username, password):
    """
    Verifica las credenciales de un usuario.
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano
        
    Returns:
        dict: Datos del usuario si las credenciales son correctas, None en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar el usuario por nombre de usuario
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        user = cursor.fetchone()
        
        if user:
            # Convertir a diccionario
            user_dict = dict(user)
            
            # Verificar la contraseña
            password_hash, _ = hash_password(password, user_dict['salt'])
            
            if password_hash == user_dict['password_hash']:
                # Actualizar último inicio de sesión
                cursor.execute(
                    'UPDATE users SET last_login = ? WHERE id = ?',
                    (datetime.now().isoformat(), user_dict['id'])
                )
                conn.commit()
                
                # Eliminar campos sensibles
                user_dict.pop('password_hash', None)
                user_dict.pop('salt', None)
                
                conn.close()
                return user_dict
        
        conn.close()
        return None
    except Exception as e:
        print(f"Error al verificar usuario: {str(e)}")
        return None

def create_session(user_id, ip_address=None, user_agent=None):
    """
    Crea una nueva sesión para un usuario.
    
    Args:
        user_id (int): ID del usuario
        ip_address (str, optional): Dirección IP del cliente
        user_agent (str, optional): User-Agent del cliente
        
    Returns:
        str: Token de sesión o None si hubo un error
    """
    try:
        # Generar token de sesión
        session_token = secrets.token_hex(32)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Establecer fechas de creación y expiración
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=1)  # La sesión expira en 1 día
        
        # Insertar la nueva sesión
        cursor.execute('''
        INSERT INTO sessions (user_id, session_token, created_at, expires_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            session_token,
            created_at.isoformat(),
            expires_at.isoformat(),
            ip_address,
            user_agent
        ))
        
        conn.commit()
        conn.close()
        
        return session_token
    except Exception as e:
        print(f"Error al crear sesión: {str(e)}")
        return None

def verify_session(session_token):
    """
    Verifica si una sesión es válida y no ha expirado.
    
    Args:
        session_token (str): Token de sesión
        
    Returns:
        dict: Datos del usuario si la sesión es válida, None en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar la sesión
        cursor.execute('''
        SELECT s.*, u.* FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ? AND u.is_active = 1
        ''', (session_token,))
        
        result = cursor.fetchone()
        
        if result:
            # Convertir a diccionario
            session_data = dict(result)
            
            # Verificar si la sesión ha expirado
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            
            if expires_at > datetime.now():
                # Eliminar campos sensibles
                session_data.pop('password_hash', None)
                session_data.pop('salt', None)
                
                conn.close()
                return session_data
            else:
                # La sesión ha expirado, eliminarla
                cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
                conn.commit()
        
        conn.close()
        return None
    except Exception as e:
        print(f"Error al verificar sesión: {str(e)}")
        return None

def invalidate_session(session_token):
    """
    Invalida una sesión (logout).
    
    Args:
        session_token (str): Token de sesión
        
    Returns:
        bool: True si se invalidó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Eliminar la sesión
        cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error al invalidar sesión: {str(e)}")
        return False

def change_password(user_id, current_password, new_password):
    """
    Cambia la contraseña de un usuario.
    
    Args:
        user_id (int): ID del usuario
        current_password (str): Contraseña actual
        new_password (str): Nueva contraseña
        
    Returns:
        bool: True si se cambió correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar el usuario
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Convertir a diccionario
            user_dict = dict(user)
            
            # Verificar la contraseña actual
            current_hash, _ = hash_password(current_password, user_dict['salt'])
            
            if current_hash == user_dict['password_hash']:
                # Generar nuevo hash y salt para la nueva contraseña
                new_hash, new_salt = hash_password(new_password)
                
                # Actualizar la contraseña
                cursor.execute(
                    'UPDATE users SET password_hash = ?, salt = ? WHERE id = ?',
                    (new_hash, new_salt, user_id)
                )
                
                # Invalidar todas las sesiones existentes
                cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                
                return True
        
        conn.close()
        return False
    except Exception as e:
        print(f"Error al cambiar contraseña: {str(e)}")
        return False

def get_all_users():
    """
    Obtiene todos los usuarios.
    
    Returns:
        list: Lista de usuarios
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, role, created_at, last_login, is_active FROM users')
        users_data = cursor.fetchall()
        
        users = []
        for user in users_data:
            users.append(dict(user))
        
        conn.close()
        return users
    except Exception as e:
        print(f"Error al obtener usuarios: {str(e)}")
        return []

# Inicializar la base de datos al importar el módulo
init_db()
