# RAG Serviços Públicos - São Luís (MA)

Sistema de busca e respostas fundamentadas sobre serviços públicos municipais e estaduais de São Luís/MA, implementado em microsserviços desacoplados utilizando a arquitetura RAG (Retrieval-Augmented Generation).

O projeto combina busca semântica em banco vetorial (PostgreSQL + pgvector) com geração restrita de respostas via LLM (Google Gemini), garantindo rastreabilidade das fontes e prevenindo alucinações por meio de injeção estrita de contexto.

---

## Arquitetura

O sistema é dividido em três componentes principais:

```
[Cliente / Frontend]
        |
   HTTP (Porta 3000)
        v
+-------------------------------------------------------------+
| Gateway Público (Node.js / Express / TypeScript)            |
| - Rate Limiting (express-rate-limit)                        |
| - Logs estruturados em JSON (Pino)                          |
| - Métricas Prometheus (prom-client)                         |
| - Documentação interativa Swagger UI (/docs, /api-docs)     |
| - Endpoints de Health e Readiness (/health, /ready)         |
| - Rota relacional direta (/api/v1/services)                 |
+-------------------------------------------------------------+
        |                                       |
   HTTP Interno                               SQL Direto
 (X-Internal-Secret)                            |
        v                                       v
+------------------------------------+   +--------------------+
| AI Service (Python 3.11 / FastAPI) |   | PostgreSQL 16      |
| - Embeddings: all-MiniLM-L6-v2     |-->| + pgvector         |
| - Busca vetorial: HNSW / Cosseno   |   |                    |
| - LLM: Google Gemini 1.5 Flash     |   | Tabela:            |
| - Métricas de latência e chunks    |   | public_services    |
+------------------------------------+   +--------------------+
        |
   Google Gemini API
```

### Componentes

- **API Gateway (`gateway/`)**: Desenvolvido em Node.js com TypeScript e Express. Centraliza a entrada pública, validação de requisições, controle de taxa, observabilidade e documentação OpenAPI.
- **AI Service (`ai-service/`)**: Microsserviço Python com FastAPI. Realiza a inferência de embeddings localmente por meio do modelo `sentence-transformers/all-MiniLM-L6-v2` (384 dimensões), executa a busca vetorial no pgvector e orquestra a geração de resposta com o Google Gemini.
- **PostgreSQL com pgvector**: Persistência de dados relacionais e vetoriais, utilizando índice HNSW (`vector_cosine_ops`) para busca por similaridade em frações de segundo.

---

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose
- (Opcional para execução local fora do Docker) Node.js 20+, Python 3.11+ e PostgreSQL 16 com extensão `vector`.
- Chave de API do Google Gemini (`GEMINI_API_KEY`) para síntese de linguagem natural.

> **Modo Fallback:** Caso a variável `GEMINI_API_KEY` não seja informada, o sistema opera normalmente retornando diretamente os serviços recuperados pela busca vetorial, sem interromper a execução.

---

## Configuração

1. Clone o repositório e acesse o diretório:
```bash
git clone https://github.com/Coelho-G-Dev/rag-servicos-publicos.git
cd rag-servicos-publicos
```

2. Crie o arquivo `.env` a partir do modelo:
```bash
cp .env.example .env
```

3. Ajuste as variáveis conforme seu ambiente:
```env
# Gateway
PORT=3000
NODE_ENV=development
AI_SERVICE_URL=http://ai-service:8000
INTERNAL_API_SECRET=super-secret-internal-key
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=100

# PostgreSQL
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_DB=rag_db
POSTGRES_PORT=5432

# AI Service
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL_NAME=gemini-1.5-flash
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
TOP_K_RESULTS=4
LOG_LEVEL=INFO
```

---

## Execução com Docker Compose

1. Inicie todos os contêineres (Banco, AI Service e Gateway):
```bash
docker-compose up -d --build
```

2. Execute a ingestão do dataset de serviços de São Luís:
```bash
docker-compose exec ai-service python scripts/ingest.py
```

O script lê o arquivo `servicos_seed.json`, gera os embeddings de 384 dimensões e popula a tabela `public_services` no PostgreSQL com indexação HNSW.

---

## Endpoints da API

### Gateway (`http://localhost:3000`)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/chat` | Consulta via pipeline RAG (busca vetorial + síntese LLM) |
| `GET` | `/api/v1/services` | Busca textual e filtros por categoria no banco relacional |
| `GET` | `/health` | Liveness check do Gateway |
| `GET` | `/ready` | Readiness check (valida conectividade com Postgres e AI Service) |
| `GET` | `/metrics` | Métricas de aplicação no formato Prometheus |
| `GET` | `/docs` | Documentação interativa via Swagger UI |
| `GET` | `/api-docs.json` | Especificação OpenAPI 3.0 em JSON |

### AI Service (`http://localhost:8000` - Interno)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/internal/rag/query` | Endpoint interno de execução do pipeline RAG |
| `GET` | `/health` | Verificação de integridade do AI Service |
| `GET` | `/metrics` | Métricas de processo e latência do pipeline RAG |
| `GET` | `/docs` | Documentação Swagger dos endpoints internos (requer `X-Internal-Secret`) |

---

## Exemplos de Uso

### 1. Consulta RAG (`POST /api/v1/chat`)

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Onde posso tomar vacina infantil ou de rotina próximo ao Centro?"}'
```

**Exemplo de Resposta:**
```json
{
  "answer": "Para vacinação no Centro de São Luís, você pode procurar o Centro de Saúde Dr. Paulo Ramos, localizado na Rua do Passeio, s/n - Centro, que oferece salas de vacina de rotina e atendimento básico de saúde.",
  "sources": [
    {
      "id": "sau-005",
      "nome": "Centro de Saúde Dr. Paulo Ramos",
      "categoria": "Saúde",
      "endereco": "Rua do Passeio, s/n - Centro, São Luís - MA",
      "similarity": 0.8712
    }
  ]
}
```

### 2. Consulta fora do domínio (Comportamento antialucinação)

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual o horário do metrô de São Paulo?"}'
```

**Resposta:**
```json
{
  "answer": "Desculpe, não encontrei informações sobre esse serviço em nossa base oficial de serviços públicos de São Luís.",
  "sources": []
}
```

### 3. Busca Relacional Direta (`GET /api/v1/services`)

Permite busca direta no banco relacional sem acionar o pipeline de inteligência artificial:

```bash
curl "http://localhost:3000/api/v1/services?category=Saúde&q=vinhais&limit=10"
```

### 4. Coleta de Métricas (`GET /metrics`)

```bash
curl http://localhost:3000/metrics
```

Métricas expostas incluem:
- `http_requests_total`: Total de requisições por rota, método e status code.
- `http_request_duration_seconds`: Histograma de latência HTTP.
- `chat_requests_total`: Total de consultas enviadas ao pipeline RAG.
- Métricas nativas de runtime do Node.js (uso de memória heap, event loop lag, GC).

---

## Testes Automatizados

### Gateway (Node.js / Jest)
Executa testes de integração das rotas HTTP, validação de payload, observabilidade e tratamento de erros:
```bash
cd gateway
npm test
```

### AI Service (Python / Pytest)
Executa testes unitários do pipeline RAG, gerador de respostas, formatador de contexto e validação do dataset:
```bash
cd ai-service
pytest -v -m "not integration"
```

Para executar o teste de integração direto contra o PostgreSQL com extensão `vector`:
```bash
pytest -m integration
```

---

## Deploy no Render

O repositório possui o manifesto [render.yaml](render.yaml) configurado para provisionamento automático (Blueprint):

1. Acesse o painel do [Render](https://dashboard.render.com/) e selecione **New +** > **Blueprint**.
2. Conecte o repositório deste projeto.
3. O Render identificará automaticamente os 3 recursos descritos no manifesto:
   - `rag-postgres`: Banco de dados PostgreSQL gerenciado com suporte a extensões.
   - `rag-ai-service`: Microsserviço Python em container Docker.
   - `rag-gateway`: Serviço web Node.js com build TypeScript e Swagger integrado.
4. Defina o valor da variável `GEMINI_API_KEY` na interface do Render.
5. Após o término da implantação, abra o console/shell do serviço `rag-ai-service` e execute o script de carga inicial.:
   ```bash
   python scripts/ingest.py
   ```

---

## Evoluções Técnicas Planejadas

- **Reranking com Cross-Encoder:** Inclusão do modelo `cross-encoder/ms-marco-MiniLM-L-6-v2` pós-recuperação vetorial para refinamento do ordenamento dos trechos antes do envio ao LLM.
- **Busca Híbrida (Hybrid Search):** Combinação de busca vetorial densa com busca textual esparsa (`tsvector` / `tsquery`) no PostgreSQL via Reciprocal Rank Fusion (RRF).
- **Cache Semântico:** Implementação de cache de perguntas frequentes baseado em similaridade vetorial prévia (Redis com RediSearch) para redução de latência e consumo de tokens.
- **Filtro Geoespacial:** Integração com a extensão PostGIS para ordenação e filtro por proximidade geográfica das unidades de atendimento.
