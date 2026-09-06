"""
Teste de integração real com PostgreSQL + pgvector e modelo de embedding.
Marcado com @pytest.mark.integration para não rodar por padrão no CI ou sem banco ativo.
Para rodar localmente com Docker ativo:
    pytest -m integration
"""

import os
import psycopg
import pytest
from app.core.config import get_settings
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import VectorRetriever


@pytest.mark.integration
def test_real_postgres_vector_search():
    settings = get_settings()
    db_url = settings.get_database_url()

    try:
        with psycopg.connect(db_url, timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
    except Exception as exc:
        pytest.skip(f"PostgreSQL real indisponível em {db_url}: {exc}")

    embedding_service = EmbeddingService()
    query = "postos de vacinação infantil"
    vector = embedding_service.generate_embedding(query)
    assert len(vector) == 384

    retriever = VectorRetriever(top_k=2)
    results = retriever.search(vector)

    assert isinstance(results, list)
    if len(results) > 0:
        first = results[0]
        assert "nome" in first
        assert "similarity" in first
        assert -1.0 <= first["similarity"] <= 1.0
