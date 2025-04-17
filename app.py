from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash, session, make_response
import os
import requests
import json
import functools
from dotenv import load_dotenv
from message_handler import MessageHandler
from tours_db import get_all_tours, get_tour_by_id, add_tour, update_tour, delete_tour
from user_db import verify_user, create_session, verify_session, invalidate_session, get_all_users, change_password, create_user, get_user_by_id, update_user, delete_user

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración para mensajes flash y sesiones
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'clave_secreta_predeterminada')
app.config['SESSION_COOKIE_SECURE'] = True  # Solo enviar cookie a través de HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevenir acceso a cookies vía JavaScript
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # Sesión expira en 24 horas (en segundos)

# Inicializar el manejador de mensajes
message_handler = MessageHandler()

# Obtener las variables de entorno
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'token_predeterminado')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')

# Decorador para proteger rutas que requieren autenticación
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si hay un token de sesión en la cookie
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login', next=request.url))
        
        # Verificar si la sesión es válida
        user_data = verify_session(session_token)
        
        if not user_data:
            flash('Su sesión ha expirado. Por favor, inicie sesión nuevamente', 'warning')
            return redirect(url_for('login', next=request.url))
        
        # Almacenar datos del usuario en el contexto de la solicitud
        session['user'] = {
            'id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'role': user_data['role']
        }
        
        return f(*args, **kwargs)
    return decorated_function

# Decorador para roles específicos
def role_required(role):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Primero verificar que el usuario esté autenticado
            if 'user' not in session:
                flash('Debe iniciar sesión para acceder a esta página', 'warning')
                return redirect(url_for('login', next=request.url))
            
            # Verificar el rol del usuario
            if session['user']['role'] != role and session['user']['role'] != 'admin':
                flash('No tiene permisos para acceder a esta página', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirigir a la página principal
    session_token = request.cookies.get('session_token')
    if session_token and verify_session(session_token):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Verificar credenciales
        user = verify_user(username, password)
        
        if user:
            # Crear sesión
            session_token = create_session(
                user['id'],
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            # Almacenar datos del usuario en la sesión
            session['user'] = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
            
            # Crear respuesta con redirección
            next_page = request.args.get('next') or url_for('index')
            response = make_response(redirect(next_page))
            
            # Configurar cookie de sesión
            max_age = 86400 * 30 if remember else None  # 30 días si 'recordarme' está activo
            response.set_cookie(
                'session_token',
                session_token,
                max_age=max_age,
                httponly=True,
                secure=request.is_secure,
                samesite='Lax'
            )
            
            flash(f'Bienvenido, {user["username"]}!', 'success')
            return response
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    # Invalidar sesión en la base de datos
    session_token = request.cookies.get('session_token')
    if session_token:
        invalidate_session(session_token)
    
    # Limpiar sesión de Flask
    session.clear()
    
    # Crear respuesta y eliminar cookie
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')
    
    flash('Ha cerrado sesión correctamente', 'success')
    return response

# Ruta para cambiar contraseña
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_route():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return redirect(url_for('change_password_route'))
        
        if len(new_password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('change_password_route'))
        
        # Cambiar contraseña
        if change_password(session['user']['id'], current_password, new_password):
            flash('Contraseña cambiada correctamente. Por favor, inicie sesión nuevamente', 'success')
            return redirect(url_for('logout'))
        else:
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('change_password_route'))
    
    return render_template('change_password.html')

# Ruta para la interfaz web (protegida)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Rutas para administración de tours (protegidas)
@app.route('/admin/tours')
@login_required
@role_required('staff')
def admin_tours():
    tours = get_all_tours()
    return render_template('admin_tours.html', tours=tours)

@app.route('/admin/tours/new', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def new_tour():
    if request.method == 'POST':
        # Procesar los datos del formulario
        tour_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'duration': request.form['duration'],
            'price': float(request.form['price']),
            'currency': request.form['currency'],
            'includes': request.form.getlist('includes'),
            'location': request.form['location'],
            'availability': request.form['availability'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',')]
        }
        
        if add_tour(tour_data):
            flash('Tour añadido correctamente', 'success')
            return redirect(url_for('admin_tours'))
        else:
            flash('Error al añadir el tour', 'danger')
    
    return render_template('tour_form.html', tour=None, action='new')

@app.route('/admin/tours/edit/<tour_id>', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def edit_tour(tour_id):
    tour = get_tour_by_id(tour_id)
    
    if not tour:
        flash('Tour no encontrado', 'danger')
        return redirect(url_for('admin_tours'))
    
    if request.method == 'POST':
        # Procesar los datos del formulario
        tour_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'duration': request.form['duration'],
            'price': float(request.form['price']),
            'currency': request.form['currency'],
            'includes': request.form.getlist('includes'),
            'location': request.form['location'],
            'availability': request.form['availability'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',')]
        }
        
        if update_tour(tour_id, tour_data):
            flash('Tour actualizado correctamente', 'success')
            return redirect(url_for('admin_tours'))
        else:
            flash('Error al actualizar el tour', 'danger')
    
    # Convertir la lista de tags a string para el formulario
    tour['tags_string'] = ', '.join(tour['tags'])
    
    return render_template('tour_form.html', tour=tour, action='edit')

@app.route('/admin/tours/delete/<tour_id>', methods=['POST'])
@login_required
@role_required('staff')
def remove_tour(tour_id):
    if delete_tour(tour_id):
        flash('Tour eliminado correctamente', 'success')
    else:
        flash('Error al eliminar el tour', 'danger')
    
    return redirect(url_for('admin_tours'))

@app.route('/api/conversations')
@login_required
def get_conversations():
    """Endpoint para obtener todas las conversaciones"""
    conversations = []
    
    # Obtener la lista de archivos en el directorio de conversaciones
    if os.path.exists(message_handler.storage_dir):
        for filename in os.listdir(message_handler.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(message_handler.storage_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    conversation = json.load(f)
                    conversations.append(conversation)
    
    return jsonify({"conversations": conversations})

@app.route('/api/messages/<phone_number>')
@login_required
def get_messages(phone_number):
    """Endpoint para obtener una conversación específica"""
    conversation = message_handler.get_conversation_history(phone_number)
    
    if conversation:
        return jsonify(conversation)
    else:
        return jsonify({"error": "Conversación no encontrada"}), 404

@app.route('/api/send-message', methods=['POST'])
@login_required
def api_send_message():
    """Endpoint para enviar un mensaje desde la interfaz web"""
    data = request.json
    
    if not data or 'phone_number' not in data or 'message' not in data:
        return jsonify({"success": False, "error": "Datos inválidos"}), 400
    
    phone_number = data['phone_number']
    message = data['message']
    
    try:
        # Generar una respuesta usando el manejador de mensajes
        message_handler.save_message(phone_number, "sent", "text", message)
        
        # Enviar el mensaje a través de la API de WhatsApp
        result = send_whatsapp_message(phone_number, message)
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verificación del webhook de WhatsApp
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Verificar que el token coincida con nuestro token de verificación
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('WEBHOOK_VERIFICADO')
            return challenge, 200
        else:
            return 'Verificación fallida', 403
    
    elif request.method == 'POST':
        # Recibir mensajes de WhatsApp
        data = request.json
        print(f"Datos recibidos: {data}")
        
        try:
            # Verificar si hay entradas en el webhook
            if 'entry' in data and data['entry']:
                # Obtener la primera entrada
                entry = data['entry'][0]
                
                # Verificar si hay cambios en la entrada
                if 'changes' in entry and entry['changes']:
                    change = entry['changes'][0]
                    
                    # Verificar si el cambio es en el valor
                    if 'value' in change and 'messages' in change['value']:
                        messages = change['value']['messages']
                        
                        for message in messages:
                            # Obtener información del mensaje
                            message_id = message.get('id', '')
                            from_number = message['from'] if 'from' in message else ''
                            timestamp = message.get('timestamp', '')
                            
                            # Procesar diferentes tipos de mensajes
                            if 'text' in message:
                                # Mensaje de texto
                                text = message['text']['body']
                                print(f"Mensaje de texto recibido de {from_number}: {text}")
                                
                                # Procesamos el mensaje y generamos una respuesta usando el MessageHandler
                                response = message_handler.process_message(from_number, "text", text, message_id, timestamp)
                                # Enviamos la respuesta generada
                                send_whatsapp_message(from_number, response)
                            
                            elif 'image' in message:
                                # Mensaje de imagen
                                image_id = message['image']['id']
                                print(f"Imagen recibida de {from_number}, ID: {image_id}")
                                # Procesamos el mensaje de imagen
                                response = message_handler.process_message(from_number, "image", image_id, message_id, timestamp)
                                # Enviamos la respuesta
                                send_whatsapp_message(from_number, response)
                            
                            elif 'audio' in message:
                                # Mensaje de audio
                                audio_id = message['audio']['id']
                                print(f"Audio recibido de {from_number}, ID: {audio_id}")
                                # Procesamos el mensaje de audio
                                response = message_handler.process_message(from_number, "audio", audio_id, message_id, timestamp)
                                # Enviamos la respuesta
                                send_whatsapp_message(from_number, response)
                            
                            elif 'document' in message:
                                # Documento
                                document_id = message['document']['id']
                                print(f"Documento recibido de {from_number}, ID: {document_id}")
                                # Procesamos el mensaje de documento
                                response = message_handler.process_message(from_number, "document", document_id, message_id, timestamp)
                                # Enviamos la respuesta
                                send_whatsapp_message(from_number, response)
                            
                            else:
                                # Otro tipo de mensaje
                                print(f"Mensaje de tipo desconocido recibido de {from_number}")
                                # Procesamos el mensaje desconocido
                                response = message_handler.process_message(from_number, "unknown", "Contenido desconocido", message_id, timestamp)
                                # Enviamos la respuesta
                                send_whatsapp_message(from_number, response)
            
            return 'OK', 200
        except Exception as e:
            print(f"Error al procesar el mensaje: {str(e)}")
            return 'Error interno', 500

def send_whatsapp_message(to_number, message_text):
    """
    Envía un mensaje de WhatsApp utilizando la API de WhatsApp Business
    
    Args:
        to_number (str): Número de teléfono del destinatario en formato internacional sin el '+'
        message_text (str): Texto del mensaje a enviar
    
    Returns:
        dict: Respuesta de la API de WhatsApp
    """
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        print(f"Mensaje enviado: {response_data}")
        return response_data
    except Exception as e:
        print(f"Error al enviar mensaje: {str(e)}")
        return {"error": str(e)}

# Rutas para administración de usuarios (solo admin)
@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        # Validaciones
        if not username or not email or not password or not role:
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('new_user'))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('new_user'))
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('new_user'))
        
        # Crear usuario
        user_id = create_user(username, password, email, role)
        
        if user_id:
            flash(f'Usuario {username} creado correctamente', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash('Error al crear el usuario. Es posible que el nombre de usuario o email ya existan.', 'danger')
            return redirect(url_for('new_user'))
    
    return render_template('user_form.html', user=None, action='new')

@app.route('/admin/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = get_user_by_id(user_id)
    
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        # Validaciones
        if not username or not email or not role:
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
        
        # No permitir cambiar el rol del último administrador
        if user['role'] == 'admin' and role != 'admin':
            # Verificar si es el último administrador
            all_users = get_all_users()
            admin_count = sum(1 for u in all_users if u['role'] == 'admin')
            
            if admin_count <= 1:
                flash('No se puede cambiar el rol del último administrador', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))
        
        # Actualizar usuario
        if update_user(user_id, username, email, role, is_active):
            flash(f'Usuario {username} actualizado correctamente', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash('Error al actualizar el usuario', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))
    
    return render_template('user_form.html', user=user, action='edit')

@app.route('/admin/users/delete/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def remove_user(user_id):
    # No permitir eliminar al usuario actual
    if str(session['user']['id']) == str(user_id):
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin_users'))
    
    user = get_user_by_id(user_id)
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_users'))
    
    if delete_user(user_id):
        flash(f'Usuario {user["username"]} eliminado correctamente', 'success')
    else:
        flash('No se puede eliminar el último administrador', 'danger')
    
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    # En desarrollo, permitir HTTP
    app.config['SESSION_COOKIE_SECURE'] = False
    app.run(debug=True, port=5000)
