from transformers import pipeline

qa_pipeline = pipeline(
    "question-answering",
    model="mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es",
    tokenizer="mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es"
)

def responder_pregunta_documental(pregunta, documentos_texto, ventana=500, paso=250):
    """
    Divide cada documento en fragmentos y aplica QA por separado (sliding window).
    Elige la mejor respuesta entre todos los fragmentos.
    """
    respuestas = []

    for nombre, texto in documentos_texto.items():
        palabras = texto.split()
        total = len(palabras)
        for i in range(0, total, paso):
            fragmento = " ".join(palabras[i:i+ventana])
            try:
                resultado = qa_pipeline({
                    "question": pregunta,
                    "context": fragmento
                })
                if resultado and resultado["score"] > 0.2:
                    respuestas.append((nombre, resultado["answer"], round(resultado["score"], 3)))
            except Exception as e:
                print(f"Error en fragmento {i}-{i+ventana} de {nombre}: {e}")

    if not respuestas:
        return "No encontré una respuesta clara en los documentos institucionales."

    mejor = max(respuestas, key=lambda x: x[2])
    return f"📄 Según el documento '{mejor[0]}':\n{mejor[1]}"
