
**Proyecto DELTA** es una plataforma integral de arquitectura desacoplada diseñada para la automatización, gestión y trazabilidad operativa de simulaciones de Naciones Unidas (Modelos ONU). A través de un enfoque basado en la transformación digital y el procesamiento de datos en tiempo real, **Proyecto DELTA** articula una interfaz web dinámica, un middleware de servicios REST y un núcleo de persistencia en la nube, optimizando de manera eficiente los flujos de preinscripción, validación de legajos institucionales, acreditación presencial y control financiero.

# 🏫 Sistema Integral de Gestión e Inscripción - Modelos ONU

Ecosistema integral diseñado para la automatización, inscripción, acreditación y gestión de delegaciones escolares en eventos de simulaciones de Naciones Unidas (Modelos ONU).

Este proyecto conecta una interfaz ágil en Streamlit con un backend ligero en Google Apps Script, utilizando Google Sheets como base de datos en tiempo real y Google Drive para el almacenamiento de comprobantes y documentación médica.

---

## 🏗️ Arquitectura del Sistema

El sistema opera bajo un modelo desacoplado de tres capas:

+--------------------------------+
|   1. FRONTEND (Streamlit)      |
|   • Preinscripción por Secciones|
|   • Carga de Legajo y Fichas   |
|   • Terminal de Acreditación   |
+----------------┬---------------+
| Peticiones HTTP (GET / POST)
v
+--------------------------------+
| 2. MIDDLEWARE / API (AppsScript)|
| • Ruteo de acciones (JSON API) |
| • Lógica de negocio y Cupos    |
| • Servicio de Mails (GmailApp) |
+----------------┬---------------+
| Lectura y Escritura
v
+--------------------------------+
|  3. BACKEND (Sheets & Drive)   |
|  • Base de Datos Relacional    |
|  • Almacenamiento de Legajos   |
+--------------------------------+

---

### 1. Frontend (Streamlit — Python)

Interfaz web accesible para las instituciones educativas y el equipo organizador:

* Preinscripción Institucional: Selección dinámica de delegaciones agrupadas por secciones (Asamblea General, Consejo de Seguridad, Foro de Davos, Prensa) con cálculo de cupos y límites parametrizados.
* Carga de Nómina y Legajos: Subida de fichas médicas y autorizaciones firmadas (convertidas a Base64) con alertas de recepción y panel de comentarios por alumno.
* Cierre de Carga: Botón de confirmación total que notifica al Secretariado e inicia el flujo de revisión.
* Módulo de Acreditación Presencial: Terminal para acreditación en vivo por DNI durante el evento.

### 2. Middleware & API (Google Apps Script — JavaScript)

Servidor intermedio expuesto como Web App REST que gestiona la lógica del negocio:

* API RESTful: Procesa solicitudes GET y POST serializadas en formato JSON.
* Gestión de Archivos: Recibe documentos en Base64, genera archivos binarios en Google Drive, ajusta permisos de visibilidad y retorna los IDs y URLs correspondientes.
* Notificaciones Automáticas: Envío de correos electrónicos de confirmación mediante GmailApp al cerrar cargas o registrar comprobantes.

### 3. Backend & Base de Datos (Google Sheets & Google Drive)

Persistencia de datos estructurada en tablas dentro de Google Sheets:

* PARAMETROS_MODELOS: Definición de ediciones activas y límites globales.
* PARAMETROS_COMITES: Configuración de comisiones, cupos por banca (integrantes_por_banca) y tope de delegaciones por tipo (max_delegaciones_seccion).
* DELEGACIONES: Registro de escuelas, contactos docentes, claves de acceso (secret_hash) y desgloses solicitados.
* NOMINAS: Registro de estudiantes, asignaciones de países, estados médicos, comentarios e IDs de archivos en Drive.
* PAGOS / ACREDITACIONES: Control financiero y libro de ingresos en tiempo real.

---

## 🛠️ Configuración e Instalación

### Requisitos Previos

* Python 3.9+
* Una cuenta de Google con acceso a Google Sheets y Google Drive.

### 1. Configuración del Backend (Google Apps Script)

1. Abre tu hoja de cálculo en Google Sheets y ve a Extensiones > Apps Script.
2. Copia el código de Code.gs en el editor.
3. Haz clic en Implementar > Nueva implementación.
4. Selecciona el tipo Aplicación web:
* Ejecutar como: Tu cuenta (Yo).
* Quién tiene acceso: Cualquier persona (Anyone).


5. Copia la URL de la aplicación web desplegada ([https://script.google.com/macros/s/.../exec](https://www.google.com/search?q=https://script.google.com/macros/s/.../exec)).

### 2. Configuración de Variables de Entorno (Secrets)

Para no exponer la URL de tu API en repositorios públicos, configura los secretos de Streamlit.

En desarrollo local, crea el archivo .streamlit/secrets.toml:
API_URL = "[https://script.google.com/macros/s/TU_SCRIPT_ID/exec](https://www.google.com/search?q=https://script.google.com/macros/s/TU_SCRIPT_ID/exec)"
admin_logueado = "tu_clave_administrador_2026"

En Streamlit Community Cloud, agrega estas mismas claves dentro de Settings > Secrets en el panel de control de tu aplicación.

### 3. Instalación Local del Frontend

# Clonar el repositorio

git clone [https://github.com/tu-usuario/gestion-modelos-onu.git](https://www.google.com/search?q=https://github.com/tu-usuario/gestion-modelos-onu.git)
PROYECTO DELTA 
Aquí tienes un párrafo de presentación institucional y profesional para el **Proyecto DELTA**:

"**Proyecto DELTA** es una plataforma integral de arquitectura desacoplada diseñada para la automatización, gestión y trazabilidad operativa de simulaciones de Naciones Unidas (Modelos ONU). A través de un enfoque basado en la transformación digital y el procesamiento de datos en tiempo real, **Proyecto DELTA** articula una interfaz web dinámica, un middleware de servicios REST y un núcleo de persistencia en la nube, optimizando de manera eficiente los flujos de preinscripción, validación de legajos institucionales, acreditación presencial y control financiero."

cd gestion-modelos-onu

# Instalar dependencias

pip install -r requirements.txt

# Ejecutar la aplicación

streamlit run app.py

---

## 📋 Estructura del Repositorio

├── .streamlit/
│   └── secrets.toml          # Variables de entorno locales (git-ignored)
├── app.py                    # Aplicación principal de Streamlit (Frontend)
├── Code.gs                   # Backend API en Google Apps Script
├── requirements.txt          # Dependencias de Python (streamlit, requests, pandas)
└── README.md                 # Documentación del proyecto

---

## 🔐 Seguridad y Privacidad

* Secretos aislados: Ninguna URL de infraestructura ni contraseña administrativa está expuesta en el código fuente de Python.
* Autenticación por Hash: Las instituciones acceden a su legajo escolar mediante su correo docente registrado y su clave privada (secret_hash).
* Protección de Datos Sensibles: Los archivos subidos (fichas médicas y autorizaciones) se almacenan de forma segura en Google Drive, guardando únicamente referencias relacionales en la base de datos.