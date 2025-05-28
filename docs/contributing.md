# Guía de Contribución - ChatNomina

## Introducción

Gracias por tu interés en contribuir a ChatNomina. Este documento proporciona las directrices y el proceso para contribuir al proyecto.

## Código de Conducta

### 1. Nuestros Compromisos

- Ambiente inclusivo y acogedor
- Respeto mutuo
- Aceptación de críticas constructivas
- Enfoque en el bienestar de la comunidad
- Empatía hacia otros miembros

### 2. Nuestras Responsabilidades

- Mantener un ambiente positivo
- Resolver conflictos de manera pacífica
- Aceptar responsabilidad por nuestras acciones
- Escuchar a otros miembros

### 3. Aplicación

- Moderación de comentarios
- Advertencias temporales
- Suspensión temporal
- Expulsión permanente

## Proceso de Contribución

### 1. Antes de Contribuir

#### Requisitos
- Cuenta de GitHub
- Git instalado
- Entorno de desarrollo configurado
- Conocimiento básico de Python/JavaScript

#### Preparación
1. Fork del repositorio
2. Clone local
3. Configurar upstream
4. Crear rama de desarrollo

```bash
# Fork y clone
git clone https://github.com/your-username/chatnomina.git
cd chatnomina

# Configurar upstream
git remote add upstream https://github.com/original-org/chatnomina.git

# Crear rama
git checkout -b feature/your-feature
```

### 2. Desarrollo

#### Estilo de Código

##### Python
- PEP 8
- Docstrings (Google Style)
- Type hints
- Tests unitarios

```python
def process_message(message: str) -> Dict[str, Any]:
    """Procesa un mensaje del usuario.

    Args:
        message: El mensaje a procesar.

    Returns:
        Dict con la respuesta procesada.

    Raises:
        ValueError: Si el mensaje está vacío.
    """
    if not message:
        raise ValueError("El mensaje no puede estar vacío")

    return {"response": "Procesado"}
```

##### JavaScript/TypeScript
- ESLint
- Prettier
- JSDoc
- Tests unitarios

```typescript
/**
 * Procesa un mensaje del usuario.
 * @param {string} message - El mensaje a procesar.
 * @returns {Promise<Response>} La respuesta procesada.
 * @throws {Error} Si el mensaje está vacío.
 */
async function processMessage(message: string): Promise<Response> {
  if (!message) {
    throw new Error("El mensaje no puede estar vacío");
  }

  return { response: "Procesado" };
}
```

#### Commits

##### Formato
```
<tipo>(<alcance>): <descripción>

[cuerpo opcional]

[pie opcional]
```

##### Tipos
- `feat`: Nueva característica
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formato
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Mantenimiento

##### Ejemplos
```
feat(auth): implementa autenticación OAuth2

- Agrega soporte para Google OAuth
- Implementa refresh tokens
- Agrega validación de tokens

Closes #123
```

```
fix(api): corrige error en procesamiento de mensajes

- Corrige validación de mensajes vacíos
- Mejora manejo de errores
- Agrega logging

Fixes #456
```

### 3. Pull Requests

#### Proceso
1. Actualizar fork
2. Crear rama
3. Desarrollar cambios
4. Ejecutar tests
5. Crear PR
6. Revisión
7. Merge

```bash
# Actualizar fork
git fetch upstream
git checkout main
git merge upstream/main

# Crear rama
git checkout -b feature/your-feature

# Desarrollar cambios
# ...

# Ejecutar tests
pytest
npm test

# Commit y push
git add .
git commit -m "feat: implementa nueva característica"
git push origin feature/your-feature
```

#### Template
```markdown
## Descripción

[Descripción detallada de los cambios]

## Tipo de Cambio

- [ ] Nueva característica
- [ ] Corrección de bug
- [ ] Mejora de documentación
- [ ] Refactorización
- [ ] Otro

## Checklist

- [ ] Tests agregados/actualizados
- [ ] Documentación actualizada
- [ ] Código sigue estándares
- [ ] Commits siguen convención
- [ ] PR actualizado con main

## Screenshots (opcional)

[Capturas de pantalla si aplica]

## Notas Adicionales

[Notas o consideraciones adicionales]
```

### 4. Revisión de Código

#### Checklist
- [ ] Código sigue estándares
- [ ] Tests pasan
- [ ] Documentación actualizada
- [ ] Sin código muerto
- [ ] Manejo de errores
- [ ] Logging apropiado
- [ ] Seguridad considerada
- [ ] Rendimiento optimizado

#### Proceso
1. Revisión automática
2. Revisión por pares
3. Comentarios
4. Cambios solicitados
5. Aprobación
6. Merge

## Desarrollo Local

### 1. Configuración

#### Backend
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar variables
cp .env.example .env
nano .env
```

#### Frontend
```bash
# Instalar dependencias
cd frontend
npm install

# Configurar variables
cp .env.example .env
nano .env
```

### 2. Desarrollo

#### Backend
```bash
# Ejecutar servidor
uvicorn app.main:app --reload

# Ejecutar tests
pytest

# Ejecutar linting
flake8
black .
mypy .
```

#### Frontend
```bash
# Ejecutar servidor
npm run dev

# Ejecutar tests
npm test

# Ejecutar linting
npm run lint
npm run format
```

### 3. Docker

```bash
# Construir imágenes
docker-compose build

# Ejecutar servicios
docker-compose up

# Ejecutar tests
docker-compose run --rm api pytest
docker-compose run --rm frontend npm test
```

## Documentación

### 1. Estilo

- Markdown
- Claridad
- Ejemplos
- Diagramas
- Enlaces

### 2. Estructura

```
docs/
├── api/
│   ├── endpoints.md
│   └── models.md
├── user_guide/
│   ├── getting_started.md
│   └── features.md
└── technical/
    ├── architecture.md
    └── deployment.md
```

### 3. Ejemplos

```markdown
# Título

## Descripción

Descripción detallada del componente o característica.

## Uso

```python
from chatnomina import Client

client = Client()
response = client.send_message("¿Cuál es mi sueldo?")
print(response)
```

## Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| message | str | Mensaje a procesar |
| context | dict | Contexto adicional |

## Retornos

| Tipo | Descripción |
|------|-------------|
| dict | Respuesta procesada |

## Ejemplos

### Ejemplo 1
```python
response = client.send_message("¿Cuál es mi sueldo?")
# {'response': 'Tu sueldo es $3,000,000', 'confidence': 0.95}
```

### Ejemplo 2
```python
response = client.send_message("¿Cuántos días de vacaciones me quedan?")
# {'response': 'Te quedan 15 días de vacaciones', 'confidence': 0.98}
```
```

## Soporte

### 1. Canales

- GitHub Issues
- GitHub Discussions
- Slack
- Email

### 2. Proceso

1. Buscar en issues existentes
2. Revisar documentación
3. Crear nuevo issue
4. Proporcionar detalles
5. Seguimiento

### 3. Template de Issue

```markdown
## Descripción

[Descripción detallada del problema o solicitud]

## Comportamiento Esperado

[Lo que debería suceder]

## Comportamiento Actual

[Lo que sucede actualmente]

## Pasos para Reproducir

1. [Primer paso]
2. [Segundo paso]
3. [Y así sucesivamente...]

## Contexto Adicional

- Versión: [e.g. 1.0.0]
- Sistema Operativo: [e.g. Windows 10]
- Navegador: [e.g. Chrome 90]
- Otros detalles relevantes

## Screenshots (opcional)

[Capturas de pantalla si aplica]
```

## Reconocimiento

### 1. Contribuidores

- Lista de contribuidores
- Badges
- Agradecimientos
- Sponsors

### 2. Proceso

1. PR aceptado
2. Agregar a lista
3. Actualizar README
4. Mención en release

### 3. Niveles

- 🌟 Contribuidor
- 🌟🌟 Colaborador
- 🌟🌟🌟 Mantenedor
- 🌟🌟🌟🌟 Sponsor 