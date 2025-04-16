import json
import os
import re
from datetime import datetime
from tours_db import search_tours, get_tour_by_id, format_tour_info, get_all_tours
from amadeus_api import amadeus_api

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
        original_content = message_content  # Mantener el contenido original para referencias
        
        # Patrones básicos de respuesta
        greeting_patterns = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos']
        help_patterns = ['ayuda', 'help', 'opciones', 'comandos', '?']
        thanks_patterns = ['gracias', 'thanks', 'thank you', 'thx']
        
        # Patrones para tours y vuelos
        tour_patterns = ['tour', 'tours', 'paquete', 'paquetes', 'vacaciones', 'viaje', 'viajes', 'destino', 'destinos']
        flight_patterns = ['vuelo', 'vuelos', 'boleto', 'boletos', 'avion', 'avión', 'aeropuerto']
        
        # Verificar si es un saludo
        if any(pattern in content for pattern in greeting_patterns):
            return (f"¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte hoy?\n\n"
                   f"Puedo ayudarte con:\n"
                   f"- Información sobre *tours* y paquetes vacacionales\n"
                   f"- Búsqueda de *vuelos* disponibles\n"
                   f"- Información de *contacto* y más\n\n"
                   f"Escribe *ayuda* para ver todas las opciones disponibles.")
        
        # Verificar si es una solicitud de ayuda
        elif any(pattern in content for pattern in help_patterns):
            return ("Estos son los comandos disponibles:\n\n"
                   "*Información general:*\n"
                   "- *ayuda*: Muestra este mensaje\n"
                   "- *info*: Información sobre este servicio\n"
                   "- *contacto*: Datos de contacto\n\n"
                   "*Tours y paquetes:*\n"
                   "- *tours*: Muestra todos los tours disponibles\n"
                   "- *tour [destino]*: Busca tours para un destino específico\n"
                   "- *detalles tour [ID]*: Muestra detalles de un tour específico\n\n"
                   "*Vuelos:*\n"
                   "- *vuelos [origen] a [destino] [fecha]*: Busca vuelos disponibles\n"
                   "  Ejemplo: vuelos MEX a CUN 2025-05-15\n"
                   "- *vuelos [origen] a [destino] [fecha ida] [fecha regreso]*: Busca vuelos de ida y vuelta\n"
                   "  Ejemplo: vuelos MEX a CUN 2025-05-15 2025-05-22")
        
        # Verificar si es una solicitud de tours
        elif content == 'tours':
            # Mostrar todos los tours disponibles
            tours = get_all_tours()
            response = "*Tours disponibles:*\n\n"
            
            for tour in tours:
                response += f"🏝️ *{tour['name']}*\n"
                response += f"📍 {tour['location']}\n"
                response += f"💰 ${tour['price']} {tour['currency']}\n"
                response += f"🔍 ID: {tour['id']}\n\n"
            
            response += "Para ver detalles de un tour específico, escribe 'detalles tour [ID]'."
            return response
        
        # Verificar si es una búsqueda de tours
        elif any(pattern in content for pattern in tour_patterns):
            # Buscar tours que coincidan con la consulta
            # Eliminar palabras clave como 'tour', 'paquete', etc.
            for pattern in tour_patterns:
                content = content.replace(pattern, '').strip()
            
            # Si es una solicitud de detalles de un tour específico
            if content.startswith('detalles') or content.startswith('detalle'):
                # Extraer el ID del tour
                tour_id = content.split()[-1].upper()
                tour = get_tour_by_id(tour_id)
                
                if tour:
                    return format_tour_info(tour)
                else:
                    return f"Lo siento, no encontré un tour con el ID {tour_id}. Escribe 'tours' para ver todos los tours disponibles."
            
            # Si hay contenido para buscar
            if content:
                results = search_tours(content)
                
                if results:
                    response = f"Encontré {len(results)} tours que coinciden con tu búsqueda:\n\n"
                    
                    for tour in results:
                        response += f"🏝️ *{tour['name']}*\n"
                        response += f"📍 {tour['location']}\n"
                        response += f"💰 ${tour['price']} {tour['currency']}\n"
                        response += f"🔍 ID: {tour['id']}\n\n"
                    
                    response += "Para ver detalles de un tour específico, escribe 'detalles tour [ID]'."
                    return response
                else:
                    return f"Lo siento, no encontré tours que coincidan con '{content}'. Escribe 'tours' para ver todos los tours disponibles."
            else:
                # Si solo escribió una palabra clave como 'tour' sin especificar destino
                return "Por favor, especifica un destino o escribe 'tours' para ver todos los tours disponibles."
        
        # Verificar si es una búsqueda de vuelos
        elif any(pattern in content for pattern in flight_patterns):
            # Buscar vuelos que coincidan con la consulta
            # Verificar si tiene el formato correcto: vuelos [origen] a [destino] [fecha] [fecha_regreso]?
            flight_match = re.search(r'vuelos? ([a-z]{3}) a ([a-z]{3}) (\d{4}-\d{2}-\d{2})(?: (\d{4}-\d{2}-\d{2}))?', content)
            
            if flight_match:
                origin = flight_match.group(1).upper()
                destination = flight_match.group(2).upper()
                departure_date = flight_match.group(3)
                return_date = flight_match.group(4) if flight_match.group(4) else None
                
                try:
                    # Buscar vuelos
                    flights = amadeus_api.search_flights(origin, destination, departure_date, return_date)
                    
                    if flights:
                        # Mostrar el primer vuelo encontrado
                        flight_info = amadeus_api.format_flight_info(flights[0])
                        return flight_info
                    else:
                        return f"Lo siento, no encontré vuelos disponibles de {origin} a {destination} para la fecha {departure_date}."
                except Exception as e:
                    print(f"Error al buscar vuelos: {str(e)}")
                    return "Lo siento, ocurrió un error al buscar vuelos. Por favor, intenta más tarde o contacta a nuestro equipo de soporte."
            else:
                return ("Para buscar vuelos, utiliza el siguiente formato:\n"
                       "- vuelos [origen] a [destino] [fecha]\n"
                       "  Ejemplo: vuelos MEX a CUN 2025-05-15\n\n"
                       "Para vuelos de ida y vuelta:\n"
                       "- vuelos [origen] a [destino] [fecha ida] [fecha regreso]\n"
                       "  Ejemplo: vuelos MEX a CUN 2025-05-15 2025-05-22")
        
        # Verificar si es un agradecimiento
        elif any(pattern in content for pattern in thanks_patterns):
            return "¡De nada! Estamos para servirte. ¿Hay algo más en lo que pueda ayudarte?"
        
        # Comando de información
        elif 'info' in content:
            return ("Somos una agencia de viajes especializada en tours y vuelos.\n"
                   "Ofrecemos los mejores paquetes turísticos y las mejores tarifas en vuelos.\n\n"
                   "Escribe 'tours' para ver nuestros paquetes disponibles o 'ayuda' para ver todas las opciones.")
        
        # Comando de contacto
        elif 'contacto' in content:
            return ("Puedes contactarnos en:\n"
                   "- Email: info@paseotravel.com\n"
                   "- Teléfono: +1 818 244 2184\n"
                   "- WhatsApp: Este mismo número\n"
                   "- Sitio web: www.paseotravel.com\n\n"
                   "Horario de atención: Lunes a Viernes de 9:00 a 19:00,\nSabados de 11:00 a 15:00")
        
        # Respuesta predeterminada
        else:
            return (f"Recibí tu mensaje: '{original_content}'.\n\n"
                   f"Puedo ayudarte con información sobre tours y vuelos. Escribe 'ayuda' para ver todas las opciones disponibles.")
    
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
