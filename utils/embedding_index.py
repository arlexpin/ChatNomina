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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IndexConfig:
    """Configuración mejorada para el indexador de documentos."""
    chunk_size: int = 3  # Reducido para fragmentos más concisos
    batch_size: int = 32
    min_chunk_words: int = 10  # Aumentado para asegurar fragmentos significativos
    model_name: str = "all-mpnet-base-v2"
    collection_name: str = "documentos_institucionales"
    cache_dir: str = ".embedding_cache"
    compression_threshold: int = 1000
    max_workers: int = 4
    hybrid_search_weight: float = 0.7
    chunk_overlap: int = 1  # Reducido para minimizar redundancia
    min_similarity_threshold: float = 0.65  # Aumentado para mayor precisión
    max_chunk_words: int = 150  # Aumentado para mantener más contexto
    context_window: int = 3  # Aumentado para mejor contexto

class DocumentIndexer:
    def __init__(self, config: Optional[IndexConfig] = None):
        """Inicializa el indexador de documentos con configuración mejorada."""
        self.config = config or IndexConfig()
        self.embedding_cache = {}
        self._setup_directories()
        self.indexacion_completa = False
        
        # Inicializar el modelo de embeddings con cache
        try:
            self.modelo_embeddings = SentenceTransformer(self.config.model_name)
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
                allow_reset=True
            ))
            self.coleccion = self.client.get_or_create_collection(
                self.config.collection_name,
                metadata={"hnsw:space": "cosine", "hnsw:construction_ef": 100}
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
            
            # Si es un título, mantenerlo con la siguiente oración
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
                            # Si el chunk actual está vacío, agregar el sub como nuevo chunk
                            if not current_chunk:
                                chunks.append(sub)
                            else:
                                # Agregar el sub al chunk actual si hay espacio
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

    async def reiniciar_indexacion(self) -> None:
        """Reinicia la indexación limpiando la colección existente."""
        try:
            # Obtener todos los IDs existentes
            resultados = self.coleccion.get()
            if resultados and resultados['ids']:
                self.coleccion.delete(ids=resultados['ids'])
                logger.info(f"Colección limpiada: {len(resultados['ids'])} documentos eliminados")
            self.indexacion_completa = False
        except Exception as e:
            logger.error(f"Error al reiniciar indexación: {e}")
            raise

    async def indexar_documentos(self, documentos_dict: Dict[str, str]) -> int:
        """Indexa documentos de manera asíncrona y eficiente."""
        total_fragmentos = 0
        tasks = []
        documentos_procesados = 0
        
        try:
            # Reiniciar la indexación
            await self.reiniciar_indexacion()
            
            for nombre_doc, texto in documentos_dict.items():
                if not texto or not isinstance(texto, str):
                    logger.warning(f"Documento inválido o vacío: {nombre_doc}")
                    continue
                    
                logger.info(f"Procesando documento: {nombre_doc}")
                fragmentos = self._chunk_text(texto)
                
                if not fragmentos:
                    logger.warning(f"No se generaron fragmentos para {nombre_doc}")
                    continue
                    
                logger.info(f"Generados {len(fragmentos)} fragmentos para {nombre_doc}")
                documentos_procesados += 1
                
                # Procesar en lotes asíncronos
                for i in range(0, len(fragmentos), self.config.batch_size):
                    batch = fragmentos[i:i + self.config.batch_size]
                    batch_documents = batch
                    batch_metadatas = [{
                        "origen": nombre_doc,
                        "fecha_indexacion": datetime.now().isoformat(),
                        "chunk_index": j,
                        "total_chunks": len(fragmentos)
                    } for j in range(i, i + len(batch))]
                    batch_ids = [f"{nombre_doc}_{j}" for j in range(i, i + len(batch))]
                    
                    task = asyncio.create_task(
                        self._process_batch_async(batch_documents, batch_metadatas, batch_ids)
                    )
                    tasks.append(task)
                    total_fragmentos += len(batch)
            
            # Esperar a que todos los lotes se procesen
            if tasks:
                await asyncio.gather(*tasks)
                logger.info(f"Procesados {documentos_procesados} documentos, {total_fragmentos} fragmentos en total")
                self.indexacion_completa = True
            else:
                logger.warning("No se generaron tareas de indexación")
            
            # Guardar cache de embeddings
            self._save_embedding_cache()
            
            return total_fragmentos
            
        except Exception as e:
            logger.error(f"Error durante la indexación: {e}")
            self.indexacion_completa = False
            raise

    def esta_indexacion_completa(self) -> bool:
        """Retorna si la indexación está completa."""
        return self.indexacion_completa

    def buscar_pregunta_semantica(
        self, 
        pregunta: str, 
        top_k: int = 5,
        filtros: Optional[Dict] = None,
        use_hybrid: bool = True
    ) -> str:
        """Búsqueda semántica mejorada con fragmentos más largos y contextuales."""
        try:
            # Preparar la consulta
            query_embedding = self._get_embedding(pregunta)
            
            # Configurar parámetros de búsqueda
            search_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k * 3,  # Aumentado para obtener más resultados
                "where": filtros if filtros else None
            }
            
            if use_hybrid:
                # Búsqueda híbrida mejorada
                keyword_results = self.coleccion.query(
                    query_texts=[pregunta],
                    n_results=top_k * 4,  # Aumentado para más resultados
                    where=filtros
                )
                
                semantic_results = self.coleccion.query(**search_params)
                
                # Combinar y re-ranking de resultados
                combined_results = self._combine_search_results(
                    semantic_results, 
                    keyword_results,
                    pregunta
                )
                
                resultados = combined_results
            else:
                resultados = self.coleccion.query(**search_params)

            if not resultados['documents'] or not resultados['documents'][0]:
                return "No se encontraron fragmentos relevantes para la consulta."

            # Formatear y re-ranking de resultados
            respuestas = []
            scores = []
            
            for i in range(len(resultados['documents'][0])):
                fragmento = resultados['documents'][0][i]
                metadata = resultados['metadatas'][0][i]
                score = resultados.get('distances', [[]])[0][i] if 'distances' in resultados else None
                
                # Calcular score combinado
                if score is not None:
                    # Normalizar score
                    normalized_score = 1 - score
                    
                    # Aplicar umbral de similitud más flexible
                    if normalized_score < self.config.min_similarity_threshold:
                        continue
                    
                    # Calcular score adicional basado en longitud y relevancia
                    length_score = min(1.0, len(fragmento.split()) / self.config.max_chunk_words)  # Normalizar por longitud máxima
                    keyword_score = self._calculate_keyword_score(pregunta, fragmento)
                    
                    # Score final combinado con más peso a la longitud
                    final_score = (normalized_score * 0.5 + length_score * 0.3 + keyword_score * 0.2)
                    
                    scores.append(final_score)
                    
                    # Formatear respuesta con más contexto
                    respuesta = (
                        f"📄 Documento: {metadata['origen']}\n"
                        f"📅 Indexado: {metadata.get('fecha_indexacion', 'N/A')}\n"
                        f"📝 Fragmento: {fragmento}\n"
                        f"🎯 Relevancia: {final_score:.2%}"
                    )
                    
                    respuestas.append(respuesta)

            # Ordenar por score final y asegurar respuestas más largas
            if respuestas:
                sorted_results = [r for _, r in sorted(zip(scores, respuestas), reverse=True)]
                # Seleccionar los mejores resultados asegurando variedad
                selected_results = []
                seen_docs = set()
                
                for result in sorted_results:
                    doc_name = result.split('\n')[0]  # Obtener nombre del documento
                    if doc_name not in seen_docs or len(selected_results) < top_k:
                        selected_results.append(result)
                        seen_docs.add(doc_name)
                    if len(selected_results) >= top_k:
                        break
                
                return "\n\n".join(selected_results)
            else:
                return "No se encontraron resultados relevantes."

        except Exception as e:
            logger.error(f"Error durante la búsqueda: {e}")
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