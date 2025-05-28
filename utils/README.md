# ChatNomina

ChatNomina es un asistente conversacional inteligente para consultas relacionadas con la nómina, desarrollado como una aplicación web utilizando NiceGUI. El sistema integra modelos de lenguaje avanzados (T5 y BERT) con acceso a SharePoint para proporcionar respuestas precisas sobre información de nómina, normativa laboral y documentación institucional.

## 💡 Características principales

- **Interfaz Web Moderna**: Aplicación web interactiva construida con NiceGUI
- **Autenticación Segura**: Integración con Microsoft Entra ID (MSAL)
- **Acceso a SharePoint**: Consulta de archivos institucionales (.txt y .docx)
- **Modelos de IA Avanzados**:
  - Modelo T5 finetuneado para generación de respuestas
  - Modelo BERT para clasificación de preguntas
  - Sistema de embeddings para búsqueda semántica
- **Procesamiento Inteligente**:
  - Clasificación automática de preguntas
  - Transformaciones personalizadas para datos de nómina
  - Búsqueda semántica en documentos
  - Consulta de normativa laboral colombiana
- **Sistema de Feedback**: Registro y análisis de respuestas incorrectas
- **Logging Detallado**: Sistema completo de registro de operaciones

## 📂 Estructura del proyecto

```
ChatNomina/
├── app.py                 # Aplicación principal
├── test_model.py         # Script de pruebas
├── modelo_finetuneado/   # Modelos entrenados
│   ├── model.safetensors
│   ├── config.json
│   ├── tokenizer_config.json
│   └── bert_model/
├── utils/                # Utilidades y helpers
│   ├── Ollama.py
│   ├── embedding_index.py
│   ├── cache_loader.py
│   ├── data_lookup.py
│   ├── transforms.py
│   ├── faq_qa.py
│   └── web_search.py
├── auth/                 # Configuración de autenticación
├── sharepoint/          # Integración con SharePoint
├── data/                # Datos y consultas
├── feedback/            # Registro de feedback
└── logs/                # Logs de la aplicación
```

## ⚡ Requisitos

- Python 3.8+
- 8GB+ RAM (recomendado para mejor rendimiento)
- Conexión a internet para búsquedas web
- Acceso a SharePoint (para funcionalidades de documentos)

> **Nota**: Las utilidades están optimizadas para funcionar en CPU. El rendimiento puede variar según la capacidad de procesamiento disponible.

## ✨ Instalación

1. Clona el repositorio:
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd ChatNomina
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r utils/requirements.txt
   ```

4. Configura las variables de entorno:
   ```bash
   # .env
   TENANT_ID=tu_tenant_id
   CLIENT_ID=tu_client_id
   SITE_ID=tu_site_id
   DRIVE_ID=tu_drive_id
   FOLDER_PATH=ruta_a_carpeta_sharepoint
   ```

## 🚀 Ejecución

1. Inicia la aplicación:
   ```bash
   python app.py
   ```

2. Abre tu navegador en `http://localhost:8080`

3. Autentícate con tu cuenta Microsoft 365

4. Ingresa tu número de documento para comenzar a hacer consultas

## 🔧 Funcionalidades Disponibles

### Consultas de Nómina
- Cálculo de días de vacaciones pendientes
- Consulta de última consignación
- Información de sueldo actual
- Datos personales y bancarios
- Cálculo de novedades y retención
- Total acumulado pagado

### Documentación y Normativa
- Búsqueda en documentos institucionales
- Consulta de normativa laboral
- FAQ sobre procesos de nómina

### Características Adicionales
- Sistema de feedback para mejorar respuestas
- Logging detallado de operaciones
- Caché de documentos para mejor rendimiento
- Interfaz responsive y moderna

## 🛠️ Desarrollo

### Estructura de Código
- `app.py`: Contiene la clase principal `ChatNominaApp` y la lógica de la interfaz
- `utils/`: Módulos de utilidad para diferentes funcionalidades
- `modelo_finetuneado/`: Modelos de IA entrenados
- `auth/`: Manejo de autenticación Microsoft
- `sharepoint/`: Integración con SharePoint

### Extensión
El proyecto puede ser extendido:
1. Agregando nuevas transformaciones en `utils/transforms.py`
2. Implementando nuevos modelos en `modelo_finetuneado/`
3. Extendiendo la interfaz en `app.py`
4. Agregando nuevas fuentes de datos en `utils/cache_loader.py`

## 📊 Monitoreo y Mantenimiento

- Los logs se almacenan en `logs/app.log`
- El feedback se registra en `feedback/feedback_incorrecto.txt`
- Se recomienda monitorear el uso de memoria y CPU
- Realizar backups periódicos de los modelos y datos

## 📝 Notas de Implementación

- El sistema utiliza modelos T5 y BERT para procesamiento de lenguaje natural
- Se implementa un sistema de caché para optimizar el rendimiento
- Las respuestas se generan considerando el contexto del usuario
- Se mantiene un registro de feedback para mejorar continuamente

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto fue desarrollado como trabajo de grado para la Maestría en Ciencia de Datos. Todos los derechos reservados.

## 📞 Soporte

Para reportar problemas o sugerir mejoras, por favor:
1. Revisa los issues existentes
2. Crea un nuevo issue con una descripción detallada
3. Incluye logs relevantes si es un problema de funcionamiento
