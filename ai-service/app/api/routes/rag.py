from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.rag.pipeline import RAGPipeline, get_rag_pipeline

router = APIRouter(prefix="/internal/rag", tags=["RAG Interno"])


class RAGQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pergunta ou solicitação do usuário")


class SourceItem(BaseModel):
    id: str
    nome: str
    categoria: str
    endereco: str
    similarity: Optional[float] = 0.0


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    retrieved_chunks: List[Dict[str, Any]]


def verify_internal_secret(
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret")
):
    settings = get_settings()
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado: Header X-Internal-Secret inválido ou ausente."
        )


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Executa consulta vetorial e geração de resposta RAG"
)
def query_rag(
    request: RAGQueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    try:
        result = pipeline.process_query(request.message)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar consulta RAG: {str(e)}"
        )
