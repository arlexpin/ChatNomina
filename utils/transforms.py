from typing import Dict, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

# Diccionario de palabras clave para transformaciones directas
TRANSFORM_KEYWORDS = {
    "vacaciones": {
        "keywords": ["vacaciones", "vacación", "días pendientes"],
        "category": "specific_data",
        "transform_func": "calcular_dias_pendientes_vacaciones"
    },
    "consignacion": {
        "keywords": ["consignaci", "consignación", "última consignación", "valor consignado"],
        "category": "specific_data",
        "transform_func": "calcular_valor_ultima_consignacion"
    },
    "sueldo": {
        "keywords": ["sueldo", "salario", "devengado", "remuneración"],
        "category": "specific_data",
        "transform_func": "obtener_sueldo_actual"
    },
    "datos_personales": {
        "keywords": ["correo", "nombre", "eps", "afp", "pension", "pensión", "salud"],
        "category": "specific_data",
        "transform_func": "obtener_datos_personales"
    },
    "datos_bancarios": {
        "keywords": ["cuenta", "banco", "consignación", "consignacion", "transferencia"],
        "category": "specific_data",
        "transform_func": "obtener_datos_bancarios"
    },
    "novedades": {
        "keywords": ["novedad", "descuento", "bonificación", "bonificacion", "extra"],
        "category": "specific_data",
        "transform_func": "calcular_total_novedades"
    },
    "retencion": {
        "keywords": ["retenci", "retención", "fuente", "impuesto"],
        "category": "specific_data",
        "transform_func": "obtener_retencion_fuente"
    },
    "total_pagado": {
        "keywords": ["acumulado", "total pagado", "total acumulado", "suma total"],
        "category": "specific_data",
        "transform_func": "calcular_total_pagado_acumulado"
    }
}

def get_transform_keywords() -> Dict[str, Dict[str, Any]]:
    """Retorna el diccionario de palabras clave para transformaciones."""
    return TRANSFORM_KEYWORDS

def get_transform_by_keyword(keyword: str) -> Optional[Dict[str, Any]]:
    """Busca una transformación por palabra clave."""
    for transform_info in TRANSFORM_KEYWORDS.values():
        if any(kw in keyword.lower() for kw in transform_info["keywords"]):
            return transform_info
    return None

def parse_fecha_segura(fecha_str):
    fecha_limpia = fecha_str.strip().split()[0]  # elimina espacios y partes de hora si hay
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(fecha_limpia, fmt)
        except ValueError:
            continue
    raise ValueError(f"No se pudo interpretar la fecha: {fecha_str}")

def calcular_dias_pendientes_vacaciones(documento, cache):
    try:
        lineas_vinc = cache.get("VINCULACION_HM.TXT", [])
        # Buscar el número de vinculación en la lista de listas
        num_vinc = next((campos[1].strip() for campos in lineas_vinc if len(campos) > 1 and campos[0].strip() == documento), None)
        if not num_vinc:
            logger.warning(f"No se encontró vinculación para el documento {documento}")
            return "No se encontró vinculación para este documento."

        # Buscar la fecha de vinculación
        fecha_vinculacion = next(
            (campos[2] for campos in lineas_vinc if len(campos) > 2 and campos[1].strip() == num_vinc),
            None
        )
        if not fecha_vinculacion:
            logger.warning(f"No se encontró fecha de vinculación para el documento {documento}")
            return "No se encontró la fecha de vinculación."

        fecha_pasada = parse_fecha_segura(fecha_vinculacion)
        fecha_actual = datetime.now()
        dias_transcurridos = (fecha_actual - fecha_pasada).days
        dias_derecho = (dias_transcurridos / 365) * 15

        # Calcular días disfrutados
        vacaciones = cache.get("VACACIONES_DERECHO_HM.TXT", [])
        dias_disfrute = sum(
            int(campos[4]) for campos in vacaciones 
            if len(campos) > 4 and campos[0].strip() == num_vinc and campos[4].strip().isdigit()
        )

        saldo = round(dias_derecho - dias_disfrute, 1)
        logger.info(f"Cálculo de vacaciones para documento {documento}: {dias_derecho} otorgados, {dias_disfrute} disfrutados, {saldo} pendientes")
        return f"Tienes {saldo} días de vacaciones pendientes. ({round(dias_derecho,1)} otorgados, {dias_disfrute} disfrutados)"
    except Exception as e:
        logger.error(f"Error calculando vacaciones para documento {documento}: {str(e)}", exc_info=True)
        return f"Error calculando vacaciones: {str(e)}"

def calcular_valor_ultima_consignacion(documento, cache):
    try:
        lineas_vinc = cache.get("VINCULACION_HM.TXT", [])
        num_vinc = next((campos[1].strip() for campos in lineas_vinc 
                        if len(campos) > 1 and campos[0].strip() == documento), None)
        if not num_vinc:
            logger.warning(f"No se encontró vinculación para el documento {documento}")
            return "No se encontró vinculación."

        consignaciones = [campos for campos in cache.get("CONSIGNACIONES_HM.TXT", []) 
                         if len(campos) > 5 and campos[0].strip() == num_vinc]
        if not consignaciones:
            logger.warning(f"No se encontraron consignaciones para el documento {documento}")
            return "No hay consignaciones registradas."

        ultima = consignaciones[-1]
        valor = int(float(ultima[5]))
        ingresos = int(float(ultima[3]))
        descuentos = int(float(ultima[4]))
        
        logger.info(f"Última consignación encontrada para documento {documento}: ${valor:,.0f}")
        return f"Tu última consignación fue de ${valor:,.0f}, los ingresos fueron ${ingresos:,.0f} y los descuentos ${descuentos:,.0f}."
    except Exception as e:
        logger.error(f"Error obteniendo la consignación para documento {documento}: {str(e)}", exc_info=True)
        return f"Error obteniendo la consignación: {str(e)}"

def obtener_sueldo_actual(documento, cache):
    try:
        lineas = cache.get("HISTORICO_SUELDO_HM.TXT", [])
        # Buscar el documento en la posición correcta (asumiendo que está en la segunda columna)
        registros = [
            campos for campos in lineas 
            if len(campos) >= 6 and campos[1].strip() == documento
        ]
        
        if not registros:
            # Intentar buscar en ACTIVOS_HM.TXT para verificar si el documento existe
            activos = cache.get("ACTIVOS_HM.TXT", [])
            if not any(campos[1].strip() == documento for campos in activos if len(campos) > 1):
                return "No se encontró información para este documento."
            return "No se encontró historial de sueldos para este documento."

        # Ordenar por fecha (asumiendo que la fecha está en la posición 3)
        registros_ordenados = sorted(
            registros,
            key=lambda r: datetime.strptime(r[3].strip().split()[0], "%d/%m/%Y")
        )

        sueldo_anterior = int(float(registros_ordenados[-2][5])) if len(registros_ordenados) > 1 else 0
        sueldo_actual = int(float(registros_ordenados[-1][5]))
        fecha_inicio_str = registros_ordenados[-1][3]
        fecha_inicio = datetime.strptime(fecha_inicio_str.strip().split()[0], "%d/%m/%Y")

        variacion = 0
        if sueldo_anterior > 0:
            variacion = ((sueldo_actual - sueldo_anterior) / sueldo_anterior) * 100

        return (
            f"Tu sueldo actual es ${sueldo_actual:,.0f}, desde el {fecha_inicio.strftime('%d/%m/%Y')} "
            f"y ha variado un {variacion:.2f}% desde ${sueldo_anterior:,.0f}."
        )
    except Exception as e:
        logger.error(f"Error calculando la variación del sueldo: {str(e)}")
        return f"Error calculando la variación del sueldo: {str(e)}"

def obtener_datos_personales(documento, cache):
    try:
        activos = cache.get("ACTIVOS_HM.TXT", [])
        persona = next((campos for campos in activos if len(campos) > 28 and campos[1].strip() == documento), None)
        if not persona:
            logger.warning(f"No se encontró información personal para el documento {documento}")
            return "No se encontró información personal."
        
        nombre = persona[7].strip()
        correo = persona[26].strip()
        telefono = persona[28].strip()
        posicion = persona[12].strip()
        contrato = persona[17].strip()
        eps = persona[18].strip()
        afp = persona[20].strip()
        
        logger.info(f"Datos personales encontrados para documento {documento}")
        return f"Nombre: {nombre}\nCorreo: {correo}\nTeléfono: {telefono}\nCargo: {posicion}\nTipo contrato: {contrato}\nEPS: {eps}\nAFP: {afp}"
    except Exception as e:
        logger.error(f"Error en datos personales para documento {documento}: {str(e)}", exc_info=True)
        return f"Error en datos personales: {str(e)}"

def obtener_datos_bancarios(documento, cache):
    try:
        cuentas = [campos for campos in cache.get("CUENTAS_BANCARIAS_HM.TXT", []) 
                  if len(campos) > 7 and campos[1].strip() == documento]
        if not cuentas:
            logger.warning(f"No se encontraron cuentas bancarias para el documento {documento}")
            return "No se encontraron cuentas bancarias."
        
        ultima = cuentas[-1]
        banco = ultima[5].strip()
        tipo = ultima[6].strip()
        numero = ultima[7].strip()
        
        logger.info(f"Datos bancarios encontrados para documento {documento}")
        return f"Cuenta en {banco}, tipo {tipo}, terminada en {numero[-4:]}"
    except Exception as e:
        logger.error(f"Error en datos bancarios para documento {documento}: {str(e)}", exc_info=True)
        return f"Error en datos bancarios: {str(e)}"

def calcular_total_novedades(documento, cache):
    try:
        novedades = [campos for campos in cache.get("NOVEDADES_HM.TXT", []) 
                    if len(campos) > 9 and campos[1].strip() == documento]
        if not novedades:
            logger.warning(f"No se encontraron novedades para el documento {documento}")
            return "No se encontraron novedades."
        
        total = sum(float(campos[9]) for campos in novedades 
                   if campos[9].strip().replace('.', '', 1).isdigit())
        
        logger.info(f"Total de novedades calculado para documento {documento}: ${total:,.2f}")
        return f"El valor total acumulado por novedades es ${total:,.2f}"
    except Exception as e:
        logger.error(f"Error calculando novedades para documento {documento}: {str(e)}", exc_info=True)
        return f"Error calculando novedades: {str(e)}"

def obtener_retencion_fuente(documento, cache):
    try:
        retenciones = [campos for campos in cache.get("VALIDADOR_RETENCION.TXT", []) 
                      if len(campos) > 15 and campos[3].strip() == documento]
        if not retenciones:
            logger.warning(f"No se encontraron registros de retención para el documento {documento}")
            return "No se encontraron registros de retención."
        
        ultima = retenciones[-1]
        porcentaje = ultima[13].strip()
        base = ultima[14].strip()
        ret_fuente = ultima[15].strip()
        
        logger.info(f"Retención encontrada para documento {documento}: {porcentaje}%, base ${base}")
        return f"Retención actual: ${ret_fuente}, base: ${base}, porcentaje aplicado: {porcentaje}%"
    except Exception as e:
        logger.error(f"Error en retención para documento {documento}: {str(e)}", exc_info=True)
        return f"Error en retención: {str(e)}"

def calcular_total_pagado_acumulado(documento, cache):
    try:
        acumulados = [campos for campos in cache.get("ACUMULADOS.TXT", []) 
                     if len(campos) > 23 and campos[1].strip() == documento]
        if not acumulados:
            logger.warning(f"No se encontraron registros acumulados para el documento {documento}")
            return "No se encontraron registros acumulados."
        
        total = sum(float(campos[23]) for campos in acumulados 
                   if campos[23].strip().replace('.', '', 1).isdigit())
        
        logger.info(f"Total acumulado calculado para documento {documento}: ${total:,.2f}")
        return f"El total pagado acumulado es ${total:,.2f}"
    except Exception as e:
        logger.error(f"Error calculando acumulado para documento {documento}: {str(e)}", exc_info=True)
        return f"Error calculando acumulado: {str(e)}"