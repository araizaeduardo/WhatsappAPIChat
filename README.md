# WhatsApp API para Agencia de Viajes

Un sistema completo para integrar la API de WhatsApp Business con un backend en Flask, especializado para agencias de viajes. Permite recibir consultas sobre tours y vuelos, y responder automáticamente con información relevante.

![WhatsApp API](https://img.shields.io/badge/WhatsApp-API-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 🌟 Características

### Funcionalidades de WhatsApp
- ✅ Verificación de webhook de WhatsApp
- 📨 Recepción de mensajes de WhatsApp (texto, imágenes, audio, documentos)
- 📤 Envío de respuestas automáticas
- 🧠 Sistema inteligente de procesamiento de mensajes
- 💾 Almacenamiento de conversaciones
- 💻 Panel de administración web para gestionar conversaciones
- 🔄 Actualización en tiempo real de las conversaciones
- 🔔 Notificaciones visuales y sonoras para nuevos mensajes
- 📅 Manejo robusto de diferentes formatos de fecha

### Funcionalidades de Agencia de Viajes
- 🏝️ Base de datos de tours y paquetes vacacionales
- ✈️ Integración con API de Amadeus para búsqueda de vuelos
- 🔍 Búsqueda de tours por destino
- 📅 Consulta de disponibilidad y precios
- 💬 Comandos específicos para consultas de viajes

## 📋 Requisitos

- Python 3.8+
- Flask
- Cuenta de WhatsApp Business API
- Ngrok o un servicio similar para exponer el servidor local

## 🚀 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/whatsapp-flask-api.git
   cd whatsapp-flask-api
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno en un archivo `.env`:
   ```
   # WhatsApp Business API de Meta
   WHATSAPP_TOKEN=tu_token_de_whatsapp
   WHATSAPP_PHONE_ID=tu_phone_id
   VERIFY_TOKEN=tu_token_de_verificacion
   ```

4. Inicia el servidor:
   ```bash
   python app.py
   ```

5. Expón tu servidor local con Ngrok:
   ```bash
   ngrok http 5000
   ```

## 🔧 Configuración de WhatsApp Business API

1. Ve al [Panel de desarrolladores de Meta](https://developers.facebook.com/)
2. Crea una aplicación o selecciona una existente
3. Configura la API de WhatsApp Business
4. En la sección de webhooks, configura:
   - URL de callback: `https://tu-dominio-ngrok.ngrok-free.app/webhook`
   - Token de verificación: El mismo que configuraste en `.env`
   - Selecciona los campos de suscripción (al menos "messages")

## 💬 Uso

### Recepción de mensajes

El sistema está configurado para recibir automáticamente mensajes de WhatsApp a través del webhook. Cuando un usuario envía un mensaje, el sistema:

1. Procesa el mensaje según su tipo (texto, imagen, audio, documento)
2. Identifica si es una consulta sobre tours, vuelos u otra información
3. Genera una respuesta automática basada en el contenido y contexto
4. Almacena la conversación para su posterior consulta
5. Envía la respuesta al usuario con la información solicitada

### Panel de administración

Accede al panel de administración visitando la URL raíz de tu aplicación:
```
https://tu-dominio-ngrok.ngrok-free.app/
```

Desde aquí podrás:
- Ver todas las conversaciones
- Leer los mensajes de cada conversación
- Enviar mensajes a los usuarios
- Monitorear la actividad en tiempo real

## 📝 Estructura del proyecto

```
whatsapp-flask-api/
├── app.py                  # Aplicación principal de Flask
├── message_handler.py      # Procesador de mensajes
├── amadeus_api.py          # Integración con API de Amadeus para vuelos
├── tours_db.py             # Base de datos de tours y funciones de búsqueda
├── requirements.txt        # Dependencias del proyecto
├── .env                    # Variables de entorno
├── .env.example            # Ejemplo de variables de entorno
├── .gitignore              # Archivos a ignorar en Git
├── LICENSE                 # Licencia del proyecto
├── README.md               # Documentación del proyecto
├── kanban_whatsapp.md      # Planificación del proyecto
├── conversations/          # Almacenamiento de conversaciones
└── templates/              # Plantillas HTML para el panel de administración
    └── index.html          # Interfaz del panel de administración
```

## 🧱 Personalización

### Respuestas automáticas

Puedes personalizar las respuestas automáticas modificando la función `generate_response` en el archivo `message_handler.py`. Actualmente, el sistema responde a:

- Saludos (hola, buenos días, etc.)
- Solicitudes de ayuda (ayuda, comandos, etc.)
- Agradecimientos (gracias, thanks, etc.)
- Comandos específicos (info, contacto)

### Comandos de viajes

El sistema reconoce comandos específicos para consultas de viajes:

- `tours`: Muestra todos los tours disponibles
- `tour [destino]`: Busca tours para un destino específico
- `detalles tour [ID]`: Muestra detalles de un tour específico
- `vuelos [origen] a [destino] [fecha]`: Busca vuelos disponibles
- `vuelos [origen] a [destino] [fecha ida] [fecha regreso]`: Busca vuelos de ida y vuelta

### Sistema de notificaciones

El panel de administración incluye un sistema completo de notificaciones para nuevos mensajes:

- **Notificación visual**: Contactos con nuevos mensajes parpadean con un efecto de animación
- **Indicador de punto verde**: Muestra un punto verde pulsante junto a contactos con mensajes nuevos
- **Borde izquierdo verde**: Resalta visualmente los contactos con mensajes sin leer
- **Notificación de sonido**: Reproduce un sonido de alerta cuando llega un nuevo mensaje
- **Titilación del título**: El título de la página parpadea para alertar sobre nuevos mensajes
- **Notificaciones del navegador**: Muestra notificaciones del sistema cuando la página no está activa

### Interfaz de administración

La interfaz de administración está construida con Bootstrap y puede ser personalizada modificando el archivo `templates/index.html`.

## 🛣️ Roadmap

Consulta nuestro [Kanban](kanban_whatsapp.md) para ver las próximas características y mejoras planeadas.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para sugerir cambios o mejoras.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ⚠️ Aviso importante

Este proyecto es para fines educativos y de desarrollo. Asegúrate de cumplir con los términos de servicio de WhatsApp Business API y las políticas de Meta al utilizar esta aplicación.

---

Desarrollado con ❤️ usando Flask y la API de WhatsApp Business
