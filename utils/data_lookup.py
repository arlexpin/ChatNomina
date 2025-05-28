import requests
import tempfile

def descargar_y_buscar_linea_por_documento(archivo_url, documento):
    """
    Descarga un archivo de texto desde una URL y busca la línea que contiene el documento especificado.
    Retorna la línea como texto si se encuentra, o None si no está.
    """
    response = requests.get(archivo_url)
    if response.status_code != 200:
        print("Error descargando archivo:", response.text)
        return None

    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tmp:
        tmp.write(response.content)
        tmp.flush()
        tmp.seek(0)
        contenido = tmp.read().decode("utf-8").splitlines()

    for linea in contenido:
        if documento in linea:
            return linea

    return None
