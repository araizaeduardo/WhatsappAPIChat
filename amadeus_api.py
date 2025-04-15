"""
Módulo para interactuar con la API de Amadeus para búsqueda de vuelos.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener las credenciales de Amadeus
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')

# URLs de la API de Amadeus
AMADEUS_AUTH_URL = 'https://test.api.amadeus.com/v1/security/oauth2/token'
AMADEUS_FLIGHT_OFFERS_URL = 'https://test.api.amadeus.com/v2/shopping/flight-offers'

class AmadeusAPI:
    """
    Clase para interactuar con la API de Amadeus.
    """
    
    def __init__(self):
        """
        Inicializa la API de Amadeus.
        """
        self.api_key = AMADEUS_API_KEY
        self.api_secret = AMADEUS_API_SECRET
        self.access_token = None
        self.token_expires = None
    
    def _get_access_token(self):
        """
        Obtiene un token de acceso para la API de Amadeus.
        
        Returns:
            str: Token de acceso
        """
        # Si ya tenemos un token válido, lo devolvemos
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        # Si no, obtenemos un nuevo token
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        response = requests.post(AMADEUS_AUTH_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Establecer la expiración del token (normalmente 30 minutos, pero restamos 1 para estar seguros)
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 60)
            return self.access_token
        else:
            raise Exception(f"Error al obtener el token de acceso: {response.text}")
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, max_results=5):
        """
        Busca vuelos disponibles.
        
        Args:
            origin (str): Código IATA del aeropuerto de origen (ej. 'MEX')
            destination (str): Código IATA del aeropuerto de destino (ej. 'CUN')
            departure_date (str): Fecha de salida en formato YYYY-MM-DD
            return_date (str, optional): Fecha de regreso en formato YYYY-MM-DD
            adults (int, optional): Número de adultos
            max_results (int, optional): Número máximo de resultados
            
        Returns:
            list: Lista de vuelos disponibles
        """
        # Obtener token de acceso
        access_token = self._get_access_token()
        
        # Configurar headers
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Configurar parámetros
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
            'currencyCode': 'MXN'
        }
        
        # Agregar fecha de regreso si se proporciona
        if return_date:
            params['returnDate'] = return_date
        
        # Realizar la solicitud
        response = requests.get(AMADEUS_FLIGHT_OFFERS_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            error_message = f"Error al buscar vuelos: {response.text}"
            print(error_message)
            return []
    
    def format_flight_info(self, flight):
        """
        Formatea la información de un vuelo para mostrarla en un mensaje.
        
        Args:
            flight (dict): Información del vuelo
            
        Returns:
            str: Mensaje formateado
        """
        try:
            # Obtener información básica
            price = flight['price']['total']
            currency = flight['price']['currency']
            
            # Información de ida
            outbound = flight['itineraries'][0]
            outbound_duration = outbound['duration']
            outbound_segments = outbound['segments']
            
            # Información de regreso (si existe)
            has_return = len(flight['itineraries']) > 1
            if has_return:
                inbound = flight['itineraries'][1]
                inbound_duration = inbound['duration']
                inbound_segments = inbound['segments']
            
            # Formatear mensaje
            message = (
                f"*Vuelo encontrado*\n\n"
                f"💰 *Precio:* {price} {currency}\n\n"
            )
            
            # Información de ida
            message += f"*Vuelo de ida* ✈️\n"
            message += f"⏱️ *Duración:* {self._format_duration(outbound_duration)}\n"
            
            for i, segment in enumerate(outbound_segments):
                departure = segment['departure']
                arrival = segment['arrival']
                carrier = segment['carrierCode']
                flight_number = segment['number']
                
                message += (
                    f"\n*Segmento {i+1}:*\n"
                    f"🛫 Salida: {departure['iataCode']} - {self._format_datetime(departure['at'])}\n"
                    f"🛬 Llegada: {arrival['iataCode']} - {self._format_datetime(arrival['at'])}\n"
                    f"✈️ Vuelo: {carrier} {flight_number}\n"
                )
            
            # Información de regreso (si existe)
            if has_return:
                message += f"\n*Vuelo de regreso* ✈️\n"
                message += f"⏱️ *Duración:* {self._format_duration(inbound_duration)}\n"
                
                for i, segment in enumerate(inbound_segments):
                    departure = segment['departure']
                    arrival = segment['arrival']
                    carrier = segment['carrierCode']
                    flight_number = segment['number']
                    
                    message += (
                        f"\n*Segmento {i+1}:*\n"
                        f"🛫 Salida: {departure['iataCode']} - {self._format_datetime(departure['at'])}\n"
                        f"🛬 Llegada: {arrival['iataCode']} - {self._format_datetime(arrival['at'])}\n"
                        f"✈️ Vuelo: {carrier} {flight_number}\n"
                    )
            
            message += "\nPara reservar este vuelo, por favor contacta a nuestro equipo de ventas."
            
            return message
        except Exception as e:
            print(f"Error al formatear información del vuelo: {str(e)}")
            return "Lo siento, no pude formatear la información del vuelo correctamente."
    
    def _format_datetime(self, datetime_str):
        """
        Formatea una cadena de fecha y hora.
        
        Args:
            datetime_str (str): Cadena de fecha y hora en formato ISO
            
        Returns:
            str: Fecha y hora formateada
        """
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return datetime_str
    
    def _format_duration(self, duration_str):
        """
        Formatea una cadena de duración.
        
        Args:
            duration_str (str): Cadena de duración en formato PT2H30M
            
        Returns:
            str: Duración formateada
        """
        try:
            # Eliminar el prefijo PT
            duration = duration_str[2:]
            
            hours = 0
            minutes = 0
            
            # Extraer horas
            if 'H' in duration:
                h_index = duration.index('H')
                hours = int(duration[:h_index])
                duration = duration[h_index+1:]
            
            # Extraer minutos
            if 'M' in duration:
                m_index = duration.index('M')
                minutes = int(duration[:m_index])
            
            return f"{hours}h {minutes}m"
        except:
            return duration_str

# Crear una instancia de la API de Amadeus
amadeus_api = AmadeusAPI()
