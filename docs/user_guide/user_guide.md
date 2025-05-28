# Guía de Usuario - ChatNomina

## Introducción

Esta guía está diseñada para ayudar a los usuarios a utilizar efectivamente el sistema ChatNomina, una aplicación de escritorio que permite realizar consultas sobre nómina y obtener respuestas precisas.

## Acceso al Sistema

1. Ejecutar la aplicación ChatNomina
2. Se abrirá una ventana nativa de la aplicación
3. Iniciar sesión con las credenciales de Microsoft
4. Esperar a que se carguen los documentos necesarios

## Interfaz de Usuario

La interfaz de ChatNomina se presenta en una ventana nativa con las siguientes secciones:

### 1. Encabezado
- Título de la aplicación
- Instrucciones de uso
- Estado de la sesión

### 2. Área de Chat
- Campo de entrada de texto para escribir preguntas
- Botón de envío
- Historial de conversación
- Botones de feedback (👍/👎) para cada respuesta
- Avatares para identificar usuario y sistema

### 3. Pie de Página
- Campo de entrada de texto
- Botón de envío
- Avatar del usuario

## Tipos de Consultas Soportadas

### 1. Consultas de Datos Personales

- Sueldo actual
- Datos bancarios
- Información personal

### 2. Consultas de Nómina

- Última consignación
- Retención en la fuente
- Novedades y descuentos
- Total acumulado

### 3. Consultas de Vacaciones

- Días pendientes
- Historial de vacaciones
- Políticas de vacaciones

### 4. Consultas de Normativa

- Leyes laborales
- Decretos
- Resoluciones
- Artículos específicos

## Mejores Prácticas

### Formulación de Preguntas

- Ser específico en las consultas
- Usar lenguaje claro y directo
- Incluir fechas cuando sea relevante
- Evitar preguntas demasiado generales

### Ejemplos de Preguntas Efectivas

✅ "¿Cuál es mi sueldo actual?"
✅ "¿Cuántos días de vacaciones me quedan para este año?"
✅ "¿Cuál fue el valor de mi última consignación?"
✅ "¿Cuál es la normativa sobre horas extras?"

### Ejemplos de Preguntas a Evitar

❌ "Dime todo sobre mi nómina"
❌ "¿Qué hay de nuevo?"
❌ "Explícame todo sobre vacaciones"

## Sistema de Feedback

Para mejorar continuamente el sistema:

1. Usar el botón 👍 cuando la respuesta sea correcta
2. Usar el botón 👎 cuando la respuesta sea incorrecta
3. Proporcionar detalles adicionales cuando sea necesario

## Solución de Problemas Comunes

### 1. La aplicación no inicia
- Verificar que Python esté instalado correctamente
- Asegurar que todas las dependencias estén instaladas
- Verificar que no haya otra instancia de la aplicación ejecutándose

### 2. No se puede iniciar sesión
- Verificar conexión a internet
- Asegurar que las credenciales sean correctas
- Verificar que la cuenta tenga acceso a SharePoint

### 3. Respuestas incorrectas
- Reformular la pregunta
- Verificar que la pregunta esté dentro del ámbito del sistema
- Usar el sistema de feedback para reportar el problema

### 4. Errores de carga
- Verificar la conexión a SharePoint
- Contactar al administrador del sistema
- Revisar los logs en la carpeta de la aplicación

## Preguntas Frecuentes (FAQ)

### ¿Puedo consultar información de otros empleados?
No, el sistema solo permite consultar información personal.

### ¿Qué tan actualizada está la información?
La información se actualiza diariamente con los datos más recientes de nómina.

### ¿Puedo exportar las conversaciones?
Actualmente no está disponible la exportación de conversaciones.

### ¿Qué hago si recibo una respuesta incorrecta?
Usa el botón 👎 y proporciona detalles sobre el error para ayudar a mejorar el sistema.

### ¿La aplicación funciona sin conexión a internet?
No, la aplicación requiere conexión a internet para:
- Autenticación con Microsoft
- Acceso a SharePoint
- Consulta de normativa web
- Actualización de datos

## Contacto y Soporte

Para reportar problemas o solicitar ayuda:

- Email: apino@icesi.edu.co
- GitHub: https://github.com/arlexpin/ChatNomina
- Universidad Icesi - Maestría en Ciencias de Datos
- Proyecto de Grado II - 2024

## Notas Adicionales

- La aplicación está optimizada para funcionar en CPU
- Se recomienda tener 8GB+ de RAM para mejor rendimiento
- Los logs se almacenan en la carpeta de la aplicación
- El feedback se utiliza para mejorar continuamente el sistema
