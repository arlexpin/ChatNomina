from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings
import uuid
import logging
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime
import pickle
import os
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IndexConfig:
    """Configuración mejorada para el indexador de documentos."""
    chunk_size: int = 10  # Aumentado para fragmentos más grandes
    batch_size: int = 32
    min_chunk_words: int = 10  # Aumentado para fragmentos más significativos
    model_name: str = "hiiamsid/sentence_similarity_spanish_es"  # Modelo específico para español
    collection_name: str = "documentos_institucionales"
    cache_dir: str = ".embedding_cache"
    compression_threshold: int = 1000
    max_workers: int = 4
    hybrid_search_weight: float = 0.7
    chunk_overlap: int = 3  # Aumentado para mejor contexto
    min_similarity_threshold: float = 0.55  # Reducido para más flexibilidad
    max_chunk_words: int = 300  # Aumentado para mantener más contexto
    context_window: int = 8  # Aumentado para mejor contexto
    onnx_providers: List[str] = None  # Nuevo campo para providers de ONNX
    training_data_weight: float = 0.8  # Peso para resultados del dataset de entrenamiento
    include_training_data: bool = True  # Incluir dataset de entrenamiento en búsquedas

    def __post_init__(self):
        # Configurar ONNX Runtime para usar solo CPU
        os.environ["ORT_TENSORRT_ENABLED"] = "0"
        os.environ["ORT_CUDA_ENABLED"] = "0"
        os.environ["ORT_CPU_ENABLED"] = "1"
        os.environ["ORT_PROVIDERS"] = "CPUExecutionProvider"
        os.environ["ORT_DISABLE_ALL"] = "1"
        self.onnx_providers = ["CPUExecutionProvider"]

class DocumentIndexer:
    def __init__(self, config: Optional[IndexConfig] = None):
        """Inicializa el indexador de documentos con configuración mejorada."""
        self.config = config or IndexConfig()
        self.embedding_cache = {}
        self._setup_directories()
        self.indexacion_completa = False
        self.training_data_indexed = False
        
        # Inicializar el modelo de embeddings con cache
        try:
            self.modelo_embeddings = SentenceTransformer(
                self.config.model_name,
                device="cpu",
                cache_folder=self.config.cache_dir
            )
            self._load_embedding_cache()
        except Exception as e:
            logger.error(f"Error al cargar el modelo de embeddings: {e}")
            raise

        # Crear cliente Chroma con persistencia y optimizaciones
        persist_path = Path.cwd() / ".chroma"
        try:
            self.client = chromadb.Client(Settings(
                persist_directory=str(persist_path),
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            ))
            self.coleccion = self.client.get_or_create_collection(
                self.config.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 64
                }
            )
            logger.info(f"Colección '{self.config.collection_name}' inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar ChromaDB: {e}")
            raise

    def _setup_directories(self):
        """Configura los directorios necesarios."""
        os.makedirs(self.config.cache_dir, exist_ok=True)

    def _load_embedding_cache(self):
        """Carga el cache de embeddings desde disco."""
        cache_file = Path(self.config.cache_dir) / "embedding_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                logger.info(f"Cache de embeddings cargado: {len(self.embedding_cache)} entradas")
            except Exception as e:
                logger.warning(f"Error al cargar cache de embeddings: {e}")

    def _save_embedding_cache(self):
        """Guarda el cache de embeddings en disco."""
        cache_file = Path(self.config.cache_dir) / "embedding_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            logger.info(f"Cache de embeddings guardado: {len(self.embedding_cache)} entradas")
        except Exception as e:
            logger.warning(f"Error al guardar cache de embeddings: {e}")

    def _get_embedding(self, text: str) -> np.ndarray:
        """Obtiene el embedding de un texto con cache."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        embedding = self.modelo_embeddings.encode(text, convert_to_numpy=True)
        self.embedding_cache[text] = embedding
        return embedding

    def _chunk_text(self, text: str) -> List[str]:
        """Divide el texto en fragmentos de manera más inteligente y contextual."""
        if not text or not isinstance(text, str):
            logger.warning("Texto inválido o vacío recibido en _chunk_text")
            return []
            
        # Dividir por párrafos primero
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            # Limpiar y normalizar el párrafo
            paragraph = re.sub(r'\s+', ' ', paragraph).strip()
            if not paragraph:
                continue
                
            # Detectar si es un título o encabezado
            is_heading = bool(re.match(r'^[A-Z][A-Z\s]+$', paragraph)) or len(paragraph.split()) <= 5
            
            # Dividir en oraciones para mejor contexto
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            # Si es un título, mantenerlo con el siguiente párrafo
            if is_heading and sentences:
                heading = sentences.pop(0)
                if sentences:
                    current_chunk.append(f"{heading} {sentences[0]}")
                    current_length += len(heading.split()) + len(sentences[0].split())
                    sentences.pop(0)
                else:
                    current_chunk.append(heading)
                    current_length += len(heading.split())
            
            # Procesar cada oración
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                words = len(sentence.split())
                
                # Si la oración es muy larga, dividirla en suboraciones
                if words > self.config.max_chunk_words:
                    sub_sentences = re.split(r'(?<=[,;:])\s+', sentence)
                    for sub in sub_sentences:
                        sub = sub.strip()
                        if len(sub.split()) >= self.config.min_chunk_words:
                            if not current_chunk:
                                chunks.append(sub)
                            else:
                                if current_length + len(sub.split()) <= self.config.max_chunk_words:
                                    current_chunk.append(sub)
                                    current_length += len(sub.split())
                                else:
                                    chunks.append(" ".join(current_chunk))
                                    current_chunk = [sub]
                                    current_length = len(sub.split())
                    continue
                
                # Si el chunk actual más la nueva oración excede el límite
                if current_length + words > self.config.max_chunk_words:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_length = words
                else:
                    current_chunk.append(sentence)
                    current_length += words
                
                # Si alcanzamos el tamaño del chunk, guardarlo
                if len(current_chunk) >= self.config.chunk_size:
                    chunks.append(" ".join(current_chunk))
                    # Mantener algunas oraciones para el siguiente chunk (overlap)
                    overlap = current_chunk[-self.config.chunk_overlap:] if self.config.chunk_overlap > 0 else []
                    current_chunk = overlap
                    current_length = sum(len(s.split()) for s in overlap)
        
        # Agregar el último chunk si existe
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Filtrar y limpiar chunks
        cleaned_chunks = []
        for chunk in chunks:
            # Limpiar espacios y caracteres especiales
            chunk = re.sub(r'\s+', ' ', chunk).strip()
            # Verificar longitud y contenido significativo
            words = len(chunk.split())
            if (self.config.min_chunk_words <= words <= self.config.max_chunk_words and 
                len(re.findall(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', chunk)) > 0):  # Asegurar que hay texto significativo
                cleaned_chunks.append(chunk)
        
        logger.debug(f"Generados {len(cleaned_chunks)} chunks limpios")
        return cleaned_chunks

    async def _process_batch_async(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """Procesa un lote de documentos de manera asíncrona."""
        try:
            # Generar embeddings en paralelo
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                embeddings = list(executor.map(self._get_embedding, documents))
            
            # Comprimir embeddings si es necesario
            if len(documents) > self.config.compression_threshold:
                embeddings = [self._compress_embedding(emb) for emb in embeddings]
            
            # Agregar a ChromaDB
            self.coleccion.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Error al procesar lote asíncrono: {e}")
            raise

    def _compress_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Comprime el embedding usando PCA simple."""
        # Implementación básica de compresión
        return embedding.astype(np.float32)

    def reiniciar_indexacion(self):
        """Reinicia la indexación eliminando todos los documentos existentes."""
        try:
            logger.info("Iniciando reinicio de indexación...")
            
            # Obtener todos los documentos
            resultados = self.coleccion.get()
            if not resultados or not resultados['ids']:
                logger.info("No hay documentos para eliminar")
                return
                
            total_docs = len(resultados['ids'])
            logger.info(f"Encontrados {total_docs} documentos para eliminar")
            
            # Eliminar documentos en lotes
            batch_size = 100
            for i in range(0, total_docs, batch_size):
                batch_ids = resultados['ids'][i:i + batch_size]
                try:
                    self.coleccion.delete(ids=batch_ids)
                    logger.info(f"Eliminados {len(batch_ids)} documentos (lote {i//batch_size + 1})")
                except Exception as e:
                    logger.error(f"Error eliminando lote {i//batch_size + 1}: {str(e)}")
                    
            # Limpiar caché de embeddings
            self.embedding_cache.clear()
            logger.info("Caché de embeddings limpiada")
            
            # Verificar que la colección está vacía
            resultados = self.coleccion.get()
            if not resultados or not resultados['ids']:
                logger.info("Reinicio de indexación completado exitosamente")
            else:
                logger.warning(f"Quedaron {len(resultados['ids'])} documentos sin eliminar")
                
        except Exception as e:
            logger.error(f"Error en reinicio de indexación: {str(e)}", exc_info=True)
            raise

    async def indexar_documentos(self, documentos: Dict[str, str]) -> None:
        """Indexa los documentos proporcionados usando embeddings."""
        try:
            if not documentos:
                logger.warning("No hay documentos para indexar")
                return
                
            logger.info(f"Iniciando indexación de {len(documentos)} documentos...")
            total_fragmentos = 0
            documentos_procesados = 0
            
            for nombre, contenido in documentos.items():
                try:
                    logger.info(f"Procesando documento: {nombre}")
                    
                    # Dividir en fragmentos
                    fragmentos = self._chunk_text(contenido)
                    if not fragmentos:
                        logger.warning(f"No se generaron fragmentos para {nombre}")
                        continue
                        
                    logger.info(f"Generados {len(fragmentos)} fragmentos para {nombre}")
                    total_fragmentos += len(fragmentos)
                    
                    # Procesar fragmentos en lotes
                    batch_size = self.config.batch_size
                    for i in range(0, len(fragmentos), batch_size):
                        batch = fragmentos[i:i + batch_size]
                        try:
                            # Generar embeddings para el lote
                            embeddings = await self._process_batch_async(batch, [{
                                "origen": nombre,
                                "fecha_indexacion": datetime.now().isoformat(),
                                "chunk_index": j,
                                "total_chunks": len(fragmentos)
                            } for j in range(i, min(i + batch_size, len(fragmentos)))], [f"{nombre}_{j+1}" for j in range(i, min(i + batch_size, len(fragmentos)))]
                            )
                            
                            logger.debug(f"Indexado lote {i//batch_size + 1} de {nombre}: {len(batch)} fragmentos")
                            
                        except Exception as e:
                            logger.error(f"Error procesando lote {i//batch_size + 1} de {nombre}: {str(e)}")
                            continue
                            
                    documentos_procesados += 1
                    logger.info(f"Documento {nombre} indexado exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error procesando documento {nombre}: {str(e)}", exc_info=True)
                    continue
                    
            # Verificar resultados
            resultados = self.coleccion.get()
            total_indexados = len(resultados['ids']) if resultados and resultados['ids'] else 0
            
            logger.info(f"""
            Resumen de indexación:
            - Documentos procesados: {documentos_procesados}/{len(documentos)}
            - Fragmentos generados: {total_fragmentos}
            - Fragmentos indexados: {total_indexados}
            """)
            
            self.indexacion_completa = True
            
        except Exception as e:
            logger.error(f"Error en indexación: {str(e)}", exc_info=True)
            raise

    def esta_indexacion_completa(self) -> bool:
        """Retorna si la indexación está completa."""
        return self.indexacion_completa

    async def indexar_dataset_entrenamiento(self, dataset_path: str) -> None:
        """Indexa el dataset de entrenamiento como fuente adicional de conocimiento."""
        try:
            if not self.config.include_training_data:
                logger.info("Indexación de dataset de entrenamiento desactivada en configuración")
                return

            logger.info(f"Iniciando indexación del dataset de entrenamiento desde: {dataset_path}")
            
            # Cargar dataset
            try:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    dataset = json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar dataset de entrenamiento: {e}")
                return

            # Preparar documentos para indexación
            documentos = []
            metadatas = []
            ids = []
            
            for i, (pregunta, respuesta) in enumerate(zip(dataset['question'], dataset['answer'])):
                # Crear documento combinando pregunta y respuesta
                doc = f"Pregunta: {pregunta}\nRespuesta: {respuesta}"
                documentos.append(doc)
                
                # Metadata específica para dataset de entrenamiento
                metadatas.append({
                    "origen": "dataset_entrenamiento",
                    "tipo": "qa_pair",
                    "pregunta": pregunta,
                    "respuesta": respuesta,
                    "fecha_indexacion": datetime.now().isoformat(),
                    "chunk_index": i
                })
                
                ids.append(f"training_{i+1}")

            # Indexar en lotes
            batch_size = self.config.batch_size
            for i in range(0, len(documentos), batch_size):
                batch_docs = documentos[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                try:
                    await self._process_batch_async(batch_docs, batch_metadatas, batch_ids)
                    logger.debug(f"Indexado lote {i//batch_size + 1} del dataset de entrenamiento")
                except Exception as e:
                    logger.error(f"Error procesando lote {i//batch_size + 1} del dataset: {str(e)}")
                    continue

            self.training_data_indexed = True
            logger.info(f"Dataset de entrenamiento indexado exitosamente: {len(documentos)} pares QA")
            
        except Exception as e:
            logger.error(f"Error en indexación del dataset: {str(e)}", exc_info=True)
            raise

    def buscar_pregunta_semantica(
        self, 
        pregunta: str, 
        top_k: int = 5,
        filtros: Optional[Dict] = None,
        use_hybrid: bool = True
    ) -> str:
        """Búsqueda semántica mejorada con soporte para dataset de entrenamiento."""
        try:
            # Normalizar la pregunta
            pregunta = pregunta.strip().lower()
            
            # Ajustar filtros para incluir dataset de entrenamiento si está indexado
            if filtros is None:
                filtros = {
                    "origen": {
                        "$in": [
                            "REGLAMENTO INTERNO DE TRABAJO - MODIFICACIÓN V2.docx",
                            "Procedimiento Liquidación de nómina.docx"
                        ]
                    }
                }
                
                if self.training_data_indexed and self.config.include_training_data:
                    filtros["origen"]["$in"].append("dataset_entrenamiento")

            # Realizar búsqueda semántica
            resultados = self.coleccion.query(
                query_texts=[pregunta],
                n_results=top_k * 5,
                include=["documents", "metadatas", "distances"],
                where=filtros
            )

            if not resultados['documents'] or not resultados['documents'][0]:
                logger.warning(f"No se encontraron resultados para la pregunta: {pregunta}")
                return "No se encontraron resultados relevantes en la documentación."

            respuestas = []
            scores = []
            seen_docs = set()

            # Procesar y rankear resultados
            for i in range(len(resultados['documents'][0])):
                fragmento = resultados['documents'][0][i]
                metadata = resultados['metadatas'][0][i]
                score = resultados.get('distances', [[]])[0][i] if 'distances' in resultados else None

                if score is not None:
                    # Normalizar score
                    normalized_score = 1 - score

                    # Ajustar umbral y pesos según el origen
                    if metadata['origen'] == "dataset_entrenamiento":
                        min_threshold = 0.45  # Umbral más bajo para dataset de entrenamiento
                        final_score = normalized_score * self.config.training_data_weight
                    else:
                        min_threshold = self.config.min_similarity_threshold
                        length_score = min(1.0, len(fragmento.split()) / self.config.max_chunk_words)
                        keyword_score = self._calculate_keyword_score(pregunta, fragmento)
                        final_score = (
                            normalized_score * 0.5 +
                            length_score * 0.3 +
                            keyword_score * 0.2
                        )

                    if normalized_score < min_threshold:
                        continue

                    # Formatear respuesta según el origen
                    if metadata['origen'] == "dataset_entrenamiento":
                        respuesta = (
                            f"📚 Respuesta del Dataset de Entrenamiento:\n"
                            f"❓ Pregunta Original: {metadata['pregunta']}\n"
                            f"✅ Respuesta: {metadata['respuesta']}\n"
                            f"🎯 Relevancia: {final_score:.2%}"
                        )
                    else:
                        respuesta = (
                            f"📄 Documento: {metadata['origen']}\n"
                            f"📝 Fragmento: {fragmento}\n"
                            f"🎯 Relevancia: {final_score:.2%}"
                        )

                    # Solo incluir si es un documento nuevo o tiene mejor score
                    doc_id = f"{metadata['origen']}_{metadata.get('chunk_index', i)}"
                    if doc_id not in seen_docs or final_score > max(scores):
                        scores.append(final_score)
                        respuestas.append(respuesta)
                        seen_docs.add(doc_id)

            # Ordenar y seleccionar mejores resultados
            if respuestas:
                sorted_results = [r for _, r in sorted(zip(scores, respuestas), reverse=True)]
                return "\n\n".join(sorted_results[:top_k])
            else:
                logger.warning(f"No se encontraron resultados relevantes para: {pregunta}")
                return "No se encontraron resultados relevantes en la documentación."

        except Exception as e:
            logger.error(f"Error durante la búsqueda: {e}", exc_info=True)
            return f"Error al procesar la consulta: {str(e)}"

    def _calculate_keyword_score(self, query: str, text: str) -> float:
        """Calcula un score basado en coincidencia de palabras clave."""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        # Calcular Jaccard similarity
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        if union == 0:
            return 0.0
            
        return intersection / union

    def _combine_search_results(
        self, 
        semantic_results: Dict, 
        keyword_results: Dict,
        query: str
    ) -> Dict:
        """Combina y re-ranking resultados de búsqueda híbrida."""
        try:
            combined_docs = []
            combined_metadatas = []
            combined_distances = []
            seen_ids = set()
            
            # Función para procesar resultados
            def process_results(results, weight=1.0):
                if not results['documents'] or not results['documents'][0]:
                    return
                    
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results.get('distances', [[]])[0][i] if 'distances' in results else None
                    
                    # Usar metadata como identificador único
                    doc_id = f"{metadata['origen']}_{metadata.get('chunk_index', i)}"
                    
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        combined_docs.append(doc)
                        combined_metadatas.append(metadata)
                        
                        if distance is not None:
                            # Ajustar distancia según el peso
                            adjusted_distance = distance * weight
                            combined_distances.append(adjusted_distance)
                        else:
                            combined_distances.append(1.0)
            
            # Procesar resultados semánticos (mayor peso)
            process_results(semantic_results, weight=0.7)
            
            # Procesar resultados keyword (menor peso)
            process_results(keyword_results, weight=0.3)
            
            # Re-ranking basado en scores combinados
            if combined_distances:
                # Calcular scores finales
                final_scores = []
                for i, doc in enumerate(combined_docs):
                    semantic_score = 1 - combined_distances[i]
                    keyword_score = self._calculate_keyword_score(query, doc)
                    final_score = semantic_score * 0.7 + keyword_score * 0.3
                    final_scores.append(final_score)
                
                # Ordenar por score final
                sorted_indices = sorted(range(len(final_scores)), key=lambda i: final_scores[i], reverse=True)
                
                return {
                    'documents': [[combined_docs[i] for i in sorted_indices]],
                    'metadatas': [[combined_metadatas[i] for i in sorted_indices]],
                    'distances': [[1 - final_scores[i] for i in sorted_indices]]
                }
            
            return {
                'documents': [combined_docs],
                'metadatas': [combined_metadatas],
                'distances': [combined_distances]
            }
            
        except Exception as e:
            logger.error(f"Error al combinar resultados: {e}")
            # En caso de error, retornar resultados semánticos
            return semantic_results

    def limpiar_cache(self):
        """Limpia el cache de embeddings."""
        self.embedding_cache.clear()
        self._save_embedding_cache()
        logger.info("Cache de embeddings limpiado")

    def optimizar_indice(self):
        """Optimiza el índice para mejor rendimiento."""
        try:
            # Actualizar configuración de HNSW
            self.coleccion.update(
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 64
                }
            )
            
            # Reconstruir índice si es necesario
            if len(self.coleccion.get()['ids']) > 10000:
                logger.info("Reconstruyendo índice para optimización...")
                self.coleccion.rebuild()
            
            logger.info("Índice optimizado correctamente")
        except Exception as e:
            logger.error(f"Error al optimizar índice: {e}")
            raise