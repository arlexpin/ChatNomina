from typing import Dict, Any, Optional
from datetime import datetime
import re

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
        num_vinc = next((l.split(";")[1].strip() for l in lineas_vinc if l.split(";")[0].strip() == documento), None)
        if not num_vinc:
            return "No se encontró vinculación para este documento."

        fecha_vinculacion = next(
            (p[2] for p in [l.split(";") for l in lineas_vinc if l.strip()] if p[1].strip() == num_vinc),
            None
        )
        if not fecha_vinculacion:
            return "No se encontró la fecha de vinculación."

        fecha_pasada = parse_fecha_segura(fecha_vinculacion)
        fecha_actual = datetime.now()
        dias_transcurridos = (fecha_actual - fecha_pasada).days
        dias_derecho = (dias_transcurridos / 365) * 15

        dias_disfrute = sum(
            int(p[4]) for p in [l.split(";") for l in cache.get("VACACIONES_DERECHO_HM.TXT", []) if l.strip()]
            if p[0].strip() == num_vinc and p[4].isdigit()
        )

        saldo = round(dias_derecho - dias_disfrute, 1)
        return f"Tienes {saldo} días de vacaciones pendientes. ({round(dias_derecho,1)} otorgados, {dias_disfrute} disfrutados)"
    except Exception as e:
        return f"Error calculando vacaciones: {str(e)}"

def calcular_valor_ultima_consignacion(documento, cache):
    try:
        num_vinc = next((l.split(";")[1].strip() for l in cache.get("VINCULACION_HM.TXT", []) if l.split(";")[0].strip() == documento), None)
        if not num_vinc:
            return "No se encontró vinculación."

        consignaciones = [l.split(";") for l in cache.get("CONSIGNACIONES_HM.TXT", []) if l.strip() and l.split(";")[0].strip() == num_vinc]
        if not consignaciones:
            return "No hay consignaciones registradas."

        ultima = consignaciones[-1]
        valor = int(float(ultima[5]))
        ingresos = int(float(ultima[3]))
        descuentos = int(float(ultima[4]))
        return f"Tu última consignación fue de ${valor:,.0f}, los ingresos fueron ${ingresos:,.0f} y los descuentos ${descuentos:,.0f}."
    except Exception as e:
        return f"Error obteniendo la consignación: {str(e)}"

def obtener_sueldo_actual(documento, cache):
    try:
        lineas = cache.get("HISTORICO_SUELDO_HM.TXT", [])
        registros = [
            l.split(";") for l in lineas if documento in l and l.strip() and len(l.split(";")) >= 6
        ]
        if not registros:
            return "No se encontró historial de sueldos para este documento."

        registros_ordenados = sorted(
            registros,
            key=lambda r: datetime.strptime(r[3].strip().split()[0], "%d/%m/%Y")
        )

        sueldo_anterior = int(registros_ordenados[-2][5]) if len(registros_ordenados) > 1 else 0
        sueldo_actual = int(registros_ordenados[-1][5])
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
        return f"Error calculando la variación del sueldo: {str(e)}"

def obtener_datos_personales(documento, cache):
    try:
        persona = next((l.split(";") for l in cache.get("ACTIVOS_HM.TXT", []) if l.split(";")[1].strip() == documento), None)
        if not persona:
            return "No se encontró información personal."
        nombre = persona[7]
        correo = persona[26]
        telefono = persona[28]
        posicion = persona[12]
        contrato = persona[17]
        eps = persona[18]
        afp = persona[20]
        return f"Nombre: {nombre}\nCorreo: {correo}\nTeléfono: {telefono}\nCargo: {posicion}\nTipo contrato: {contrato}\nEPS: {eps}\n AFP: {afp}"
    except Exception as e:
        return f"Error en datos personales: {str(e)}"

def obtener_datos_bancarios(documento, cache):
    try:
        cuentas = [l.split(";") for l in cache.get("CUENTAS_BANCARIAS_HM.TXT", []) if l.strip() and l.split(";")[1].strip() == documento]
        if not cuentas:
            return "No se encontraron cuentas bancarias."
        ultima = cuentas[-1]
        return f"Cuenta en {ultima[5]}, tipo {ultima[6]}, terminada en {ultima[7][-4:]}"
    except Exception as e:
        return f"Error en datos bancarios: {str(e)}"

def calcular_total_novedades(documento, cache):
    try:
        novedades = [l.split(";") for l in cache.get("NOVEDADES_HM.TXT", []) if l.strip() and l.split(";")[1].strip() == documento]
        if not novedades:
            return "No se encontraron novedades."
        total = sum(float(p[9]) for p in novedades if p[9].replace('.', '', 1).isdigit())
        return f"El valor total acumulado por novedades es ${round(total, 2)}"
    except Exception as e:
        return f"Error calculando novedades: {str(e)}"

def obtener_retencion_fuente(documento, cache):
    try:
        retenciones = [l.split(";") for l in cache.get("VALIDADOR_RETENCION.TXT", []) if l.strip() and l.split(";")[3].strip() == documento]
        if not retenciones:
            return "No se encontraron registros de retención."
        ultima = retenciones[-1]
        porcentaje = ultima[13]
        base = ultima[14]
        ret_fuente = ultima[15]
        return f"Retención actual: ${ret_fuente}, base: ${base}, porcentaje aplicado: {porcentaje}%"
    except Exception as e:
        return f"Error en retención: {str(e)}"

def calcular_total_pagado_acumulado(documento, cache):
    try:
        acumulados = [l.split(";") for l in cache.get("ACUMULADOS.TXT", []) if l.strip() and l.split(";")[1].strip() == documento]
        if not acumulados:
            return "No se encontraron registros acumulados."
        total = sum(float(p[23]) for p in acumulados if p[23].replace('.', '', 1).isdigit())
        return f"El total pagado acumulado es ${round(total, 2)}"
    except Exception as e:
        return f"Error calculando acumulado: {str(e)}"