# Guía de Desarrollo - ChatNomina

## Visión General

Esta guía proporciona información detallada para desarrolladores que deseen contribuir o extender ChatNomina. Incluye instrucciones de configuración, arquitectura, mejores prácticas y flujos de trabajo.

## Requisitos de Desarrollo

### Hardware
- CPU: Procesador de 4+ núcleos (recomendado)
- RAM: 8GB+ (recomendado)
- Almacenamiento: 10GB+ de espacio libre

### Software
- Python 3.8+
- Git
- Editor de código (VS Code recomendado)
- Navegador web moderno

### Herramientas de Desarrollo
- VS Code / PyCharm
- Postman / Insomnia
- DBeaver / pgAdmin
- Redis Commander
- Docker Desktop

## Configuración del Entorno

### 1. Clonar el Repositorio

```bash
git clone https://github.com/empresa/chatnomina.git
cd chatnomina
```

### 2. Configurar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
.\venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar variables
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/chatnomina
REDIS_URL=redis://localhost:6379/0
MODEL_PATH=./models
API_KEY=your_api_key
ENVIRONMENT=development
```

### 4. Configurar Base de Datos

```bash
# Crear base de datos
createdb chatnomina

# Ejecutar migraciones
python manage.py migrate

# Cargar datos iniciales
python manage.py loaddata initial_data.json
```

### 5. Configurar Redis

```bash
# Iniciar Redis
docker run -d -p 6379:6379 redis:6

# Verificar conexión
redis-cli ping
```

## Estructura del Proyecto

```
chatnomina/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   ├── models/
│   │   └── schemas/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── intent/
│   │   ├── entity/
│   │   └── response/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── payroll.py
│   └── utils/
│       ├── __init__.py
│       ├── text.py
│       └── validation.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docs/
│   ├── api.md
│   ├── development.md
│   └── user_guide/
├── scripts/
│   ├── setup.sh
│   └── deploy.sh
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Arquitectura

### Diagrama de Componentes

```mermaid
graph TD
    subgraph Desktop App
        A[Native Window] --> B[UI Components]
        B --> C[Event Handler]
    end

    subgraph Backend
        C --> D[Auth Service]
        C --> E[Chat Service]
        C --> F[Payroll Service]
        C --> G[User Service]
    end

    subgraph Models
        E --> H[Intent Model]
        E --> I[Entity Model]
        E --> J[Response Model]
    end

    subgraph Data
        D --> K[(PostgreSQL)]
        E --> K
        F --> K
        G --> K
        E --> L[(Redis)]
        H --> M[(Model Storage)]
        I --> M
        J --> M
    end
```

### Flujo de Datos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant W as Ventana Nativa
    participant S as Chat Service
    participant M as Models
    participant D as Database
    participant R as Redis

    U->>W: Ingresa mensaje
    W->>S: Procesar mensaje
    S->>M: Clasificar intención
    S->>M: Extraer entidades
    S->>D: Consultar datos
    S->>R: Cachear contexto
    S->>M: Generar respuesta
    S->>W: Actualizar UI
    W->>U: Mostrar respuesta
```

## Desarrollo

### 1. Estilo de Código

#### Python
- PEP 8
- Docstrings (Google style)
- Type hints
- Máximo 88 caracteres por línea
- 4 espacios para indentación

```python
from typing import Dict, List, Optional
from nicegui import ui

class ChatNominaApp:
    """Aplicación nativa de chat para consultas de nómina.
    
    Esta clase maneja la interfaz de usuario nativa y la lógica
    de procesamiento de mensajes.
    """
    
    def __init__(self):
        """Inicializa la aplicación nativa."""
        self.window_size = (450, 750)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario nativa."""
        ui.page('/')(self.main_page)
        ui.run(
            title='ChatNomina',
            native=True,
            window_size=self.window_size
        )
```

#### JavaScript/TypeScript
- ESLint
- Prettier
- JSDoc
- Máximo 80 caracteres por línea
- 2 espacios para indentación

```typescript
interface MessageContext {
  userId: string;
  sessionId?: string;
}

/**
 * Procesa un mensaje del usuario.
 * @param {string} message - Mensaje a procesar.
 * @param {MessageContext} context - Contexto de la conversación.
 * @returns {Promise<MessageResponse>} Respuesta procesada.
 * @throws {Error} Si el mensaje está vacío.
 */
async function processMessage(
  message: string,
  context: MessageContext
): Promise<MessageResponse> {
  if (!message.trim()) {
    throw new Error("El mensaje no puede estar vacío");
  }

  // Procesar mensaje
  return {
    text: "Respuesta procesada",
    confidence: 0.95
  };
}
```

### 2. Testing

#### Unit Tests
```python
# tests/unit/test_chat.py
import pytest
from app.services.chat import ChatService

def test_process_message():
    """Test procesamiento de mensaje."""
    service = ChatService()
    
    # Test caso válido
    response = service.process_message(
        "¿Cuál es mi sueldo?",
        {"user_id": "123"}
    )
    assert response["confidence"] > 0.9
    assert "$" in response["text"]
    
    # Test caso inválido
    with pytest.raises(ValueError):
        service.process_message("", {"user_id": "123"})
```

#### Integration Tests
```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint():
    """Test endpoint de chat."""
    response = client.post(
        "/api/chat/message",
        json={
            "message": "¿Cuál es mi sueldo?",
            "context": {"user_id": "123"}
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert "text" in response.json()
```

#### E2E Tests
```python
# tests/e2e/test_workflow.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_chat_workflow():
    """Test flujo completo de chat."""
    driver = webdriver.Chrome()
    driver.get("http://localhost:3000")
    
    # Login
    driver.find_element(By.ID, "email").send_keys("test@example.com")
    driver.find_element(By.ID, "password").send_keys("password")
    driver.find_element(By.ID, "login").click()
    
    # Chat
    driver.find_element(By.ID, "message").send_keys("¿Cuál es mi sueldo?")
    driver.find_element(By.ID, "send").click()
    
    # Verificar respuesta
    response = driver.find_element(By.CLASS_NAME, "response")
    assert "$" in response.text
    
    driver.quit()
```

### 3. CI/CD

#### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run tests
        run: |
          pytest tests/
          
      - name: Run linting
        run: |
          flake8 app/
          black --check app/
          mypy app/
```

#### Docker
```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/chatnomina
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=chatnomina
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:6
    volumes:
      - redis_data:/data
      
volumes:
  postgres_data:
  redis_data:
```

### 4. Monitoreo

#### Logging
```python
# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    """Configura el sistema de logging para la aplicación nativa."""
    logger = logging.getLogger("chatnomina")
    logger.setLevel(logging.INFO)
    
    # Directorio de logs en la carpeta de la aplicación
    log_dir = Path.home() / "ChatNomina" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Handler para archivo
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(file_handler)
    
    # Handler para consola (ventana nativa)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(console_handler)
    
    return logger
```

#### Métricas
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram
import time

# Métricas
REQUEST_COUNT = Counter(
    "chatnomina_request_total",
    "Total de peticiones",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "chatnomina_request_latency_seconds",
    "Latencia de peticiones",
    ["endpoint"]
)

MODEL_LATENCY = Histogram(
    "chatnomina_model_latency_seconds",
    "Latencia de modelos",
    ["model"]
)

# Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Registrar métricas
    REQUEST_COUNT.labels(
        endpoint=request.url.path,
        method=request.method,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response
```

### 5. Seguridad

#### Autenticación
```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un token JWT."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt
```

#### Validación
```python
# app/utils/validation.py
from pydantic import BaseModel, validator
from typing import Optional

class MessageRequest(BaseModel):
    """Modelo de validación para mensajes."""
    message: str
    context: Optional[dict] = None
    
    @validator("message")
    def message_not_empty(cls, v):
        """Valida que el mensaje no esté vacío."""
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío")
        return v
    
    @validator("context")
    def validate_context(cls, v):
        """Valida el contexto."""
        if v and "user_id" not in v:
            raise ValueError("El contexto debe incluir user_id")
        return v
```

### 6. Despliegue

#### Script de Despliegue
```bash
#!/bin/bash
# scripts/deploy.sh

# Variables
APP_NAME="chatnomina"
ENVIRONMENT=$1
VERSION=$(git describe --tags)

# Validar entorno
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "Entorno inválido. Use: staging o production"
    exit 1
fi

# Construir imagen
docker build -t $APP_NAME:$VERSION .

# Desplegar
if [ "$ENVIRONMENT" == "staging" ]; then
    # Staging
    docker-compose -f docker-compose.staging.yml up -d
else
    # Production
    docker-compose -f docker-compose.prod.yml up -d
fi

# Verificar despliegue
curl -f http://localhost:8000/health || exit 1

echo "Despliegue exitoso: $APP_NAME:$VERSION en $ENVIRONMENT"
```

#### Configuración de Producción
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build: .
    restart: always
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/chatnomina
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        
  db:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=chatnomina
    volumes:
      - postgres_data:/var/lib/postgresql/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        
  redis:
    image: redis:6
    restart: always
    volumes:
      - redis_data:/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        
volumes:
  postgres_data:
  redis_data:
```

## Mejores Prácticas

### 1. Código

- Escribir código limpio y mantenible
- Seguir principios SOLID
- Documentar funciones y clases
- Usar type hints
- Escribir tests unitarios
- Mantener cobertura de tests > 80%
- Revisar código antes de commit
- Usar branches para features

### 2. Git

- Usar branches descriptivos
- Hacer commits atómicos
- Escribir mensajes claros
- Revisar cambios antes de push
- Mantener historial limpio
- Usar tags para versiones

### 3. Seguridad

- No exponer secretos
- Validar entradas
- Sanitizar salidas
- Usar HTTPS
- Implementar rate limiting
- Mantener dependencias actualizadas
- Escanear vulnerabilidades

### 4. Performance

- Optimizar consultas DB
- Usar caché
- Implementar paginación
- Comprimir respuestas
- Monitorear recursos
- Optimizar modelos
- Usar async/await

## Troubleshooting

### 1. Logs

#### Niveles de Log
- DEBUG: Información detallada
- INFO: Confirmación de operaciones
- WARNING: Situaciones inesperadas
- ERROR: Errores manejables
- CRITICAL: Errores críticos

#### Formato
```
2024-03-15 12:00:00,123 - chatnomina - INFO - Mensaje procesado
2024-03-15 12:00:00,124 - chatnomina - ERROR - Error en procesamiento
```

### 2. Errores Comunes

#### Database
- Connection refused
- Timeout
- Deadlock
- Constraint violation

#### Redis
- Connection refused
- Memory limit
- Key expiration

#### Models
- CUDA out of memory
- Model not found
- Invalid input
- Low confidence

### 3. Soluciones

#### Database
```python
# Reintentar conexión
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def get_db_connection():
    """Obtiene conexión a base de datos con reintentos."""
    return create_engine(DATABASE_URL)
```

#### Redis
```python
# Manejar errores de Redis
from redis.exceptions import RedisError

try:
    redis_client.set("key", "value")
except RedisError as e:
    logger.error(f"Error de Redis: {e}")
    # Fallback a base de datos
    db_client.set("key", "value")
```

#### Models
```python
# Manejar errores de modelos
try:
    response = model.predict(input)
except RuntimeError as e:
    if "CUDA out of memory" in str(e):
        # Liberar memoria
        torch.cuda.empty_cache()
        # Reintentar con batch más pequeño
        response = model.predict(input, batch_size=1)
    else:
        raise
```

## Recursos

### 1. Documentación

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Redis](https://redis.io/documentation)
- [PyTorch](https://pytorch.org/docs/)
- [Docker](https://docs.docker.com/)

### 2. Herramientas

- [Postman](https://www.postman.com/)
- [DBeaver](https://dbeaver.io/)
- [Redis Commander](https://github.com/joeferner/redis-commander)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)

### 3. Comunidad

- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Issues](https://github.com/empresa/chatnomina/issues)
- [Discord](https://discord.gg/chatnomina)
- [Blog](https://blog.chatnomina.com/)

## Contribuir

### 1. Proceso

1. Fork repositorio
2. Crear branch
3. Desarrollar cambios
4. Escribir tests
5. Actualizar docs
6. Crear PR
7. Revisión
8. Merge

### 2. Guías

- [Guía de Contribución](CONTRIBUTING.md)
- [Código de Conducta](CODE_OF_CONDUCT.md)
- [Guía de Estilo](STYLE_GUIDE.md)

### 3. Contacto

- Email: dev@chatnomina.com
- Slack: #dev-chatnomina
- GitHub: @chatnomina/dev 

## Solución de Problemas Comunes

### Problemas de Interfaz
- Si la ventana no se abre, verifica que no haya otra instancia ejecutándose
- Para problemas de rendimiento en la interfaz, asegúrate de tener los drivers gráficos actualizados
- Si la ventana se cierra inesperadamente, revisa los logs en la carpeta de la aplicación

### Problemas de Rendimiento
- Si experimentas lentitud en las respuestas, considera aumentar la RAM disponible
- Para mejorar el rendimiento, puedes ajustar los parámetros de batch_size en la configuración
- En caso de problemas de memoria, reduce el tamaño de los lotes de procesamiento

## Optimización
- Utiliza el modo de procesamiento por lotes para mejorar el rendimiento
- Ajusta el tamaño de los lotes según la memoria disponible
- Considera usar caché para respuestas frecuentes
- Implementa compresión de modelos para reducir el uso de memoria
- Optimiza el renderizado de la interfaz nativa para mejor rendimiento 