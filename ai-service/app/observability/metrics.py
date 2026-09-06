from prometheus_client import Counter, Histogram

rag_queries_total = Counter(
    "rag_queries_total",
    "Total de queries RAG processadas pelo AI Service",
    ["status"]
)

rag_retrieval_duration_seconds = Histogram(
    "rag_retrieval_duration_seconds",
    "Duração da busca por similaridade vetorial no pgvector em segundos",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

rag_generation_duration_seconds = Histogram(
    "rag_generation_duration_seconds",
    "Duração da geração de resposta pelo modelo Gemini em segundos",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
)

rag_retrieved_chunks_count = Histogram(
    "rag_retrieved_chunks_count",
    "Quantidade de trechos relevantes recuperados por consulta",
    buckets=[0, 1, 2, 3, 4, 5, 8, 10]
)

rag_llm_errors_total = Counter(
    "rag_llm_errors_total",
    "Total de erros na comunicação com o provedor LLM",
    ["error_type"]
)
