from flask import Flask, request, jsonify, render_template
import os
import requests
import json
from dotenv import load_dotenv
from message_handler import MessageHandler

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Inicializar el manejador de mensajes
message_handler = MessageHandler()

# Obtener las variables de entorno
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'token_predeterminado')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/conversations')
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

@app.route('/api/conversations/<phone_number>')
def get_conversation(phone_number):
    """Endpoint para obtener una conversación específica"""
    conversation = message_handler.get_conversation_history(phone_number)
    
    if conversation:
        return jsonify(conversation)
    else:
        return jsonify({"error": "Conversación no encontrada"}), 404

@app.route('/api/send-message', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
