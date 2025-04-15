import json
import os
from datetime import datetime
import re

class MessageHandler:
    """
    Clase para manejar los mensajes de WhatsApp, incluyendo el procesamiento
    y la generación de respuestas.
    """
    
    def __init__(self, storage_dir='conversations'):
        """
        Inicializa el manejador de mensajes.
        
        Args:
            storage_dir (str): Directorio donde se almacenarán las conversaciones
        """
        self.storage_dir = storage_dir
        
        # Crear directorio de almacenamiento si no existe
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def process_message(self, from_number, message_type, message_content, message_id=None, timestamp=None):
        """
        Procesa un mensaje recibido y devuelve una respuesta.
        
        Args:
            from_number (str): Número de teléfono del remitente
            message_type (str): Tipo de mensaje (text, image, audio, document, etc.)
            message_content (str): Contenido del mensaje
            message_id (str, optional): ID del mensaje
            timestamp (str, optional): Marca de tiempo del mensaje
            
        Returns:
            str: Mensaje de respuesta
        """
        # Guardar el mensaje en el historial
        self.save_message(from_number, "received", message_type, message_content, message_id, timestamp)
        
        # Generar respuesta basada en el tipo de mensaje y contenido
        response = self.generate_response(from_number, message_type, message_content)
        
        # Guardar la respuesta en el historial
        self.save_message(from_number, "sent", "text", response)
        
        return response
    
    def save_message(self, phone_number, direction, msg_type, content, message_id=None, timestamp=None):
        """
        Guarda un mensaje en el historial de conversaciones.
        
        Args:
            phone_number (str): Número de teléfono
            direction (str): Dirección del mensaje ('received' o 'sent')
            msg_type (str): Tipo de mensaje
            content (str): Contenido del mensaje
            message_id (str, optional): ID del mensaje
            timestamp (str, optional): Marca de tiempo del mensaje
        """
        # Normalizar el número de teléfono para usarlo como nombre de archivo
        filename = self._normalize_phone(phone_number)
        filepath = os.path.join(self.storage_dir, f"{filename}.json")
        
        # Obtener la conversación existente o crear una nueva
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
        else:
            conversation = {
                "phone_number": phone_number,
                "messages": []
            }
        
        # Crear el nuevo mensaje
        message = {
            "direction": direction,
            "type": msg_type,
            "content": content,
            "timestamp": timestamp or datetime.now().isoformat(),
            "message_id": message_id
        }
        
        # Agregar el mensaje a la conversación
        conversation["messages"].append(message)
        
        # Guardar la conversación actualizada
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)
    
    def generate_response(self, from_number, message_type, message_content):
        """
        Genera una respuesta basada en el tipo y contenido del mensaje.
        
        Args:
            from_number (str): Número de teléfono del remitente
            message_type (str): Tipo de mensaje
            message_content (str): Contenido del mensaje
            
        Returns:
            str: Mensaje de respuesta
        """
        # Si no es un mensaje de texto, enviar una respuesta genérica
        if message_type != "text":
            return f"Gracias por enviar un {message_type}. Actualmente solo puedo procesar mensajes de texto."
        
        # Convertir a minúsculas para facilitar el procesamiento
        content = message_content.lower()
        
        # Patrones básicos de respuesta
        greeting_patterns = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos']
        help_patterns = ['ayuda', 'help', 'opciones', 'comandos', '?']
        thanks_patterns = ['gracias', 'thanks', 'thank you', 'thx']
        
        # Verificar si es un saludo
        if any(pattern in content for pattern in greeting_patterns):
            return f"¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte hoy?"
        
        # Verificar si es una solicitud de ayuda
        elif any(pattern in content for pattern in help_patterns):
            return ("Estos son los comandos disponibles:\n"
                   "- *ayuda*: Muestra este mensaje\n"
                   "- *info*: Información sobre este servicio\n"
                   "- *contacto*: Datos de contacto\n")
        
        # Verificar si es un agradecimiento
        elif any(pattern in content for pattern in thanks_patterns):
            return "¡De nada! Estamos para servirte. ¿Hay algo más en lo que pueda ayudarte?"
        
        # Comando de información
        elif 'info' in content:
            return ("Este es un servicio de mensajería automatizado.\n"
                   "Estamos en fase de desarrollo y pronto tendremos más funcionalidades.")
        
        # Comando de contacto
        elif 'contacto' in content:
            return ("Puedes contactarnos en:\n"
                   "- Email: contacto@ejemplo.com\n"
                   "- Teléfono: +1234567890\n"
                   "- Sitio web: www.ejemplo.com")
        
        # Respuesta predeterminada
        else:
            return f"Recibí tu mensaje: '{message_content}'. ¿En qué más puedo ayudarte?"
    
    def get_conversation_history(self, phone_number):
        """
        Obtiene el historial de conversación para un número de teléfono.
        
        Args:
            phone_number (str): Número de teléfono
            
        Returns:
            dict: Historial de conversación o None si no existe
        """
        filename = self._normalize_phone(phone_number)
        filepath = os.path.join(self.storage_dir, f"{filename}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def _normalize_phone(self, phone_number):
        """
        Normaliza un número de teléfono para usarlo como nombre de archivo.
        
        Args:
            phone_number (str): Número de teléfono
            
        Returns:
            str: Número de teléfono normalizado
        """
        # Eliminar caracteres no alfanuméricos
        return re.sub(r'\W+', '', phone_number)
