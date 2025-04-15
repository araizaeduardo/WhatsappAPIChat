# WhatsApp API con Flask

Un sistema completo para integrar la API de WhatsApp Business con un backend en Flask, permitiendo recibir y responder mensajes de WhatsApp de forma automatizada.

![WhatsApp API](https://img.shields.io/badge/WhatsApp-API-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 🌟 Características

- ✅ Verificación de webhook de WhatsApp
- 📨 Recepción de mensajes de WhatsApp (texto, imágenes, audio, documentos)
- 📤 Envío de respuestas automáticas
- 🧠 Sistema inteligente de procesamiento de mensajes
- 💾 Almacenamiento de conversaciones
- 🖥️ Panel de administración web para gestionar conversaciones
- 🔄 Actualización en tiempo real de las conversaciones

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

## 💻 Uso

### Recepción de mensajes

El sistema está configurado para recibir automáticamente mensajes de WhatsApp a través del webhook. Cuando un usuario envía un mensaje, el sistema:

1. Procesa el mensaje según su tipo (texto, imagen, audio, documento)
2. Genera una respuesta automática basada en el contenido
3. Almacena la conversación para su posterior consulta
4. Envía la respuesta al usuario

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

## 🧩 Estructura del proyecto

```
whatsapp-flask-api/
├── app.py                  # Aplicación principal de Flask
├── message_handler.py      # Procesador de mensajes
├── requirements.txt        # Dependencias del proyecto
├── .env                    # Variables de entorno
├── conversations/          # Almacenamiento de conversaciones
└── templates/              # Plantillas HTML para el panel de administración
    └── index.html          # Interfaz del panel de administración
```

## 📝 Personalización

### Respuestas automáticas

Puedes personalizar las respuestas automáticas modificando la función `generate_response` en el archivo `message_handler.py`. Actualmente, el sistema responde a:

- Saludos (hola, buenos días, etc.)
- Solicitudes de ayuda (ayuda, comandos, etc.)
- Agradecimientos (gracias, thanks, etc.)
- Comandos específicos (info, contacto)

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
