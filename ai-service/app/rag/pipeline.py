import time
from typing import Any, Dict, List, Optional
from app.observability.logger import logger
from app.observability.metrics import (
    rag_generation_duration_seconds,
    rag_queries_total,
    rag_retrieval_duration_seconds,
    rag_retrieved_chunks_count,
)
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.generator import AnswerGenerator, get_generator
from app.rag.retriever import VectorRetriever, get_retriever


class RAGPipeline:
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        retriever: Optional[VectorRetriever] = None,
        generator: Optional[AnswerGenerator] = None,
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.retriever = retriever or get_retriever()
        self.generator = generator or get_generator()

    def process_query(self, message: str) -> Dict[str, Any]:
        """
        Executa o pipeline RAG completo:
        1. Gera embedding da mensagem localmente
        2. Busca no Postgres com pgvector
        3. Chama Gemini com contexto estrito
        4. Registra métricas e logs estruturados de rastreabilidade
        """
        start_total = time.perf_counter()

        start_emb = time.perf_counter()
        query_vector = self.embedding_service.generate_embedding(message)
        embedding_duration = time.perf_counter() - start_emb

        start_retrieval = time.perf_counter()
        retrieved_chunks = self.retriever.search(query_vector)
        retrieval_duration = time.perf_counter() - start_retrieval

        rag_retrieval_duration_seconds.observe(retrieval_duration)
        rag_retrieved_chunks_count.observe(len(retrieved_chunks))

        start_gen = time.perf_counter()
        try:
            answer = self.generator.generate_answer(message, retrieved_chunks)
            generation_duration = time.perf_counter() - start_gen
            rag_generation_duration_seconds.observe(generation_duration)
            rag_queries_total.labels(status="success").inc()
        except Exception as e:
            rag_queries_total.labels(status="error").inc()
            logger.error("rag_pipeline_generation_failed", error=str(e), query=message)
            raise

        sources: List[Dict[str, Any]] = [
            {
                "id": chunk["id"],
                "nome": chunk["nome"],
                "categoria": chunk["categoria"],
                "endereco": chunk["endereco"],
                "similarity": chunk.get("similarity", 0.0),
            }
            for chunk in retrieved_chunks
        ]
        source_ids = [s["id"] for s in sources]

        total_duration = time.perf_counter() - start_total

        logger.info(
            "rag_query_processed",
            query=message,
            chunks_retrieved_count=len(retrieved_chunks),
            source_ids=source_ids,
            embedding_duration_ms=round(embedding_duration * 1000, 2),
            retrieval_duration_ms=round(retrieval_duration * 1000, 2),
            generation_duration_ms=round(generation_duration * 1000, 2),
            total_duration_ms=round(total_duration * 1000, 2),
        )

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks,
        }


def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline()
