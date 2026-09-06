CREATE EXTENSION IF NOT EXISTS vector;

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
