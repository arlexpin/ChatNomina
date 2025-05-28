def encontrar_valor_en_linea(linea, posibles_campos, documento):
    """
    Busca el documento en una línea usando posibles nombres de columna
    """
    for campo in posibles_campos:
        if campo.lower() in linea.lower() and documento in linea:
            return True
    return False


def extraer_columna_por_encabezado(encabezados, nombres_posibles):
    """
    Devuelve el índice de la columna que coincide con cualquiera de los nombres dados
    """
    for i, encabezado in enumerate(encabezados):
        if encabezado.strip().lower() in [n.lower() for n in nombres_posibles]:
            return i
    return -1
