from typing import Any, Dict, List, Optional
import numpy as np
from app.core.config import get_settings
from app.db.postgres import get_db_connection
from app.observability.logger import logger


class VectorRetriever:
    def __init__(self, top_k: Optional[int] = None):
        self.top_k = top_k or get_settings().TOP_K_RESULTS

    def search(self, query_vector: List[float], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Busca os k serviços mais similares no Postgres utilizando o operador <=> (distância de cosseno).
        """
        k = top_k or self.top_k
        query = """
            SELECT 
                id, 
                nome, 
                categoria, 
                descricao, 
                endereco,
                1 - (embedding <=> %s::vector) AS similarity
            FROM public_services
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        results: List[Dict[str, Any]] = []
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (np.array(query_vector), np.array(query_vector), k))
                    rows = cur.fetchall()
                    for row in rows:
                        results.append({
                            "id": row[0],
                            "nome": row[1],
                            "categoria": row[2],
                            "descricao": row[3],
                            "endereco": row[4],
                            "similarity": float(row[5]) if row[5] is not None else 0.0,
                        })
        except Exception as e:
            logger.error("retriever_query_failed", error=str(e))
            raise

        return results


def get_retriever() -> VectorRetriever:
    return VectorRetriever()
