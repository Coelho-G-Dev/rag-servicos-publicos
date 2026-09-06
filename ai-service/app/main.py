from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.routes.rag import router as rag_router
from app.core.config import get_settings
from app.db.postgres import close_pool, init_db_schema
from app.observability.health import get_health_status
from app.observability.logger import logger, setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logger(settings.LOG_LEVEL)
    logger.info("ai_service_startup", env=settings.ENVIRONMENT)
    try:
        init_db_schema()
    except Exception as e:
        logger.warning("db_init_warning", error=str(e))
    yield
    logger.info("ai_service_shutdown")
    close_pool()


settings = get_settings()
app = FastAPI(
    title="RAG Serviços Públicos - AI Service",
    description="Microsserviço interno de busca vetorial e geração de respostas com Gemini",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(rag_router)


from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="RAG Serviços Públicos - AI Service (Interno)",
        version="1.0.0",
        description="Microsserviço interno de busca vetorial com pgvector e geração estrita com Google Gemini.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "InternalSecretAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Internal-Secret",
            "description": "Segredo compartilhado configurado na variável INTERNAL_API_SECRET."
        }
    }
    openapi_schema["security"] = [{"InternalSecretAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/health", tags=["Observabilidade"])
def health():
    return get_health_status()
