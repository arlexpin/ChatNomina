import requests
import tempfile
from docx import Document

def cargar_archivos_txt_desde_sharepoint(archivos_json):
    cache = {}
    for archivo in archivos_json:
        nombre = archivo.get("name", "").strip()
        if nombre.lower().endswith(".txt"):
            url = archivo.get("@microsoft.graph.downloadUrl")
            if not url:
                continue
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    # Unir las líneas con saltos de línea para mantener la estructura del texto
                    texto = "\n".join(line.strip() for line in response.content.decode("utf-8").splitlines() if line.strip())
                    if texto:  # Solo agregar si hay contenido
                        cache[nombre] = texto
                    else:
                        print(f"⚠️ Archivo vacío: {nombre}")
                else:
                    print(f"⚠️ Error descargando {nombre}: status {response.status_code}")
            except Exception as e:
                print(f"❌ Error procesando {nombre}: {e}")
    return cache

def cargar_documentos_word_desde_sharepoint(archivos_json):
    documentos = {}
    for archivo in archivos_json:
        nombre = archivo.get("name", "")
        if nombre.endswith(".doc") or nombre.endswith(".docx"):
            url = archivo.get("@microsoft.graph.downloadUrl")
            if not url:
                continue
            try:
                response = requests.get(url)
                with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                    tmp.write(response.content)
                    tmp.flush()
                    doc = Document(tmp.name)
                    texto = []

                    # Párrafos normales
                    for p in doc.paragraphs:
                        if p.text.strip():
                            texto.append(p.text.strip())

                    # Contenido de tablas (si hay)
                    for tabla in doc.tables:
                        for fila in tabla.rows:
                            fila_texto = " | ".join(cell.text.strip() for cell in fila.cells if cell.text.strip())
                            if fila_texto:
                                texto.append(fila_texto)

                    documentos[nombre] = "\n".join(texto)

            except Exception as e:
                print(f"❌ Error cargando Word {nombre}: {e}")
    return documentos