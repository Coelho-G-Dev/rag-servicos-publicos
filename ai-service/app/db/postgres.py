from contextlib import contextmanager
from typing import Generator, Optional
import psycopg
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from app.core.config import get_settings
from app.observability.logger import logger

_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        settings = get_settings()
        db_url = settings.get_database_url()
        logger.info("db_pool_init", host=settings.POSTGRES_HOST, db=settings.POSTGRES_DB)
        _pool = ConnectionPool(
            conninfo=db_url,
            min_size=1,
            max_size=10,
            timeout=10.0,
            configure=register_vector,
            open=True,
        )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None and not _pool.closed:
        _pool.close()
        _pool = None
        logger.info("db_pool_closed")


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Context manager para obter uma conexão do pool com pgvector registrado."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def check_db_health() -> bool:
    """Executa um ping simples no banco para checar conectividade."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return cur.fetchone() is not None
    except Exception as e:
        logger.warning("db_health_check_failed", error=str(e))
        return False


def init_db_schema() -> None:
    """Garante que a extensão vector e as tabelas estejam criadas no banco de dados."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                register_vector(conn)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public_services (
                        id VARCHAR(64) PRIMARY KEY,
                        nome VARCHAR(255) NOT NULL,
                        categoria VARCHAR(100) NOT NULL,
                        descricao TEXT NOT NULL,
                        endereco TEXT NOT NULL,
                        embedding vector(384),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_public_services_embedding 
                    ON public_services USING hnsw (embedding vector_cosine_ops);
                    CREATE INDEX IF NOT EXISTS idx_public_services_categoria 
                    ON public_services (categoria);
                    CREATE INDEX IF NOT EXISTS idx_public_services_nome 
                    ON public_services (nome);
                """)
                conn.commit()
        logger.info("db_schema_initialized_successfully")
    except Exception as e:
        logger.warning("db_schema_init_skipped_or_failed", error=str(e))
