"""
Base de datos simple para tours y paquetes turísticos.
"""

# Base de datos de tours (en un entorno real, esto estaría en una base de datos como SQLite, MySQL, etc.)
TOURS = [
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
        "includes": ["Hotel 4 estrellas", "Desayunos", "Tour en catamarán", "Snorkel"],
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

def get_all_tours():
    """
    Obtiene todos los tours disponibles.
    
    Returns:
        list: Lista de todos los tours
    """
    return TOURS

def search_tours(query):
    """
    Busca tours que coincidan con la consulta.
    
    Args:
        query (str): Consulta de búsqueda
        
    Returns:
        list: Lista de tours que coinciden con la consulta
    """
    query = query.lower()
    results = []
    
    for tour in TOURS:
        # Buscar en nombre, descripción, ubicación y etiquetas
        if (query in tour["name"].lower() or 
            query in tour["description"].lower() or 
            query in tour["location"].lower() or 
            any(query in tag for tag in tour["tags"])):
            results.append(tour)
    
    return results

def get_tour_by_id(tour_id):
    """
    Obtiene un tour por su ID.
    
    Args:
        tour_id (str): ID del tour
        
    Returns:
        dict: Tour encontrado o None si no existe
    """
    for tour in TOURS:
        if tour["id"] == tour_id:
            return tour
    
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
        f"🗓️ *Duración:* {tour['duration']}\n"
        f"📍 *Ubicación:* {tour['location']}\n"
        f"💰 *Precio:* ${tour['price']} {tour['currency']}\n"
        f"🗓️ *Disponibilidad:* {tour['availability']}\n\n"
        f"✅ *Incluye:*\n{includes}\n\n"
        f"🔍 *ID del tour:* {tour['id']}\n\n"
        f"Para reservar este tour, responde con 'reservar {tour['id']}'"
    )
