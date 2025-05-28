# API Documentation - ChatNomina

## Overview

ChatNomina provides a RESTful API for interacting with the payroll chatbot system. This API allows clients to authenticate, send queries, and retrieve responses programmatically.

## Base URL

```
https://api.chatnomina.com/v1
```

## Authentication

### OAuth 2.0

All API requests require authentication using OAuth 2.0. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Obtaining Access Tokens

#### Request
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=<client_id>&
client_secret=<client_secret>
```

#### Response
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "def502..."
}
```

## Endpoints

### Chat

#### Send Message

Sends a message to the chatbot and receives a response.

##### Request
```http
POST /chat/message
Content-Type: application/json

{
    "message": "¿Cuál es mi sueldo actual?",
    "context": {
        "user_id": "12345",
        "session_id": "abc123"
    }
}
```

##### Response
```json
{
    "response": "Tu sueldo actual es de $3,000,000 COP",
    "confidence": 0.95,
    "sources": [
        {
            "type": "database",
            "reference": "payroll_records"
        }
    ],
    "timestamp": "2024-03-20T10:30:00Z"
}
```

#### Get Chat History

Retrieves the chat history for a specific session.

##### Request
```http
GET /chat/history?session_id=abc123
```

##### Response
```json
{
    "messages": [
        {
            "id": "msg_123",
            "role": "user",
            "content": "¿Cuál es mi sueldo actual?",
            "timestamp": "2024-03-20T10:30:00Z"
        },
        {
            "id": "msg_124",
            "role": "assistant",
            "content": "Tu sueldo actual es de $3,000,000 COP",
            "timestamp": "2024-03-20T10:30:01Z"
        }
    ],
    "session_id": "abc123",
    "start_time": "2024-03-20T10:29:00Z"
}
```

### User Management

#### Get User Profile

Retrieves the profile information for the authenticated user.

##### Request
```http
GET /users/profile
```

##### Response
```json
{
    "user_id": "12345",
    "name": "Juan Pérez",
    "email": "juan.perez@example.com",
    "role": "employee",
    "department": "IT",
    "hire_date": "2020-01-15"
}
```

#### Update User Preferences

Updates the user's chat preferences.

##### Request
```http
PUT /users/preferences
Content-Type: application/json

{
    "language": "es",
    "theme": "dark",
    "notifications": {
        "email": true,
        "push": false
    }
}
```

##### Response
```json
{
    "status": "success",
    "message": "Preferences updated successfully",
    "preferences": {
        "language": "es",
        "theme": "dark",
        "notifications": {
            "email": true,
            "push": false
        }
    }
}
```

### Payroll Information

#### Get Salary Information

Retrieves the salary information for the authenticated user.

##### Request
```http
GET /payroll/salary
```

##### Response
```json
{
    "base_salary": 3000000,
    "currency": "COP",
    "payment_frequency": "monthly",
    "last_payment": {
        "date": "2024-03-15",
        "amount": 3000000,
        "deductions": {
            "health": 120000,
            "pension": 120000,
            "tax": 300000
        },
        "net_amount": 2460000
    }
}
```

#### Get Vacation Balance

Retrieves the vacation balance for the authenticated user.

##### Request
```http
GET /payroll/vacation-balance
```

##### Response
```json
{
    "total_days": 15,
    "used_days": 5,
    "available_days": 10,
    "year": 2024,
    "last_update": "2024-03-20T10:30:00Z"
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {
            "field": "Additional error details"
        }
    }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `INVALID_TOKEN` | Invalid or expired token |
| `INVALID_REQUEST` | Invalid request parameters |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMITED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- 100 requests per minute per client
- 1000 requests per hour per client
- 10000 requests per day per client

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616236800
```

## Webhooks

### Configuration

Configure webhooks to receive real-time updates:

```http
POST /webhooks
Content-Type: application/json

{
    "url": "https://your-server.com/webhook",
    "events": ["message.received", "message.sent"],
    "secret": "your-webhook-secret"
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `message.received` | When a new message is received |
| `message.sent` | When a response is sent |
| `user.authenticated` | When a user successfully authenticates |
| `error.occurred` | When an error occurs |

### Webhook Payload

```json
{
    "event": "message.received",
    "timestamp": "2024-03-20T10:30:00Z",
    "data": {
        "message_id": "msg_123",
        "user_id": "12345",
        "content": "¿Cuál es mi sueldo actual?"
    }
}
```

## SDKs

### Python

```python
from chatnomina import ChatNominaClient

client = ChatNominaClient(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

response = client.chat.send_message(
    message="¿Cuál es mi sueldo actual?",
    context={"user_id": "12345"}
)
```

### JavaScript

```javascript
const { ChatNominaClient } = require('chatnomina');

const client = new ChatNominaClient({
    clientId: 'your_client_id',
    clientSecret: 'your_client_secret'
});

const response = await client.chat.sendMessage({
    message: '¿Cuál es mi sueldo actual?',
    context: { userId: '12345' }
});
```

## Versioning

The API uses semantic versioning. The current version is v1.

- Major version changes (v1 → v2) may include breaking changes
- Minor version changes (v1.1 → v1.2) add new features
- Patch version changes (v1.1.1 → v1.1.2) include bug fixes

## Changelog

### v1.0.0 (2024-03-20)
- Initial release
- Basic chat functionality
- User management
- Payroll information endpoints

### v1.1.0 (2024-03-25)
- Added webhook support
- Added vacation balance endpoint
- Improved error handling
- Added rate limiting

## Support

For API support, contact:
- Email: api-support@chatnomina.com
- Documentation: https://docs.chatnomina.com
- Status Page: https://status.chatnomina.com 