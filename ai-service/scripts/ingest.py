#!/usr/bin/env python3
"""
Script de ingestão de dados para o RAG de Serviços Públicos de São Luís.
Lê o dataset servicos_seed.json, gera embeddings vetoriais locais (all-MiniLM-L6-v2)
e popula a tabela public_services no PostgreSQL com pgvector.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

CURRENT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = CURRENT_DIR.parent
ROOT_DIR = AI_SERVICE_DIR.parent

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "rag_db")
DB_USER = os.getenv("POSTGRES_USER", "rag_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_password")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")


def find_seed_file() -> Path:
    """Localiza o arquivo de seed de serviços."""
    candidates = [
        AI_SERVICE_DIR / "data" / "servicos_seed.json",
        ROOT_DIR / "data" / "servicos_seed.json",
        Path("data/servicos_seed.json"),
        Path("ai-service/data/servicos_seed.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Arquivo servicos_seed.json não encontrado nos caminhos: {candidates}")


def build_text_for_embedding(item: Dict[str, Any]) -> str:
    """Concatena os campos do serviço público em um texto representativo para o embedding."""
    return (
        f"Nome: {item['nome']}. "
        f"Categoria: {item['categoria']}. "
        f"Endereço: {item['endereco']}. "
        f"Descrição: {item['descricao']}"
    )


def init_db(conn: psycopg.Connection) -> None:
    """Cria a extensão vector e a tabela public_services caso não existam."""
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


def run_ingest():
    seed_path = find_seed_file()
    print(f"[*] Lendo dataset seed de: {seed_path}")
    with open(seed_path, "r", encoding="utf-8") as f:
        services: List[Dict[str, Any]] = json.load(f)

    total_records = len(services)
    print(f"[*] Total de serviços carregados: {total_records}")

    print(f"[*] Carregando modelo local de embeddings: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [build_text_for_embedding(s) for s in services]
    print(f"[*] Gerando embeddings para {total_records} serviços...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    print(f"[*] Conectando ao PostgreSQL em: {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            init_db(conn)
            register_vector(conn)

            upsert_query = """
                INSERT INTO public_services (id, nome, categoria, descricao, endereco, embedding, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    categoria = EXCLUDED.categoria,
                    descricao = EXCLUDED.descricao,
                    endereco = EXCLUDED.endereco,
                    embedding = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP;
            """

            with conn.cursor() as cur:
                for service, emb in zip(services, embeddings):
                    cur.execute(
                        upsert_query,
                        (
                            service["id"],
                            service["nome"],
                            service["categoria"],
                            service["descricao"],
                            service["endereco"],
                            emb.tolist(),
                        ),
                    )
            conn.commit()
            print(f"[+] Ingestão concluída com sucesso! {total_records} registros inseridos/atualizados com pgvector.")
    except Exception as e:
        print(f"[!] Erro ao conectar ou inserir no banco de dados: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    run_ingest()
