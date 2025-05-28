# API - ChatNomina

## Visión General

La API de ChatNomina proporciona endpoints para interactuar con el sistema de chat inteligente para consultas de nómina. Esta documentación detalla los endpoints disponibles, sus parámetros, respuestas y ejemplos de uso.

## Autenticación

### Token JWT

Todas las peticiones a la API requieren autenticación mediante JWT (JSON Web Token).

#### Obtención del Token

```http
POST /api/auth/token
Content-Type: application/json

{
    "username": "usuario@empresa.com",
    "password": "contraseña"
}
```

Respuesta:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

#### Uso del Token

Incluir el token en el header de todas las peticiones:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Endpoints

### 1. Chat

#### Enviar Mensaje

```http
POST /api/chat/message
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "¿Cuál es mi sueldo actual?",
    "context": {
        "user_id": "123",
        "session_id": "abc-123"
    }
}
```

Respuesta:
```json
{
    "response": {
        "text": "Tu sueldo actual es de $3,000,000 COP",
        "confidence": 0.95,
        "entities": [
            {
                "text": "sueldo",
                "type": "CONCEPT",
                "start": 3,
                "end": 9
            },
            {
                "text": "$3,000,000",
                "type": "MONEY",
                "start": 24,
                "end": 34
            }
        ],
        "intent": "query_salary",
        "sources": ["payroll_records"]
    },
    "context": {
        "session_id": "abc-123",
        "last_query": "¿Cuál es mi sueldo actual?",
        "last_response": "Tu sueldo actual es de $3,000,000 COP"
    }
}
```

#### Obtener Historial

```http
GET /api/chat/history
Authorization: Bearer <token>
Query Parameters:
    - session_id: string (opcional)
    - limit: integer (opcional, default: 10)
    - offset: integer (opcional, default: 0)
```

Respuesta:
```json
{
    "history": [
        {
            "timestamp": "2024-03-15T10:30:00Z",
            "message": "¿Cuál es mi sueldo actual?",
            "response": {
                "text": "Tu sueldo actual es de $3,000,000 COP",
                "confidence": 0.95
            }
        },
        {
            "timestamp": "2024-03-15T10:31:00Z",
            "message": "¿Y cuánto me retienen?",
            "response": {
                "text": "De tu sueldo se retiene $300,000 COP por concepto de salud y pensión",
                "confidence": 0.92
            }
        }
    ],
    "total": 2,
    "limit": 10,
    "offset": 0
}
```

### 2. Usuario

#### Obtener Perfil

```http
GET /api/user/profile
Authorization: Bearer <token>
```

Respuesta:
```json
{
    "user": {
        "id": "123",
        "email": "usuario@empresa.com",
        "name": "Juan Pérez",
        "department": "Desarrollo",
        "position": "Desarrollador Senior",
        "hire_date": "2020-01-15",
        "salary": {
            "amount": 3000000,
            "currency": "COP",
            "payment_frequency": "monthly"
        },
        "benefits": {
            "health_insurance": true,
            "pension": true,
            "vacation_days": 15
        }
    }
}
```

#### Actualizar Preferencias

```http
PUT /api/user/preferences
Content-Type: application/json
Authorization: Bearer <token>

{
    "language": "es",
    "notifications": {
        "email": true,
        "push": false
    },
    "theme": "dark",
    "timezone": "America/Bogota"
}
```

Respuesta:
```json
{
    "preferences": {
        "language": "es",
        "notifications": {
            "email": true,
            "push": false
        },
        "theme": "dark",
        "timezone": "America/Bogota"
    },
    "updated_at": "2024-03-15T11:00:00Z"
}
```

### 3. Nómina

#### Obtener Recibo de Nómina

```http
GET /api/payroll/payslip
Authorization: Bearer <token>
Query Parameters:
    - month: integer (1-12)
    - year: integer
```

Respuesta:
```json
{
    "payslip": {
        "period": {
            "month": 3,
            "year": 2024,
            "start_date": "2024-03-01",
            "end_date": "2024-03-31"
        },
        "employee": {
            "id": "123",
            "name": "Juan Pérez",
            "position": "Desarrollador Senior"
        },
        "earnings": {
            "base_salary": 3000000,
            "overtime": 0,
            "bonuses": 0,
            "total": 3000000
        },
        "deductions": {
            "health": 120000,
            "pension": 120000,
            "tax": 0,
            "total": 240000
        },
        "net_salary": 2760000,
        "payment_date": "2024-03-31",
        "payment_method": "bank_transfer",
        "bank_account": "****1234"
    }
}
```

#### Obtener Historial de Nómina

```http
GET /api/payroll/history
Authorization: Bearer <token>
Query Parameters:
    - start_date: string (YYYY-MM-DD)
    - end_date: string (YYYY-MM-DD)
    - limit: integer (opcional, default: 12)
    - offset: integer (opcional, default: 0)
```

Respuesta:
```json
{
    "history": [
        {
            "period": {
                "month": 3,
                "year": 2024
            },
            "net_salary": 2760000,
            "payment_date": "2024-03-31"
        },
        {
            "period": {
                "month": 2,
                "year": 2024
            },
            "net_salary": 2760000,
            "payment_date": "2024-02-29"
        }
    ],
    "total": 2,
    "limit": 12,
    "offset": 0
}
```

### 4. Beneficios

#### Obtener Estado de Beneficios

```http
GET /api/benefits/status
Authorization: Bearer <token>
```

Respuesta:
```json
{
    "benefits": {
        "vacation": {
            "total_days": 15,
            "used_days": 5,
            "remaining_days": 10,
            "next_reset": "2024-12-31"
        },
        "health_insurance": {
            "provider": "EPS Sura",
            "plan": "Premium",
            "coverage": "Familiar",
            "members": [
                {
                    "name": "Juan Pérez",
                    "relationship": "Titular"
                },
                {
                    "name": "María Pérez",
                    "relationship": "Cónyuge"
                }
            ]
        },
        "pension": {
            "provider": "Protección",
            "type": "Régimen de Prima Media",
            "contribution_rate": 0.04
        }
    }
}
```

#### Solicitar Vacaciones

```http
POST /api/benefits/vacation/request
Content-Type: application/json
Authorization: Bearer <token>

{
    "start_date": "2024-04-01",
    "end_date": "2024-04-05",
    "reason": "Vacaciones familiares",
    "contact": {
        "name": "María Pérez",
        "phone": "+573001234567",
        "email": "maria@email.com"
    }
}
```

Respuesta:
```json
{
    "request": {
        "id": "vac-123",
        "status": "pending",
        "start_date": "2024-04-01",
        "end_date": "2024-04-05",
        "days": 5,
        "remaining_days": 5,
        "submitted_at": "2024-03-15T12:00:00Z",
        "approver": {
            "name": "Ana García",
            "position": "Gerente de RRHH"
        }
    }
}
```

## Códigos de Error

### HTTP Status Codes

- 200: OK
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Unprocessable Entity
- 429: Too Many Requests
- 500: Internal Server Error

### Error Response Format

```json
{
    "error": {
        "code": "INVALID_REQUEST",
        "message": "El formato de la fecha es inválido",
        "details": {
            "field": "start_date",
            "value": "01-04-2024",
            "expected_format": "YYYY-MM-DD"
        }
    }
}
```

### Códigos de Error Comunes

| Código | Descripción |
|--------|-------------|
| INVALID_TOKEN | Token JWT inválido o expirado |
| INVALID_REQUEST | Parámetros de la petición inválidos |
| UNAUTHORIZED | No tiene permisos para acceder al recurso |
| RESOURCE_NOT_FOUND | El recurso solicitado no existe |
| RATE_LIMIT_EXCEEDED | Se ha excedido el límite de peticiones |
| INTERNAL_ERROR | Error interno del servidor |

## Rate Limiting

La API implementa rate limiting para proteger los recursos:

- 100 peticiones por minuto por IP
- 1000 peticiones por hora por usuario
- 10000 peticiones por día por usuario

Headers de respuesta:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1615813200
```

## Versiones

La API utiliza versionado semántico (MAJOR.MINOR.PATCH):

- MAJOR: Cambios incompatibles
- MINOR: Nuevas funcionalidades compatibles
- PATCH: Correcciones de bugs compatibles

La versión actual es 1.0.0.

### Especificar Versión

Incluir la versión en el header:
```http
Accept: application/vnd.chatnomina.v1+json
```

O en la URL:
```http
GET /api/v1/chat/message
```

## Webhooks

### Configuración

```http
POST /api/webhooks
Content-Type: application/json
Authorization: Bearer <token>

{
    "url": "https://empresa.com/webhook",
    "events": ["message.received", "message.responded"],
    "secret": "webhook_secret_key"
}
```

### Eventos Disponibles

- message.received: Nuevo mensaje recibido
- message.responded: Respuesta generada
- user.created: Nuevo usuario creado
- user.updated: Usuario actualizado
- payslip.generated: Nuevo recibo generado
- vacation.requested: Nueva solicitud de vacaciones
- vacation.approved: Solicitud de vacaciones aprobada
- vacation.rejected: Solicitud de vacaciones rechazada

### Formato del Webhook

```json
{
    "event": "message.responded",
    "timestamp": "2024-03-15T12:00:00Z",
    "data": {
        "message_id": "msg-123",
        "user_id": "123",
        "message": "¿Cuál es mi sueldo?",
        "response": {
            "text": "Tu sueldo actual es de $3,000,000 COP",
            "confidence": 0.95
        }
    },
    "signature": "sha256=..."
}
```

## SDKs

### Python

```python
from chatnomina import ChatNomina

client = ChatNomina(
    api_key="your_api_key",
    environment="production"
)

# Enviar mensaje
response = client.chat.send_message(
    message="¿Cuál es mi sueldo?",
    context={"user_id": "123"}
)

# Obtener historial
history = client.chat.get_history(
    session_id="abc-123",
    limit=10
)

# Obtener recibo
payslip = client.payroll.get_payslip(
    month=3,
    year=2024
)
```

### JavaScript

```javascript
const ChatNomina = require('chatnomina');

const client = new ChatNomina({
    apiKey: 'your_api_key',
    environment: 'production'
});

// Enviar mensaje
client.chat.sendMessage({
    message: '¿Cuál es mi sueldo?',
    context: { userId: '123' }
})
.then(response => console.log(response))
.catch(error => console.error(error));

// Obtener historial
client.chat.getHistory({
    sessionId: 'abc-123',
    limit: 10
})
.then(history => console.log(history))
.catch(error => console.error(error));

// Obtener recibo
client.payroll.getPayslip({
    month: 3,
    year: 2024
})
.then(payslip => console.log(payslip))
.catch(error => console.error(error));
```

## Seguridad

### HTTPS

Todas las peticiones deben realizarse sobre HTTPS.

### Autenticación

- JWT con expiración de 1 hora
- Refresh token con expiración de 30 días
- Tokens revocables

### CORS

```http
Access-Control-Allow-Origin: https://app.chatnomina.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Sanitización

- Validación de entrada
- Escapado de HTML
- Prevención de SQL injection
- Prevención de XSS

## Monitoreo

### Health Check

```http
GET /api/health
```

Respuesta:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-03-15T12:00:00Z",
    "services": {
        "database": "up",
        "cache": "up",
        "queue": "up",
        "models": "up"
    }
}
```

### Métricas

```http
GET /api/metrics
Authorization: Bearer <token>
```

Respuesta:
```json
{
    "requests": {
        "total": 1000,
        "success": 980,
        "error": 20,
        "latency": {
            "p50": 100,
            "p90": 200,
            "p99": 500
        }
    },
    "users": {
        "active": 100,
        "total": 1000
    },
    "models": {
        "intent_classifier": {
            "accuracy": 0.95,
            "latency": 50
        },
        "entity_extractor": {
            "f1_score": 0.92,
            "latency": 100
        }
    }
}
```

## Soporte

### Contacto

- Email: api@chatnomina.com
- Teléfono: +57 300 123 4567
- Horario: Lunes a Viernes 8:00 - 18:00 (GMT-5)

### Documentación Adicional

- [Guía de Integración](https://docs.chatnomina.com/integration)
- [Ejemplos de Código](https://docs.chatnomina.com/examples)
- [FAQ](https://docs.chatnomina.com/faq)
- [Changelog](https://docs.chatnomina.com/changelog) 