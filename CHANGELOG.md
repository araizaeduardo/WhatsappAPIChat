# Changelog - WhatsApp Travel Agency API

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2025-04-16

### Corregido
- Sistema de permisos basado en roles mejorado
- Acceso correcto a conversaciones para usuarios con rol 'staff'
- Restricción de acceso a administración de tours solo para 'staff' y 'admin'
- Jerarquía de permisos claramente definida (admin > staff > user)

### Mejorado
- Implementación de decoradores de protección para rutas
- Separación clara de responsabilidades por rol

## [1.3.0] - 2025-04-16

### Añadido
- Sistema completo de administración de usuarios (CRUD)
- Formulario para crear nuevos usuarios con validación
- Formulario para editar usuarios existentes
- Función para eliminar usuarios con confirmación
- Protección para evitar eliminar el último administrador
- Protección para evitar que un usuario elimine su propia cuenta
- Opción para activar/desactivar usuarios

### Mejorado
- Interfaz de administración de usuarios con acciones
- Validación de formularios con JavaScript
- Seguridad en la gestión de usuarios
- Actualización del archivo .gitignore para mayor seguridad

## [1.2.0] - 2025-04-16

### Añadido
- Sistema completo de autenticación de usuarios con SQLite
- Protección de rutas administrativas con decoradores
- Página de inicio de sesión con recordatorio de sesión
- Gestión segura de sesiones con tokens y cookies
- Control de acceso basado en roles (admin, staff, user)
- Función para cambiar contraseña con validación
- Panel de administración de usuarios (solo para administradores)
- Información de usuario en el panel principal
- Menú desplegable para opciones de usuario

### Cambiado
- Mejorada la seguridad general de la aplicación
- Actualizada la interfaz para mostrar información del usuario actual
- Protegidas todas las rutas administrativas y API con autenticación

### Corregido
- Solucionado problema de carga de mensajes en el panel de conversaciones
- Corregida la URL para cargar mensajes de `/api/conversations/` a `/api/messages/`

## [1.1.0] - 2025-04-15

### Añadido
- Sistema de administración CRUD para tours con SQLite
- Migración de la base de datos de tours de memoria a SQLite
- Nuevas plantillas HTML para la gestión de tours
- Botón para acceder al administrador de tours desde el panel principal
- Estructura base común para todas las páginas (base.html)
- Validación de datos y mensajes de confirmación en formularios
- Mensajes flash para operaciones CRUD
- Formularios dinámicos para añadir múltiples elementos en tours

### Cambiado
- Mejorado el manejo de diferentes formatos de fecha y timestamp
- Actualizado el estilo visual para usar Bootstrap 5 y Font Awesome
- Optimizado el formato de visualización de fechas (hoy, ayer, fecha completa)
- Actualizada la documentación (README.md y kanban_whatsapp.md)

### Corregido
- Solucionado el problema de "Invalid Date" en el panel de administración
- Mejorado el acceso a las columnas de la base de datos SQLite

## [1.0.0] - 2025-04-10

### Añadido
- Verificación y manejo de webhook de WhatsApp
- Recepción de mensajes de WhatsApp (texto, imágenes, audio, documentos)
- Envío de respuestas automáticas
- Sistema inteligente de procesamiento de mensajes
- Almacenamiento de conversaciones en archivos JSON
- Panel de administración web para gestionar conversaciones
- Actualización en tiempo real de las conversaciones
- Base de datos de tours y paquetes vacacionales en memoria
- Integración con API de Amadeus para búsqueda de vuelos
- Búsqueda de tours por destino
- Comandos específicos para consultas de tours y vuelos
- Sistema de notificaciones visuales y sonoras para nuevos mensajes
- Documentación completa (README.md)
- Tablero Kanban para planificación (kanban_whatsapp.md)

### Configurado
- Entorno de desarrollo con Python y Flask
- Ngrok para exponer servidor local
- Variables de entorno en archivo .env
- Estructura básica del proyecto Flask
