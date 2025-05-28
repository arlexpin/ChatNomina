# ChatNomina - Sistema de Chat Inteligente para Consultas de Nómina

[![CI/CD Pipeline](https://github.com/arlexpin/ChatNomina/actions/workflows/ci.yml/badge.svg)](https://github.com/arlexpin/ChatNomina/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/chatnomina/badge/?version=latest)](https://chatnomina.readthedocs.io/en/latest/?badge=latest)

## Descripción

ChatNomina es un sistema de chat inteligente desarrollado como parte del Proyecto de Grado II de la Maestría en Ciencias de Datos de la Universidad Icesi. El sistema está diseñado para responder consultas relacionadas con nómina, utilizando modelos de lenguaje avanzados y procesamiento de lenguaje natural. El sistema integra múltiples fuentes de información, incluyendo documentos de SharePoint y normativa web, para proporcionar respuestas precisas y contextualizadas.

## Características Principales

- 💬 Chat interactivo con modelo T5 fine-tuned para respuestas específicas de nómina
- 🧠 Clasificación de preguntas con BERT para categorización precisa
- 📁 Integración con SharePoint para acceso a documentos corporativos
- 📊 Sistema de feedback para mejora continua del modelo
- 🔍 Búsqueda en normativa web y documentos oficiales
- 🔐 Autenticación segura con Microsoft Azure AD
- 📈 Dashboard de métricas y uso del sistema
- 🔄 Pipeline de CI/CD automatizado
- 🖥️ Interfaz nativa de escritorio (no web)

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
└── docs/          # Documentación detallada (Anexos del trabajo de grado)
```

## Requisitos

- Python 3.8+
- 8GB+ RAM (recomendado para mejor rendimiento)
- Acceso a SharePoint
- Credenciales de Azure AD

> **Nota sobre rendimiento**: El sistema está optimizado para funcionar en CPU. Aunque el rendimiento puede ser más lento que en GPU, el sistema está diseñado para funcionar eficientemente en entornos sin aceleración por hardware.

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

2. Se abrirá una ventana nativa de ChatNomina
3. Autenticarse con las credenciales de Microsoft
4. Ingresar el número de documento
5. Comenzar a realizar consultas sobre nómina

> **Nota**: La aplicación se ejecuta como una ventana nativa de escritorio, no como una aplicación web. Esto proporciona una mejor experiencia de usuario y mayor seguridad al mantener los datos localmente.

## Ejemplos de Consultas

- "¿Cuál es mi sueldo actual?"
- "¿Cuántos días de vacaciones me quedan?"
- "¿Cuál fue mi última consignación?"
- "¿Cuál es la normativa sobre horas extras?"

## Documentación

La documentación detallada se encuentra en el directorio `docs/`:

- [Guía de Usuario](docs/user_guide/user_guide.md)
- [Documentación Técnica](docs/technical/technical.md)
- [Arquitectura del Sistema](docs/technical/architecture.md)
- [Guía de Desarrollo](docs/technical/development.md)
- [Seguridad](docs/technical/security.md)
- [Despliegue](docs/technical/deployment.md)
- [API Reference](docs/api/api.md)

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

Para más detalles sobre el proceso de contribución, consulta nuestra [Guía de Contribución](docs/contributing.md).

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Arlex Pino - apino@icesi.edu.co

- Project Link: [https://github.com/arlexpin/ChatNomina](https://github.com/arlexpin/ChatNomina)
- Universidad Icesi - Maestría en Ciencias de Datos
- Proyecto de Grado II - 2024

## Agradecimientos

- Universidad Icesi
- Maestría en Ciencias de Datos
- Profesores y asesores del proyecto en especial a mi tutor Uram Anibal Sosa
- Equipo de desarrollo y colaboradores
