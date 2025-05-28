from transformers import pipeline
import requests
from bs4 import BeautifulSoup

qa_pipeline = pipeline(
    "question-answering",
    model="mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es",
    tokenizer="mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es"
)

def buscar_normativa_web(pregunta):
    try:
        consulta = pregunta.replace(" ", "+")
        url = f"https://www.google.com/search?q=site%3Awww.mintrabajo.gov.co+{consulta}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        enlaces = [a['href'] for a in soup.find_all('a', href=True) if '/url?q=' in a['href']]
        if not enlaces:
            return "No encontré resultados relevantes en MinTrabajo.gov.co."

        primer_url = enlaces[0].split('/url?q=')[1].split('&')[0]
        r_doc = requests.get(primer_url, headers=headers)
        soup_doc = BeautifulSoup(r_doc.text, "html.parser")
        texto = " ".join([p.get_text() for p in soup_doc.find_all("p")])

        if not texto.strip():
            return f"Puedes revisar directamente: {primer_url}"

        respuesta = qa_pipeline({"question": pregunta, "context": texto})
        return f"🔎 Según MinTrabajo.gov.co:\n{respuesta['answer']}\nReferencia: {primer_url}"
    except Exception as e:
        return f"Error al buscar normatividad en línea: {str(e)}"