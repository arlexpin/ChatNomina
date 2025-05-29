# Importe de librerías y módulos necesarios
import os
import logging
import httpx
import asyncio
import logging.handlers
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from uuid import uuid4
from nicegui import ui, app
from transformers import T5ForConditionalGeneration, T5Tokenizer, pipeline as hf_pipeline, AutoModelForSequenceClassification, AutoTokenizer
import webbrowser
from msal import PublicClientApplication
from utils.cache_loader import (
    cargar_archivos_txt_desde_sharepoint,
    cargar_documentos_word_desde_sharepoint,
)
from utils.embedding_index import DocumentIndexer, IndexConfig
from utils.web_search import buscar_normativa_web
from utils.transforms import (
    calcular_dias_pendientes_vacaciones,
    calcular_valor_ultima_consignacion,
    obtener_sueldo_actual,
    obtener_datos_personales,
    obtener_datos_bancarios,
    calcular_total_novedades,
    obtener_retencion_fuente,
    calcular_total_pagado_acumulado,
    get_transform_keywords,
    get_transform_by_keyword
)
import torch

# Cargar variables de entorno (descomentado)
load_dotenv()

# Configuración detallada de logging
BASE_DIR = Path(__file__).resolve().parent
log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)
log_file_path = log_dir / "app.log"

# Configurar el logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Crear formateador
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configurar handler para archivo con rotación
file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Configurar handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Limpiar handlers existentes y agregar los nuevos
root_logger.handlers.clear()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Configurar niveles específicos para algunos loggers
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Obtener logger para este módulo
logger = logging.getLogger(__name__)

# Mensaje de prueba para verificar la escritura en el archivo
logger.info("="*50)
logger.info("INICIO DE LA APLICACIÓN")
logger.info(f"Directorio de logs: {log_file_path}")
logger.info("="*50)

# Configuración de feedback
FEEDBACK_DIR = BASE_DIR / "feedback"
FEEDBACK_DIR.mkdir(exist_ok=True)
FEEDBACK_FILE = FEEDBACK_DIR / "feedback_incorrecto.txt"

class ChatNominaApp:

    def __init__(self):
        logger.info("Inicializando ChatNominaApp...")
        # Configuración
        self.MODELO_DIR = "D:/OneDrive - Universidad Icesi/Proyectos en curso/ZZ - Python/Maestria Ciencias de Datos/ProyectoGradoII/ChatNomina/modelo_finetuneado/"
        self.MAX_LENGTH = 512
        
        # Configuración básica de PyTorch
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        os.environ["OMP_NUM_THREADS"] = "1"
        
        # Resto de la configuración inicial
        self.TENANT_ID = os.getenv("TENANT_ID", "e994072b-523e-4bfe-86e2-442c5e10b244")
        self.CLIENT_ID = os.getenv("CLIENT_ID", "d4f0a82a-0933-4dad-b584-1fa5cd7ab1e3")
        self.AUTHORITY = f"https://login.microsoftonline.com/{self.TENANT_ID}"
        self.SCOPE = ["Files.Read.All"]
        self.SITE_ID = os.getenv("SITE_ID", "icesiedu.sharepoint.com,0c48bb60-1f87-48c7-ac59-63598f29f94f,d346b80a-b5ca-40fd-9992-fd1307514698")
        self.DRIVE_ID = os.getenv("DRIVE_ID", "b!YLtIDIcfx0isWWNZjyn5Twq4RtPKtf1AmZL9EwdRRpjHTFOg5NodRaFJ9iDy219-")
        self.FOLDER_PATH = os.getenv("FOLDER_PATH", "/2. REPORTES - HR Y HUMANO")
        
        # Estado de la aplicación
        self.messages: List[Tuple[str, str, str, str]] = []
        self.documento_usuario: Optional[str] = None
        self.access_token: Optional[str] = None
        
        # Modelos (inicialmente None)
        self.model_t5: Optional[T5ForConditionalGeneration] = None
        self.tokenizer_t5: Optional[T5Tokenizer] = None
        self.bert_model: Optional[AutoModelForSequenceClassification] = None
        self.bert_tokenizer: Optional[AutoTokenizer] = None
        self.qa_pipeline = None
        
        # Categorías de preguntas y transformaciones
        self.transform_keywords = get_transform_keywords()
        self.question_categories = {
            "specific_data": ["sueldo", "salario", "vacaciones", "consignaci", "retenci", "novedad", "descuento", "total", "acumulado"],
            "general_info": ["qué", "cómo", "cuándo", "dónde", "por qué"],
            "document_qa": ["normativa", "ley", "decreto", "resolucion", "articulo"]
        }
        
        # Mapeo de funciones de transformación
        self.transform_functions = {
            "calcular_dias_pendientes_vacaciones": calcular_dias_pendientes_vacaciones,
            "calcular_valor_ultima_consignacion": calcular_valor_ultima_consignacion,
            "obtener_sueldo_actual": obtener_sueldo_actual,
            "obtener_datos_personales": obtener_datos_personales,
            "obtener_datos_bancarios": obtener_datos_bancarios,
            "calcular_total_novedades": calcular_total_novedades,
            "obtener_retencion_fuente": obtener_retencion_fuente,
            "calcular_total_pagado_acumulado": calcular_total_pagado_acumulado
        }
        
        self.txt_cache: Dict[str, Any] = {}
        self.word_docs: Dict[str, Any] = {}
        self.loading = False
        self.documentos_cargados = False
        self.modelos_cargados = False
        
        self.app = PublicClientApplication(client_id=self.CLIENT_ID, authority=self.AUTHORITY)
        
        # Initialize DocumentIndexer (sin cargar modelos aún)
        indexer_config = IndexConfig(model_name="hiiamsid/sentence_similarity_spanish_es")
        self.indexer = DocumentIndexer(config=indexer_config)
        logger.info("ChatNominaApp inicializada (sin modelos).")

    async def cargar_modelos(self):
        """Carga los modelos necesarios después de tener los documentos."""
        if self.modelos_cargados:
            logger.info("Los modelos ya están cargados.")
            return True

        logger.info("Iniciando carga de modelos...")
        try:
            # Cargar modelo T5 con configuración específica para CPU
            logger.info(f"Cargando modelo T5 desde: {self.MODELO_DIR}...")
            self.model_t5 = T5ForConditionalGeneration.from_pretrained(
                self.MODELO_DIR,
                device_map="cpu",
                torch_dtype=torch.float32,
                local_files_only=True,
                use_cache=True,
                low_cpu_mem_usage=True
            )
            
            # Configurar tokenizer con opciones específicas
            self.tokenizer_t5 = T5Tokenizer.from_pretrained(
                self.MODELO_DIR,
                local_files_only=True,
                model_max_length=self.MAX_LENGTH,
                use_fast=True
            )
            
            # Configurar el tokenizer
            if not self.tokenizer_t5.bos_token_id:
                self.tokenizer_t5.bos_token_id = self.tokenizer_t5.pad_token_id
            if not self.tokenizer_t5.eos_token_id:
                self.tokenizer_t5.eos_token_id = self.tokenizer_t5.pad_token_id
            
            # Cargar modelo BERT con configuración específica para CPU
            logger.info("Cargando modelo BERT...")
            self.bert_model = AutoModelForSequenceClassification.from_pretrained(
                os.path.join(self.MODELO_DIR, "bert_model"),
                num_labels=3,
                device_map="cpu",
                torch_dtype=torch.float32
            )
            self.bert_tokenizer = AutoTokenizer.from_pretrained(
                os.path.join(self.MODELO_DIR, "bert_model"),
                use_fast=True
            )
            
            # Cargar QA Pipeline con configuración específica para CPU
            logger.info("Cargando QA pipeline...")
            self.qa_pipeline = hf_pipeline(
                "question-answering",
                model=self.MODELO_DIR,
                tokenizer=self.MODELO_DIR,
                device_map="cpu",
                framework="pt",
                torch_dtype=torch.float32
            )
            
            logger.info("Todos los modelos cargados exitosamente")
            self.modelos_cargados = True
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar los modelos: {e}", exc_info=True)
            return False

    def _generar_respuesta_t5(self, prompt: str) -> str:
        """Genera una respuesta usando el modelo T5."""
        try:
            if not self.model_t5 or not self.tokenizer_t5:
                logger.error("Modelo T5 o tokenizer no están cargados")
                return "No se pudo generar la respuesta porque el modelo no está cargado."

            # Limpiar y preparar el prompt
            prompt = prompt.strip()
            if not prompt.endswith("Respuesta:"):
                prompt = f"""Pregunta: {prompt}
Contexto: Esta es una pregunta sobre nómina y recursos humanos de la Universidad Icesi. Responde de manera clara y concisa basándote en la normativa y procedimientos de la empresa.
Instrucciones: Genera una respuesta específica y útil. Si no tienes información suficiente, indica que necesitas más detalles.
Respuesta:"""

            # Tokenizar con configuración específica
            inputs = self.tokenizer_t5(
                prompt,
                max_length=self.MAX_LENGTH,
                truncation=True,
                return_tensors="pt",
                padding=True,
                add_special_tokens=True
            )

            # Generar respuesta con parámetros optimizados
            with torch.no_grad():
                try:
                    outputs = self.model_t5.generate(
                        inputs["input_ids"],
                        max_length=min(self.MAX_LENGTH, 512),
                        min_length=100,  # Aumentado para respuestas más completas
                        num_beams=5,     # Aumentado para mejor calidad
                        length_penalty=2.0,  # Aumentado para favorecer respuestas más largas
                        early_stopping=True,
                        do_sample=True,  # Habilitado para mejor diversidad
                        temperature=0.7,  # Reducido para más coherencia
                        top_k=50,        # Ajustado para mejor calidad
                        top_p=0.9,       # Ajustado para mejor calidad
                        repetition_penalty=1.2,  # Ajustado para evitar repeticiones
                        no_repeat_ngram_size=3,
                        forced_bos_token_id=self.tokenizer_t5.bos_token_id,
                        forced_eos_token_id=self.tokenizer_t5.eos_token_id,
                        pad_token_id=self.tokenizer_t5.pad_token_id,
                        num_return_sequences=1
                    )
                except RuntimeError as e:
                    if "out of memory" in str(e):
                        logger.error("Error de memoria al generar respuesta")
                        return "Lo siento, hubo un error de memoria al procesar tu pregunta. Por favor, intenta con una pregunta más corta."
                    raise

            # Decodificar y limpiar la respuesta
            respuesta = self.tokenizer_t5.decode(outputs[0], skip_special_tokens=True)
            respuesta = respuesta.strip()
            
            # Limpiar la respuesta de prefijos comunes y contenido no deseado
            for prefix in ["Pregunta:", "Contexto:", "Instrucciones:", "Respuesta:"]:
                if respuesta.startswith(prefix):
                    respuesta = respuesta[len(prefix):].strip()
                elif prefix in respuesta:
                    respuesta = respuesta.split(prefix)[-1].strip()
            
            # Verificar calidad de la respuesta
            if len(respuesta) < 100 or len(respuesta.split()) < 20:  # Aumentado el mínimo de palabras
                logger.warning(f"Respuesta T5 demasiado corta o inválida: {respuesta}")
                return "Lo siento, no pude generar una respuesta adecuada para tu pregunta. Por favor, intenta reformularla o ser más específico."
                
            # Verificar repetición del prompt
            palabras_prompt = set(prompt.lower().split())
            palabras_respuesta = set(respuesta.lower().split())
            palabras_comunes = palabras_prompt.intersection(palabras_respuesta)
            
            if len(palabras_comunes) / len(palabras_prompt) > 0.4:  # Reducido el umbral
                logger.warning(f"Respuesta T5 parece ser una repetición del prompt: {respuesta}")
                return "Lo siento, no pude generar una respuesta adecuada para tu pregunta. Por favor, intenta reformularla."

            # Verificar que la respuesta no contenga nombres de archivos o rutas
            if any(ext in respuesta.lower() for ext in ['.txt', '.docx', '.xlsx', '.csv']):
                logger.warning(f"Respuesta T5 contiene nombres de archivos: {respuesta}")
                return "Lo siento, no pude generar una respuesta adecuada para tu pregunta. Por favor, intenta reformularla."

            # Verificar que la respuesta no sea genérica
            respuestas_genericas = [
                "esta es una pregunta sobre nómina",
                "esta es una pregunta sobre recursos humanos",
                "no tengo información específica",
                "necesito más detalles",
                "esta es una pregunta sobre",
                "esta pregunta está relacionada con"
            ]
            if any(gen in respuesta.lower() for gen in respuestas_genericas):
                logger.warning(f"Respuesta T5 demasiado genérica: {respuesta}")
                return "Lo siento, no pude generar una respuesta específica para tu pregunta. Por favor, intenta ser más específico en tu consulta."

            logger.debug(f"Respuesta T5 generada: {respuesta}")
            return respuesta

        except Exception as e:
            logger.error(f"Error generando respuesta con T5: {e}", exc_info=True)
            return "No se pudo generar una respuesta en este momento. Por favor, intenta reformular tu pregunta."

    def _clasificar_pregunta(self, pregunta: str) -> Tuple[str, float]:
        """Clasifica la pregunta usando múltiples estrategias y retorna la categoría y su confianza."""
        pregunta_lower = pregunta.lower().strip()
        
        # 1. Verificar si es una pregunta de normativa primero
        keywords_normativa = [
            "ley", "decreto", "resolución", "norma", "reglamento", "estatuto",
            "código", "artículo", "parágrafo", "literal", "inciso", "jurídico",
            "legal", "normativo", "legislación", "derecho", "obligación", "deber",
            "acoso", "laboral", "trabajo", "contrato", "empleado", "empleador",
            "salud", "seguridad", "riesgo", "prevención", "protección"
        ]
        if any(keyword in pregunta_lower for keyword in keywords_normativa):
            logger.debug("Pregunta clasificada como 'document_qa' por contenido normativo")
            return "document_qa", 0.9
        
        # 2. Verificar palabras clave específicas
        transform_info = get_transform_by_keyword(pregunta_lower)
        if transform_info:
            logger.debug(f"Pregunta clasificada como '{transform_info['category']}' por palabra clave específica")
            return transform_info['category'], 0.9
        
        # 3. Verificar palabras clave generales
        for categoria, keywords in self.question_categories.items():
            if any(keyword in pregunta_lower for keyword in keywords):
                logger.debug(f"Pregunta clasificada como '{categoria}' por palabras clave generales")
                return categoria, 0.8
        
        # 4. Usar BERT para clasificación
        try:
            if self.bert_model and self.bert_tokenizer:
                inputs = self.bert_tokenizer(
                    pregunta,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                )
                
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    predictions = torch.softmax(outputs.logits, dim=1)
                    confianza, categoria_idx = torch.max(predictions, dim=1)
                    
                categorias = ["specific_data", "general_info", "document_qa"]
                return categorias[categoria_idx.item()], confianza.item()
        except Exception as e:
            logger.error(f"Error en clasificación BERT: {e}")
        
        # Si no hay clasificación clara, usar document_qa para intentar buscar en documentos
        logger.debug("Pregunta clasificada como 'document_qa' por defecto")
        return "document_qa", 0.5

    def _es_pregunta_normativa(self, pregunta: str) -> bool:
        """Determina si una pregunta está relacionada con normativa."""
        keywords_normativa = [
            "ley", "decreto", "resolución", "norma", "reglamento", "estatuto",
            "código", "artículo", "parágrafo", "literal", "inciso", "jurídico",
            "legal", "normativo", "legislación", "derecho", "obligación", "deber"
        ]
        return any(keyword in pregunta.lower() for keyword in keywords_normativa)

    def _verificar_documento_en_cache(self, documento: str) -> bool:
        """Verifica si el documento existe en el contenido de los archivos."""
        try:
            # Buscar en archivos TXT
            for key, content in self.txt_cache.items():
                if isinstance(content, str):
                    if documento in content:
                        logger.info(f"Documento {documento} encontrado en {key}")
                        return True
                elif isinstance(content, list):
                    if any(documento in str(line) for line in content):
                        logger.info(f"Documento {documento} encontrado en {key}")
                        return True
            
            # Buscar en archivos Word
            for key, content in self.word_docs.items():
                if isinstance(content, str):
                    if documento in content:
                        logger.info(f"Documento {documento} encontrado en {key}")
                        return True
                elif isinstance(content, list):
                    if any(documento in str(line) for line in content):
                        logger.info(f"Documento {documento} encontrado en {key}")
                        return True
            
            logger.warning(f"Documento {documento} no encontrado en ningún archivo")
            return False
        except Exception as e:
            logger.error(f"Error al verificar documento en caché: {e}")
            return False

    def _responder_pregunta(self, pregunta_texto: str) -> str:
        """Orquesta la lógica para responder una pregunta del usuario."""
        logger.info(f"Procesando pregunta: \"{pregunta_texto}\"")
        logger.info(f"Estado actual - Documento usuario: {self.documento_usuario}, Documentos cargados: {self.documentos_cargados}")
        logger.info(f"Estado de caché - TXT: {len(self.txt_cache)}, Word: {len(self.word_docs)}")
        
        # Verificar si el documento existe en los archivos
        if self.documento_usuario:
            if not self._verificar_documento_en_cache(self.documento_usuario):
                return f"No se encontró información para el documento {self.documento_usuario}. Por favor, verifica el número e intenta nuevamente."
        
        respuesta_final = "Lo siento, no pude encontrar una respuesta para tu pregunta en este momento."

        # --- PASO 1: Verificar documento de usuario ---
        if not self.documento_usuario:
            logger.warning("No hay documento de usuario registrado")
            return "Por favor, ingresa tu número de documento primero para que pueda ayudarte mejor."

        # --- PASO 2: Verificar documentos y modelos cargados ---
        if not self.documentos_cargados or not self.modelos_cargados:
            logger.warning("Los documentos o modelos no están completamente cargados")
            return "Los documentos aún se están procesando. Por favor, espera un momento antes de hacer preguntas."

        # --- PASO 3: Clasificar la pregunta ---
        categoria, confianza = self._clasificar_pregunta(pregunta_texto)
        logger.info(f"Pregunta clasificada como: {categoria} (confianza: {confianza:.2f})")
        
        # --- PASO 4: Funciones de transformación directa (keywords) ---
        if categoria == "specific_data" and confianza > 0.7:
            transform_info = get_transform_by_keyword(pregunta_texto)
            logger.info(f"Transformación encontrada: {transform_info}")
            if transform_info:
                try:
                    transform_func = self.transform_functions[transform_info["transform_func"]]
                    logger.info(f"Ejecutando transformación: {transform_info['transform_func']}")
                    respuesta_transform = transform_func(self.documento_usuario, self.txt_cache)
                    logger.info(f"Resultado de transformación: {respuesta_transform}")
                    if respuesta_transform and "no se encontró información" not in respuesta_transform.lower():
                        logger.info(f"Respuesta generada por transformación directa: {respuesta_transform}")
                        return respuesta_transform
                    else:
                        logger.warning("Transformación no encontró información válida")
                except Exception as e:
                    logger.error(f"Error en transformación directa para {transform_info['transform_func']}: {e}")
        
        # --- PASO 5: Búsqueda Semántica (RAG) para preguntas generales o de normativa ---
        if categoria in ["document_qa", "general_info"] and self.indexer and self.qa_pipeline and self.indexer.esta_indexacion_completa():
            logger.debug("Intentando RAG mejorado (Búsqueda Semántica + QA Pipeline)...")
            
            # Buscar en todos los documentos indexados
            fragmentos_semanticos = self.indexer.buscar_pregunta_semantica(
                pregunta_texto,
                top_k=5
            )
            
            if isinstance(fragmentos_semanticos, str) and "No se encontraron fragmentos relevantes" not in fragmentos_semanticos:
                fragmentos_procesados = []
                for fragmento in fragmentos_semanticos.split("\n\n"):
                    if not fragmento.strip():
                        continue
                        
                    texto_fragmento = fragmento
                    if "📝 Fragmento:" in fragmento:
                        texto_fragmento = fragmento.split("📝 Fragmento:", 1)[1].split("\n")[0].strip()
                    
                    try:
                        resultado_qa = self.qa_pipeline(
                            question=pregunta_texto,
                            context=texto_fragmento,
                            max_answer_len=150,
                            handle_impossible_answer=True
                        )
                        
                        if resultado_qa and resultado_qa.get('answer') and resultado_qa['answer'].strip():
                            score = resultado_qa.get('score', 0)
                            if score > 0.4:  # Umbral para capturar respuestas relevantes
                                fragmentos_procesados.append((score, resultado_qa['answer']))
                    except Exception as e:
                        logger.error(f"Error en QA pipeline para fragmento: {e}")

                if fragmentos_procesados:
                    fragmentos_procesados.sort(reverse=True)
                    mejor_respuesta = fragmentos_procesados[0][1]
                    logger.info(f"Mejor respuesta RAG: {mejor_respuesta}")
                    return mejor_respuesta
        
        # --- PASO 6: Generación directa con T5 ---
        try:
            # Mejorar el prompt para preguntas sobre procedimientos y reglamento
            prompt = f"""Pregunta: {pregunta_texto}
Contexto: Esta es una pregunta sobre procedimientos de nómina o reglamento interno de la Universidad Icesi. 
Instrucciones: Genera una respuesta clara y concisa basada en la normativa y procedimientos de la empresa. 
Si la información no está disponible en los documentos, indica que necesitas más detalles o que la información no está especificada.
Respuesta:"""
            
            respuesta_t5 = self._generar_respuesta_t5(prompt)
            
            if respuesta_t5 and len(respuesta_t5) > 10:
                logger.info(f"Respuesta generada por T5: {respuesta_t5}")
                return respuesta_t5
                
        except Exception as e:
            logger.error(f"Error en generación T5: {e}")

        logger.warning(f"No se encontró respuesta adecuada para: \"{pregunta_texto}\"")
        return respuesta_final

    async def cargar_documentos(self, container: ui.element = None):
        if self.documentos_cargados:
            logger.info("Los documentos ya están cargados. No se realizará una nueva carga.")
            return True

        logger.info("Iniciando carga de documentos...")
        self.loading = True
        
        progress_bar = None
        progress_label = None
        progress_container_outer = None

        if container:
            with container:
                progress_container_outer = ui.column().classes('w-full items-center mt-4 gap-1')
                with progress_container_outer:
                    progress_label = ui.label('Cargando 0%').classes('text-sm font-medium text-gray-700')
                    progress_bar = ui.linear_progress(value=0, show_value=False).props('size=20px rounded color=primary')
                    progress_bar.classes('w-2/4')

        try:
            # Cargar documentos de SharePoint
            success = await self._cargar_documentos_sharepoint(progress_bar, progress_label)
            
            if success:
                if container:
                    progress_label.set_text('Cargando modelos...')
                    progress_bar.set_value(0.5)
                
                # Cargar modelos después de los documentos
                modelos_cargados = await self.cargar_modelos()
                
                if modelos_cargados:
                    if container:
                        ui.notify("✅ Documentos y modelos cargados correctamente", type="positive")
                    self.documentos_cargados = True
                else:
                    if container:
                        ui.notify("⚠️ Documentos cargados pero hubo problemas con los modelos", type="warning")
                    self.documentos_cargados = True  # Aún así marcamos documentos como cargados
            else:
                if container:
                    ui.notify("❌ Error al cargar documentos", type="negative")
            return success
            
        except Exception as e:
            logger.error(f"Error al cargar documentos: {str(e)}")
            if container:
                ui.notify(f"❌ Error al cargar documentos: {str(e)}", type="negative")
            return False
        finally:
            self.loading = False
            if progress_bar and progress_label and container:
                progress_container_outer.clear() 
                progress_bar.set_value(1.0)
                progress_label.set_text("Carga completa!")

    def _cargar_qa_pipeline(self):
        try:
            # Usar el modelo finetuneado local
            model_name_qa = self.MODELO_DIR
            logger.info(f"Cargando QA pipeline con el modelo finetuneado desde: {model_name_qa}...")
            self.qa_pipeline = hf_pipeline(
                "question-answering",
                model=model_name_qa,
                tokenizer=model_name_qa,
                device_map="cpu"
            )
            logger.info("QA pipeline cargado exitosamente con el modelo finetuneado.")
        except Exception as e:
            logger.error(f"Error al cargar el QA pipeline: {e}", exc_info=True)
            self.qa_pipeline = None

    async def solicitar_autenticacion(self, container: ui.column) -> bool:
        logger.info("Iniciando proceso de autenticación")
        if self.loading:
            logger.warning("Autenticación ya en progreso")
            return True
            
        try:
            accounts = self.app.get_accounts()
            logger.debug(f"Cuentas MSAL encontradas: {len(accounts)}")
            
            if accounts:
                logger.info("Intentando autenticación silenciosa MSAL...")
                result = self.app.acquire_token_silent(self.SCOPE, account=accounts[0])
                if result and "access_token" in result:
                    self.access_token = result["access_token"]
                    logger.info("Autenticación silenciosa MSAL exitosa.")
                    ui.notify("✅ Sesión activa detectada", type="positive")
                    return True
                else:
                    logger.info("Autenticación silenciosa MSAL fallida o token no encontrado.")
            
            logger.info("Iniciando flujo de dispositivo MSAL...")
            flow = self.app.initiate_device_flow(scopes=self.SCOPE)
            logger.debug(f"Flujo de dispositivo: {flow}")

            with ui.dialog().classes("w-full max-w-md") as dialog, ui.card().classes("gap-4 p-4 w-full"):
                ui.label("Autenticación Requerida").classes("text-lg font-bold text-primary")
                ui.markdown("**1. Copia este código:**").classes("text-sm font-medium")
                with ui.row().classes("items-center gap-2 w-full pl-4"):
                    ui.input(value=flow['user_code'], label="Código de verificación").props("readonly outlined dense").classes("w-64 font-mono bg-gray-50")
                    ui.button(icon="content_copy", on_click=lambda: self._copiar_al_portapapeles(flow['user_code']), color="primary").props("flat dense").tooltip("Copiar al portapapeles")
                ui.markdown("**2. Ingresa a la página de autenticación:**").classes("text-sm font-medium mt-4")
                with ui.row().classes("items-center gap-2 pl-4"):
                    ui.link(flow["verification_uri"], flow["verification_uri"], new_tab=True).classes("text-blue-600 text-sm truncate")
                    ui.button(icon="open_in_new", on_click=lambda: webbrowser.open(flow["verification_uri"]), color="primary").props("flat dense")
                ui.markdown("**3. Cuando hayas completado la autenticación:**").classes("text-sm font-medium mt-4")
                with ui.row().classes("pl-4"):
                    ui.button("Cargar Documentos", on_click=lambda: dialog.submit("continue"), icon="cloud_download").props("unelevated color=positive").classes("w-full")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancelar", on_click=lambda: dialog.submit("cancel"), color="gray").props("outlined")
                    ui.button("Cerrar", on_click=dialog.close, color="red").props("outlined").classes("w-24")
                
            result = await dialog
            if result == "cancel":
                raise Exception("Autenticación cancelada")

            result = self.app.acquire_token_by_device_flow(flow)
            if not result or "access_token" not in result:
                raise Exception("No se obtuvo token de acceso")

            self.access_token = result["access_token"]
            ui.notify("✅ Autenticación exitosa", type="positive")

            return True

        except Exception as e:
            logger.exception("Fallo crítico en autenticación")
            ui.notify(f"❌ Error en autenticación: {str(e)}", type="negative")
            return False
        finally:
            self.loading = False

    def _copiar_al_portapapeles(self, texto: str):
        """Copia texto al portapapeles y muestra notificación"""
        ui.run_javascript(f"navigator.clipboard.writeText('{texto}')")
        ui.notify("✓ Código copiado", type="positive", timeout=1000)

    async def _cargar_documentos_sharepoint(self, progress_bar: Optional[ui.linear_progress], progress_label: Optional[ui.label]) -> bool:
        """Carga los documentos desde SharePoint y los procesa."""
        logger.info("Preparando conexión a SharePoint")
        logger.debug(f"Usando token: {self.access_token[:15]}...")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://graph.microsoft.com/v1.0/sites/{self.SITE_ID}/drives/{self.DRIVE_ID}/root:/{self.FOLDER_PATH}:/children"
        logger.debug(f"URL de SharePoint: {url}")

        try:
            logger.info("Iniciando carga de documentos desde SharePoint...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                archivos_json = response.json().get("value", [])
                total_archivos = len(archivos_json)
                logger.info(f"Total de archivos encontrados: {total_archivos}")
                logger.info(f"Detalle de archivos: {[archivo.get('name', 'Sin nombre') for archivo in archivos_json]}")
                
                if total_archivos == 0 and progress_label:
                    progress_label.set_text("No se encontraron archivos en SharePoint.")
                    if progress_bar: progress_bar.set_value(1.0)
                    self.word_docs = {}
                    return True

                for index, archivo in enumerate(archivos_json, start=1):
                    await asyncio.sleep(0.1)
                    logger.debug(f"Procesando archivo: {archivo.get('name', 'Sin nombre')}")

                    progreso_actual = index / total_archivos
                    if progress_bar:
                        progress_bar.set_value(progreso_actual)
                    if progress_label:
                        progress_label.set_text(f'Cargando {progreso_actual:.0%}')
                
                if total_archivos > 0:
                    logger.info("Iniciando carga de archivos TXT...")
                    self.txt_cache = cargar_archivos_txt_desde_sharepoint(archivos_json)
                    logger.info(f"Archivos TXT cargados: {len(self.txt_cache)}")
                    
                    logger.info("Iniciando carga de documentos Word...")
                    self.word_docs = cargar_documentos_word_desde_sharepoint(archivos_json)
                    logger.info(f"Documentos Word cargados: {len(self.word_docs)}")
                    
                    if progress_label:
                        progress_label.set_text('Indexando documentos...')
                    
                    # Usar el indexador para procesar los documentos
                    logger.info("Iniciando indexación de documentos...")
                    await self.indexer.indexar_documentos(self.word_docs)
                    self.documentos_cargados = True
                    logger.info("Documentos indexados correctamente")
                    
                    if progress_label:
                        progress_label.set_text('Indexación completada')
                    
                    logger.info(f"Carga exitosa. TXT: {len(self.txt_cache)}, Word: {len(self.word_docs)}")
                elif total_archivos == 0:
                    logger.info("No se encontraron archivos para procesar en SharePoint.")
            
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code}. Response: {e.response.text}")
            if progress_label: progress_label.set_text(f"Error del servidor: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Error de conexión: {str(e)}")
            if progress_label: progress_label.set_text("Error de conexión con SharePoint")
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            logger.exception("Error inesperado al cargar documentos")
            if progress_label: progress_label.set_text(f"Error al procesar: {str(e)}")
        finally:
            logger.debug("Finalizando carga de SharePoint")
            if progress_bar and progress_label:
                 if progress_bar.value < 1.0 and "Error" not in progress_label.text and "No se encontraron" not in progress_label.text:
                     progress_label.set_text("Proceso finalizado.")

        return False

    async def main_page(self):
        logger.info("Ejecutando main_page")
        ui.label("Bienvenido a ChatNomina").classes("text-2xl font-bold")
        logger.debug(f"Estado inicial: documento={self.documento_usuario}, token={'Si' if self.access_token else 'No'}")
        
        main_container = ui.column().classes('w-full max-w-3xl mx-auto')
        
        if not await self.solicitar_autenticacion(main_container):
            with main_container:
                ui.label("No se pudo autenticar. Por favor, inténtalo de nuevo.").classes("text-red-500 text-lg")
            return

        await self.cargar_documentos(main_container)

        def send_message_and_process():
            """Captura el texto, lo procesa y actualiza el chat."""
            nonlocal user_id, avatar_user, avatar_system
            
            pregunta_actual = text_input.value.strip()
            if not pregunta_actual:
                ui.notify("Por favor, escribe un mensaje.", type='warning')
                return

            logger.debug(f"Usuario ({user_id}) envió: \"{pregunta_actual}\"")
            self.messages.append((user_id, avatar_user, pregunta_actual, datetime.now().strftime('%H:%M')))
            
            text_input.value = ''
            self.chat_messages_area.refresh()

            async def get_and_display_bot_response():
                respuesta_bot_texto = ""
                if pregunta_actual.strip().isdigit() and len(pregunta_actual.strip()) >= 6:
                    self.documento_usuario = pregunta_actual.strip()
                    logger.info(f"Documento guardado en caché: {self.documento_usuario}")
                    logger.info(f"Estado del caché TXT: {list(self.txt_cache.keys()) if self.txt_cache else 'Vacío'}")
                    logger.info(f"Estado del caché Word: {list(self.word_docs.keys()) if self.word_docs else 'Vacío'}")
                    
                    # Verificar si el documento existe en los cachés
                    doc_en_txt = any(self.documento_usuario in str(key) for key in self.txt_cache.keys())
                    doc_en_word = any(self.documento_usuario in str(key) for key in self.word_docs.keys())
                    logger.info(f"Documento encontrado en TXT: {doc_en_txt}, en Word: {doc_en_word}")
                    
                    respuesta_bot_texto = f"Documento ({self.documento_usuario}) registrado. Ahora puedes hacer preguntas sobre tu nómina."
                    logger.info(f"Documento de usuario ({user_id}) registrado: {self.documento_usuario}")
                else:
                    if not self.documento_usuario:
                        respuesta_bot_texto = "Por favor, registra tu número de documento primero."
                        logger.warning(f"Usuario ({user_id}) intentó preguntar sin registrar documento.")
                    elif not self.documentos_cargados and not any(kw in pregunta_actual.lower() for kw in ["vacaciones", "normativa", "ley"]):
                        respuesta_bot_texto = "Los documentos aún se están procesando o no están disponibles. Por favor, espera un momento o intenta con preguntas generales."
                        logger.warning(f"Usuario ({user_id}) preguntó '{pregunta_actual}' pero los documentos no están listos.")
                    else:
                        # Verificar estado del caché antes de procesar la pregunta
                        logger.info(f"Estado del caché antes de procesar pregunta:")
                        logger.info(f"- Documento usuario: {self.documento_usuario}")
                        logger.info(f"- Documentos cargados: {self.documentos_cargados}")
                        logger.info(f"- TXT Cache keys: {list(self.txt_cache.keys()) if self.txt_cache else 'Vacío'}")
                        logger.info(f"- Word Cache keys: {list(self.word_docs.keys()) if self.word_docs else 'Vacío'}")
                        
                        respuesta_bot_texto = self._responder_pregunta(pregunta_actual)
                
                self.messages.append(("system", avatar_system, respuesta_bot_texto, datetime.now().strftime('%H:%M')))
                self.chat_messages_area.refresh()

            asyncio.create_task(get_and_display_bot_response())

        user_id = str(uuid4())
        avatar_user = f'https://robohash.org/{user_id}?bgset=bg2'
        avatar_system = f'https://images.emojiterra.com/microsoft/fluent-emoji/15.1/128px/1f916_color.png'

        ui.add_css(r'''a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}.chat-input {width: 100%; max-width: 800px; margin: 0 auto;}''')
        
        with ui.header().classes('bg-white shadow-sm'):
            with ui.column().classes('w-full max-w-3xl mx-auto py-3'):
                ui.label('🤖 ChatNomina').classes('text-2xl font-bold text-primary')
                ui.label('Consulta información sobre tu nómina de forma automática').classes('text-sm text-gray-500')
                ui.label('Instrucciones').classes('text-sm text-gray-500')
                ui.label('1. Ingresa tu número de documento (solo números)').classes('text-sm text-gray-400')
                ui.label('2. Escribe tu pregunta sobre nómina').classes('text-sm text-gray-400')
                ui.label('3. Presiona Enter para enviar').classes('text-sm text-gray-400')
                ui.label('4. Proporciona feedback si la respuesta no es útil').classes('text-sm text-gray-400')
    
        self.chat_messages_area = ui.refreshable(self.chat_messages_ui_builder)
        self.chat_messages_area(user_id, avatar_system)

        with ui.footer().classes('bg-white border-t'), ui.column().classes('w-full max-w-3xl mx-auto py-4'):
            with ui.row().classes('w-full no-wrap items-center gap-2'):
                with ui.avatar():
                    ui.image(avatar_user)
                text_input = ui.input(placeholder='Ingresa tu documento o pregunta...') \
                    .on('keydown.enter', send_message_and_process) \
                    .props('rounded outlined input-class=mx-3') \
                    .classes('flex-grow')
                ui.button(icon='send', on_click=send_message_and_process).props('round dense')
        
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

    def manejar_feedback(self, pregunta: str, respuesta: str, es_util: bool):
        """Maneja el feedback del usuario sobre las respuestas."""
        if not es_util:
            with ui.dialog() as dialog, ui.card():
                ui.label("Por favor, ingresa más detalles sobre la respuesta")
                detalles = ui.textarea()
                ui.button("Enviar", on_click=lambda: self.guardar_feedback(pregunta, respuesta, detalles.value, dialog))
            dialog.open()

    def guardar_feedback(self, pregunta: str, respuesta: str, detalles: str, dialog) -> None:
        """Guarda el feedback en un archivo dentro de la carpeta feedback."""
        try:
            # Asegurar que el directorio existe
            FEEDBACK_DIR.mkdir(exist_ok=True)
            
            # Obtener timestamp actual
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(FEEDBACK_FILE, "a", encoding="utf-8") as file:
                file.write(f"[{timestamp}]\n")
                file.write(f"Pregunta: {pregunta}\n")
                file.write(f"Respuesta: {respuesta}\n")
                file.write(f"Detalles adicionales: {detalles}\n")
                file.write("-" * 80 + "\n\n")
            
            ui.notify("Gracias por tu retroalimentación. La hemos registrado para mejorar el sistema.", type='positive')
            dialog.close()
        except Exception as e:
            logger.error(f"Error al guardar feedback: {e}")
            ui.notify(f"Error al guardar feedback: {e}", type='negative')

    def chat_messages_ui_builder(self, user_id_actual: str, avatar_system: str):
        if not self.messages:
            with ui.column().classes('w-full items-center justify-center h-64'):
                 ui.icon('forum', size='xl', color='gray-400')
                 ui.label('Ingresa tu número de documento y luego haz tu pregunta.').classes('text-gray-500 text-center')
            return

        for msg_sender_id, avatar_system, msg_text, msg_stamp in self.messages:
            is_sent_by_current_user = (msg_sender_id == user_id_actual)
            
            display_name = "Tú" if is_sent_by_current_user else "ChatNomina"
            current_avatar = avatar_system
            
            with ui.chat_message(name=display_name, text=msg_text, stamp=msg_stamp, avatar=current_avatar, sent=is_sent_by_current_user):
                if not is_sent_by_current_user and (msg_sender_id, avatar_system, msg_text, msg_stamp) == self.messages[-1]:
                    if len(self.messages) >=2:
                        pregunta_asociada = self.messages[-2][2]
                        respuesta_actual_bot = msg_text

                        with ui.row().classes('w-full justify-end mt-1 py-1'):
                            ui.label('¿Útil?').classes('text-xs text-gray-500 mr-1')
                            ui.button(icon='thumb_up', on_click=lambda p=pregunta_asociada, r=respuesta_actual_bot: self.manejar_feedback(p, r, True)) \
                                .props('flat dense round color=positive').classes('p-0 m-0 w-6 h-6 min-w-0 min-h-0')
                            ui.button(icon='thumb_down', on_click=lambda p=pregunta_asociada, r=respuesta_actual_bot: self.manejar_feedback(p, r, False)) \
                                .props('flat dense round color=negative').classes('p-0 m-0 w-6 h-6 min-w-0 min-h-0')
        
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')

if __name__ in {'__main__', '__mp_main__'}:
    # Configurar multiprocessing para Windows
    if os.name == 'nt':
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)
    
    app_instance = ChatNominaApp()
    ui.page('/')(app_instance.main_page)
    ui.run(
        title='ChatNomina',
        native=True,
        window_size=(450, 750),
        favicon=None,
        reload=False  # Deshabilitar reload automático
    )