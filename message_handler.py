import json
import os
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from tours_db import search_tours, get_tour_by_id, format_tour_info, get_all_tours
from amadeus_api import amadeus_api

class MessageHandler:
    """
    Clase para manejar los mensajes de WhatsApp, incluyendo el procesamiento
    y la generación de respuestas.
    """
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Mantener compatibilidad con la ruta original
        self.conversations_dir = os.path.join(data_dir, 'conversations')
        self.archived_dir = os.path.join(data_dir, 'archived')
        
        # Crear directorios si no existen
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.archived_dir, exist_ok=True)
        
        # Cargar o crear archivo de metadatos
        self.metadata_file = os.path.join(data_dir, 'conversation_metadata.json')
        self.metadata = self.load_metadata()
        
        # Sistema anti-bot
        self.message_history = defaultdict(list)  # Historial de mensajes por número
        self.bot_blacklist = set()  # Lista negra de números identificados como bots
        self.response_timestamps = defaultdict(list)  # Timestamps de respuestas por número
        self.max_responses_per_hour = 10  # Máximo de respuestas automáticas por hora
        self.bot_detection_threshold = 3  # Número de mensajes similares para considerar bot
        
        # Cargar lista negra si existe
        self.bot_blacklist_file = os.path.join(data_dir, 'bot_blacklist.json')
        self.load_bot_blacklist()
    
    def load_metadata(self):
        """Cargar metadatos de conversaciones o crear si no existe"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Si hay un error al cargar, crear un nuevo archivo
                pass
        
        # Estructura inicial de metadatos
        return {
            "tags": {},  # Etiquetas por conversación
            "status": {}  # Estado por conversación
        }
    
    def save_metadata(self):
        """Guardar metadatos de conversaciones"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def load_bot_blacklist(self):
        """Cargar lista negra de bots"""
        if os.path.exists(self.bot_blacklist_file):
            try:
                with open(self.bot_blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bot_blacklist = set(data.get("blacklist", []))
            except (json.JSONDecodeError, FileNotFoundError):
                self.bot_blacklist = set()
    
    def save_bot_blacklist(self):
        """Guardar lista negra de bots"""
        with open(self.bot_blacklist_file, 'w', encoding='utf-8') as f:
            json.dump({"blacklist": list(self.bot_blacklist)}, f, ensure_ascii=False, indent=4)
    
    def process_message(self, from_number, message_type, message_content, message_id=None, timestamp=None):
        """
        Procesa un mensaje recibido y devuelve una respuesta.
        
        Args:
            from_number (str): Número de teléfono del remitente
            message_type (str): Tipo de mensaje
            message_content (str): Contenido del mensaje
            message_id (str, optional): ID del mensaje
            timestamp (str, optional): Marca de tiempo del mensaje
            
        Returns:
            str: Mensaje de respuesta o None si se identifica como bot
        """
        # Normalizar el número de teléfono
        from_number = self.normalize_phone_number(from_number)
        
        # Verificar si el número está en la lista negra de bots
        if from_number in self.bot_blacklist:
            print(f"Mensaje ignorado de número en lista negra: {from_number}")
            # Guardar el mensaje pero no responder
            self.save_message(from_number, "received", message_type, message_content, message_id, timestamp)
            return None
        
        # Verificar límite de frecuencia de respuestas
        if not self.can_send_response(from_number):
            print(f"Límite de respuestas excedido para: {from_number}")
            # Guardar el mensaje pero no responder
            self.save_message(from_number, "received", message_type, message_content, message_id, timestamp)
            return None
        
        # Guardar el mensaje en el historial
        self.save_message(from_number, "received", message_type, message_content, message_id, timestamp)
        
        # Actualizar historial para detección de bots
        self.update_message_history(from_number, message_content)
        
        # Verificar si es un bot basado en patrones repetitivos
        if self.is_bot(from_number):
            print(f"Bot detectado: {from_number}")
            self.bot_blacklist.add(from_number)
            self.save_bot_blacklist()
            # Añadir etiqueta de bot a la conversación
            tags = self.get_conversation_tags(from_number)
            if "Bot" not in tags:
                tags.append("Bot")
                self.set_conversation_tags(from_number, tags)
            return None
        
        # Generar respuesta basada en el tipo de mensaje y contenido
        response = self.generate_response(from_number, message_type, message_content)
        
        # Registrar timestamp de respuesta para control de frecuencia
        self.response_timestamps[from_number].append(time.time())
        
        # Guardar la respuesta en el historial
        self.save_message(from_number, "sent", "text", response)
        
        return response
    
    def update_message_history(self, phone_number, message_content):
        """Actualizar historial de mensajes para detección de bots"""
        # Mantener solo los últimos 10 mensajes
        if len(self.message_history[phone_number]) >= 10:
            self.message_history[phone_number].pop(0)
        
        self.message_history[phone_number].append(message_content)
    
    def is_bot(self, phone_number):
        """Detectar si un número es un bot basado en patrones repetitivos"""
        if len(self.message_history[phone_number]) < self.bot_detection_threshold:
            return False
        
        # Contar ocurrencias de cada mensaje
        message_counts = Counter(self.message_history[phone_number])
        
        # Si algún mensaje se repite más del umbral, considerar bot
        most_common = message_counts.most_common(1)
        if most_common and most_common[0][1] >= self.bot_detection_threshold:
            return True
        
        return False
    
    def can_send_response(self, phone_number):
        """Verificar si se puede enviar una respuesta basado en límites de frecuencia"""
        # Obtener timestamps de la última hora
        one_hour_ago = time.time() - 3600
        recent_responses = [t for t in self.response_timestamps[phone_number] if t > one_hour_ago]
        
        # Actualizar lista de timestamps recientes
        self.response_timestamps[phone_number] = recent_responses
        
        # Verificar si se excede el límite por hora
        return len(recent_responses) < self.max_responses_per_hour
    
    def analyze_existing_conversations(self):
        """Analizar conversaciones existentes para detectar bots"""
        print("Analizando conversaciones existentes para detectar bots...")
        detected_bots = []
        
        # Obtener todas las conversaciones (activas y archivadas)
        conversations = self.get_conversations(include_archived=True)
        
        for conversation in conversations:
            phone_number = conversation['phone_number']
            messages = conversation['messages']
            
            # Saltear si ya está en la lista negra
            if phone_number in self.bot_blacklist:
                continue
            
            # Filtrar solo mensajes recibidos
            received_messages = [msg for msg in messages if msg['direction'] == 'received']
            
            # Si hay pocos mensajes, no analizar
            if len(received_messages) < self.bot_detection_threshold:
                continue
            
            # Contar ocurrencias de cada mensaje
            message_contents = [msg['content'] for msg in received_messages]
            message_counts = Counter(message_contents)
            
            # Verificar si hay mensajes repetidos que superen el umbral
            most_common = message_counts.most_common(1)
            if most_common and most_common[0][1] >= self.bot_detection_threshold:
                bot_message = most_common[0][0]
                repetitions = most_common[0][1]
                print(f"Bot detectado: {phone_number} - Mensaje '{bot_message[:30]}...' repetido {repetitions} veces")
                detected_bots.append({
                    'phone_number': phone_number,
                    'message': bot_message,
                    'repetitions': repetitions
                })
                
                # Añadir a la lista negra
                self.bot_blacklist.add(phone_number)
                
                # Añadir etiqueta de bot a la conversación
                tags = self.get_conversation_tags(phone_number)
                if "Bot" not in tags:
                    tags.append("Bot")
                    self.set_conversation_tags(phone_number, tags)
        
        # Guardar la lista negra actualizada
        self.save_bot_blacklist()
        
        print(f"Análisis completado: {len(detected_bots)} bots detectados")
        return detected_bots
    
    def save_message(self, phone_number, direction, msg_type, content, message_id=None, timestamp=None, source="whatsapp"):
        # Normalizar número de teléfono
        phone_number = self.normalize_phone_number(phone_number)
        
        # Crear directorio para el número si no existe
        conversation_dir = os.path.join(self.conversations_dir, phone_number)
        os.makedirs(conversation_dir, exist_ok=True)
        
        # Archivo de mensajes
        messages_file = os.path.join(conversation_dir, 'messages.json')
        
        # Cargar mensajes existentes o crear lista vacía
        if os.path.exists(messages_file):
            with open(messages_file, 'r', encoding='utf-8') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = []
        else:
            messages = []
        
        # Crear nuevo mensaje
        message = {
            "direction": direction,
            "type": msg_type,
            "content": content,
            "timestamp": timestamp or datetime.now().isoformat(),
            "message_id": message_id,
            "source": source
        }
        
        # Añadir mensaje a la lista
        messages.append(message)
        
        # Guardar mensajes
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        # Si es un mensaje nuevo recibido, establecer estado como 'new' si no tiene estado
        if direction == 'received' and phone_number not in self.metadata['status']:
            self.set_conversation_status(phone_number, 'new')
        
        return message
    
    def get_conversations(self, include_archived=False):
        """Obtener lista de todas las conversaciones"""
        conversations = []
        
        # Directorios a recorrer
        dirs_to_check = [self.conversations_dir]
        if include_archived:
            dirs_to_check.append(self.archived_dir)
        
        # Recorrer directorios de conversaciones
        for base_dir in dirs_to_check:
            if not os.path.exists(base_dir):
                continue
                
            for phone_number in os.listdir(base_dir):
                conversation_dir = os.path.join(base_dir, phone_number)
                if os.path.isdir(conversation_dir):
                    messages_file = os.path.join(conversation_dir, 'messages.json')
                    if os.path.exists(messages_file):
                        with open(messages_file, 'r', encoding='utf-8') as f:
                            try:
                                messages = json.load(f)
                                # Determinar la fuente más reciente (whatsapp, sms, email)
                                source = "whatsapp"  # valor por defecto
                                for msg in reversed(messages):
                                    if "source" in msg:
                                        source = msg["source"]
                                        break
                                
                                # Determinar si está archivada
                                is_archived = base_dir == self.archived_dir
                                
                                # Obtener etiquetas y estado
                                tags = self.get_conversation_tags(phone_number)
                                status = self.get_conversation_status(phone_number)
                                
                                conversations.append({
                                    'phone_number': phone_number,
                                    'messages': messages,
                                    'source': source,
                                    'archived': is_archived,
                                    'tags': tags,
                                    'status': status
                                })
                            except json.JSONDecodeError:
                                pass
        
        # Ordenar conversaciones por timestamp del último mensaje (más reciente primero)
        def get_timestamp_value(conversation):
            if not conversation['messages']:
                return 0  # Si no hay mensajes, poner al final
            
            # Obtener el timestamp del último mensaje
            timestamp = conversation['messages'][-1]['timestamp']
            
            # Convertir el timestamp a un valor numérico para comparación
            try:
                # Si es un número entero como string, convertirlo a int
                if isinstance(timestamp, str) and timestamp.isdigit():
                    return int(timestamp)
                # Si es un timestamp ISO, convertirlo a datetime y luego a timestamp
                elif isinstance(timestamp, str):
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        return dt.timestamp()
                    except ValueError:
                        # Si no se puede convertir, usar 0
                        return 0
                # Si ya es un número, usarlo directamente
                elif isinstance(timestamp, (int, float)):
                    return timestamp
                else:
                    return 0
            except Exception as e:
                print(f"Error al procesar timestamp: {timestamp}, {e}")
                return 0
        
        # Ordenar usando la función auxiliar
        conversations.sort(key=get_timestamp_value, reverse=True)
        
        return conversations
    
    def get_conversation_tags(self, phone_number):
        """Obtener etiquetas de una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        return self.metadata['tags'].get(phone_number, [])
    
    def set_conversation_tags(self, phone_number, tags):
        """Establecer etiquetas para una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        self.metadata['tags'][phone_number] = tags
        self.save_metadata()
        return tags
    
    def add_conversation_tag(self, phone_number, tag):
        """Añadir una etiqueta a una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        if phone_number not in self.metadata['tags']:
            self.metadata['tags'][phone_number] = []
        
        if tag not in self.metadata['tags'][phone_number]:
            self.metadata['tags'][phone_number].append(tag)
            self.save_metadata()
        
        return self.metadata['tags'][phone_number]
    
    def remove_conversation_tag(self, phone_number, tag):
        """Eliminar una etiqueta de una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        if phone_number in self.metadata['tags'] and tag in self.metadata['tags'][phone_number]:
            self.metadata['tags'][phone_number].remove(tag)
            self.save_metadata()
        
        return self.metadata['tags'].get(phone_number, [])
    
    def get_conversation_status(self, phone_number):
        """Obtener estado de una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        return self.metadata['status'].get(phone_number, 'new')
    
    def set_conversation_status(self, phone_number, status):
        """Establecer estado para una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        self.metadata['status'][phone_number] = status
        self.save_metadata()
        return status
    
    def archive_conversation(self, phone_number):
        """Archivar una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        source_dir = os.path.join(self.conversations_dir, phone_number)
        target_dir = os.path.join(self.archived_dir, phone_number)
        
        if os.path.exists(source_dir):
            # Crear directorio de destino si no existe
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Mover directorio de conversación a archivados
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)  # Eliminar directorio de destino si ya existe
            
            shutil.move(source_dir, target_dir)
            return True
        
        return False
    
    def unarchive_conversation(self, phone_number):
        """Desarchivar una conversación"""
        phone_number = self.normalize_phone_number(phone_number)
        source_dir = os.path.join(self.archived_dir, phone_number)
        target_dir = os.path.join(self.conversations_dir, phone_number)
        
        if os.path.exists(source_dir):
            # Crear directorio de destino si no existe
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Mover directorio de conversación a activos
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)  # Eliminar directorio de destino si ya existe
            
            shutil.move(source_dir, target_dir)
            return True
        
        return False
    
    def export_conversation(self, phone_number):
        """Exportar una conversación a formato JSON"""
        phone_number = self.normalize_phone_number(phone_number)
        
        # Buscar la conversación en activos o archivados
        conversation_dir = os.path.join(self.conversations_dir, phone_number)
        is_archived = False
        
        if not os.path.exists(conversation_dir):
            conversation_dir = os.path.join(self.archived_dir, phone_number)
            is_archived = True
            
            if not os.path.exists(conversation_dir):
                return None  # No se encontró la conversación
        
        messages_file = os.path.join(conversation_dir, 'messages.json')
        if not os.path.exists(messages_file):
            return None
        
        with open(messages_file, 'r', encoding='utf-8') as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                return None
        
        # Crear objeto de exportación
        export_data = {
            'phone_number': phone_number,
            'messages': messages,
            'tags': self.get_conversation_tags(phone_number),
            'status': self.get_conversation_status(phone_number),
            'archived': is_archived,
            'exported_at': datetime.now().isoformat()
        }
        
        return export_data
    
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
        flight_patterns = ['vuelo', 'vuelos', 'boleto', 'boletos', 'avion', 'avión', 'aeropuerto', 'flight', 'flights', 'ticket', 'tickets']
        
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
            # Intentar diferentes patrones de búsqueda de vuelos
            
            # Patrón 1: vuelos [origen] a [destino] [fecha] [fecha_regreso]?
            flight_match = re.search(r'vuelos? ([a-z]{3}) a ([a-z]{3}) (\d{4}-\d{2}-\d{2})(?:\s(\d{4}-\d{2}-\d{2}))?', content)
            
            # Patrón 2: vuelos de [origen] a [destino] para [fecha] [fecha_regreso]?
            if not flight_match:
                flight_match = re.search(r'vuelos? de ([a-z]{3}) a ([a-z]{3}) (?:para|el) (\d{4}-\d{2}-\d{2})(?:\s(?:al|hasta|regreso)\s(\d{4}-\d{2}-\d{2}))?', content)
            
            # Patrón 3: vuelos [origen]-[destino] [fecha] [fecha_regreso]?
            if not flight_match:
                flight_match = re.search(r'vuelos? ([a-z]{3})[\s-]([a-z]{3}) (\d{4}-\d{2}-\d{2})(?:\s(\d{4}-\d{2}-\d{2}))?', content)
                
            # Patrón 4: vuelos de [origen] a [destino] del [fecha] al [fecha]
            if not flight_match:
                flight_match = re.search(r'vuelos? de ([a-z]{3}) a ([a-z]{3}) del (\d{4}-\d{2}-\d{2}) al (\d{4}-\d{2}-\d{2})', content)
            
            if flight_match:
                origin = flight_match.group(1).upper()
                destination = flight_match.group(2).upper()
                departure_date = flight_match.group(3)
                return_date = flight_match.group(4) if flight_match.group(4) else None
                
                # Crear enlace de quick_search
                quick_search_params = [
                    f"origin={origin}",
                    f"destination={destination}",
                    f"departure_date={departure_date}"
                ]
                
                # Determinar el tipo de viaje (ida y vuelta o solo ida)
                if return_date:
                    quick_search_params.append(f"return_date={return_date}")
                    quick_search_params.append("trip_type=roundtrip")
                else:
                    quick_search_params.append("trip_type=oneway")
                
                quick_search_params.append("adults=1")
                quick_search_params.append("auto_search=true")
                
                quick_search_url = f"https://vuelos.paseotravel.com/quick_search?{'&'.join(quick_search_params)}"
                
                try:
                    # Buscar vuelos
                    flights = amadeus_api.search_flights(origin, destination, departure_date, return_date)
                    
                    if flights:
                        # Mostrar el primer vuelo encontrado
                        flight_info = amadeus_api.format_flight_info(flights[0])
                        
                        # Agregar enlace para completar la reserva
                        flight_info += f"\n\n🔗 *Completa tu reserva aquí:*\n{quick_search_url}"
                        
                        # Agregar mensaje adicional sobre más opciones
                        flight_info += "\n\nEste es solo uno de los vuelos disponibles. Para ver más opciones y completar tu reserva, haz clic en el enlace anterior."
                        
                        return flight_info
                    else:
                        return f"Lo siento, no encontré vuelos disponibles de {origin} a {destination} para la fecha {departure_date}.\n\nPuedes intentar con otras fechas o destinos, o buscar directamente en nuestro sitio web:\n{quick_search_url}"
                except Exception as e:
                    print(f"Error al buscar vuelos: {str(e)}")
                    return f"Lo siento, ocurrió un error al buscar vuelos. Por favor, intenta más tarde o visita nuestro sitio web para buscar opciones:\n{quick_search_url}"
            else:
                # Si no se encontró un patrón específico pero el usuario está interesado en vuelos
                # Ofrecer un enlace genérico a la página de búsqueda
                generic_search_url = "https://vuelos.paseotravel.com/quick_search"
                
                return ("Para buscar vuelos, utiliza alguno de estos formatos:\n\n"
                       "*Vuelos solo ida:*\n"
                       "- vuelos [origen] a [destino] [fecha]\n"
                       "  Ejemplo: vuelos MEX a CUN 2025-05-15\n"
                       "- vuelos de [origen] a [destino] para [fecha]\n"
                       "  Ejemplo: vuelos de MEX a CUN para 2025-05-15\n\n"
                       "*Vuelos de ida y vuelta:*\n"
                       "- vuelos [origen] a [destino] [fecha ida] [fecha regreso]\n"
                       "  Ejemplo: vuelos MEX a CUN 2025-05-15 2025-05-22\n"
                       "- vuelos de [origen] a [destino] del [fecha ida] al [fecha regreso]\n"
                       "  Ejemplo: vuelos de MEX a CUN del 2025-05-15 al 2025-05-22\n\n"
                       f"También puedes visitar directamente nuestro buscador de vuelos:\n{generic_search_url}")
        
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
    
    def normalize_phone_number(self, phone_number):
        """
        Normaliza un número de teléfono para usarlo como nombre de archivo.
        
        Args:
            phone_number (str): Número de teléfono
            
        Returns:
            str: Número de teléfono normalizado
        """
        # Eliminar caracteres no alfanuméricos
        return re.sub(r'\W+', '', phone_number)
