# ChatNomina - Sistema de Chat Inteligente para Consultas de Nómina

## Descripción
ChatNomina es un sistema de chat inteligente diseñado para responder consultas relacionadas con nómina, utilizando modelos de lenguaje avanzados y procesamiento de lenguaje natural. El sistema integra múltiples fuentes de información, incluyendo documentos de SharePoint y normativa web, para proporcionar respuestas precisas y contextualizadas.

## Características Principales
- 💬 Chat interactivo con modelo T5 fine-tuned
- 🧠 Clasificación de preguntas con BERT
- 📁 Integración con SharePoint para acceso a documentos
- 📊 Sistema de feedback para mejora continua
- 🔍 Búsqueda en normativa web
- 🔐 Autenticación segura con Microsoft Azure AD

## Estructura del Proyecto
```
ChatNomina/
├── app.py                 # Aplicación principal
├── test_model.py         # Scripts de prueba del modelo
├── modelo_finetuneado/   # Modelos entrenados
├── utils/                # Utilidades y helpers
├── feedback/            # Sistema de feedback
├── logs/               # Registros de la aplicación
├── nlp/               # Procesamiento de lenguaje natural
├── sharepoint/       # Integración con SharePoint
├── data/            # Datos y recursos
├── auth/           # Autenticación y autorización
└── docs/          # Documentación detallada
```

## Requisitos
- Python 3.8+
- CUDA (opcional, para aceleración GPU)
- Acceso a SharePoint
- Credenciales de Azure AD

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd ChatNomina
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear un archivo `.env` con las siguientes variables:
```env
TENANT_ID=your_tenant_id
CLIENT_ID=your_client_id
SITE_ID=your_site_id
DRIVE_ID=your_drive_id
FOLDER_PATH=your_folder_path
```

## Uso
1. Iniciar la aplicación:
```bash
python app.py
```

2. Abrir el navegador en `http://localhost:8080`

3. Autenticarse con las credenciales de Microsoft

4. Comenzar a realizar consultas sobre nómina

## Ejemplos de Consultas
- "¿Cuál es mi sueldo actual?"
- "¿Cuántos días de vacaciones me quedan?"
- "¿Cuál fue mi última consignación?"
- "¿Cuál es la normativa sobre horas extras?"

## Documentación
La documentación detallada se encuentra en el directorio `docs/`:
- [Guía de Usuario](docs/user_guide.md)
- [Documentación Técnica](docs/technical.md)
- [API Reference](docs/api.md)
- [Guía de Desarrollo](docs/development.md)

## Contribución
1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto
[Tu Nombre] - [Tu Email]
Project Link: [https://github.com/yourusername/ChatNomina](https://github.com/yourusername/ChatNomina) 