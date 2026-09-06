from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest
from app.api.routes.rag import get_rag_pipeline
from app.core.config import get_settings
from app.main import app
from app.rag.pipeline import RAGPipeline

client = TestClient(app)
settings = get_settings()


@pytest.fixture
def mock_pipeline():
    mock = MagicMock(spec=RAGPipeline)
    mock.process_query.return_value = {
        "answer": "O CRAS Coroadinho oferece serviços do CadÚnico.",
        "sources": [
            {
                "id": "soc-001",
                "nome": "CRAS Coroadinho",
                "categoria": "Assistência Social",
                "endereco": "Av. Amália Saldanha, 25 - Coroadinho",
                "similarity": 0.91,
            }
        ],
        "retrieved_chunks": [
            {
                "id": "soc-001",
                "nome": "CRAS Coroadinho",
                "categoria": "Assistência Social",
                "endereco": "Av. Amália Saldanha, 25 - Coroadinho",
                "descricao": "Inscrição e atualização do CadÚnico.",
                "similarity": 0.91,
            }
        ],
    }
    return mock


def test_internal_rag_query_unauthorized_missing_header():
    response = client.post(
        "/internal/rag/query",
        json={"message": "Onde atualizar o CadÚnico?"},
    )
    assert response.status_code == 401
    assert "X-Internal-Secret" in response.json()["detail"]


def test_internal_rag_query_unauthorized_invalid_header():
    response = client.post(
        "/internal/rag/query",
        headers={"X-Internal-Secret": "chave-errada"},
        json={"message": "Onde atualizar o CadÚnico?"},
    )
    assert response.status_code == 401


def test_internal_rag_query_success(mock_pipeline):
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline

    response = client.post(
        "/internal/rag/query",
        headers={"X-Internal-Secret": settings.INTERNAL_API_SECRET},
        json={"message": "Onde atualizar o CadÚnico?"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "O CRAS Coroadinho oferece serviços do CadÚnico."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["id"] == "soc-001"
    assert len(data["retrieved_chunks"]) == 1


def test_internal_rag_query_validation_error():
    response = client.post(
        "/internal/rag/query",
        headers={"X-Internal-Secret": settings.INTERNAL_API_SECRET},
        json={"message": ""},
    )
    assert response.status_code == 422


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "rag-ai-service"


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "rag_queries_total" in response.text
