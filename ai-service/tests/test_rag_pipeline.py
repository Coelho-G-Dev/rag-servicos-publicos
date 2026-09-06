from unittest.mock import MagicMock
import pytest
from app.rag.embeddings import EmbeddingService
from app.rag.generator import AnswerGenerator
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import VectorRetriever


@pytest.fixture
def mock_embedding_service():
    mock = MagicMock(spec=EmbeddingService)
    mock.generate_embedding.return_value = [0.05] * 384
    return mock


@pytest.fixture
def mock_retriever():
    mock = MagicMock(spec=VectorRetriever)
    mock.search.return_value = [
        {
            "id": "sau-002",
            "nome": "UPA Vinhais",
            "categoria": "Saúde",
            "descricao": "Unidade de Pronto Atendimento 24h para emergências.",
            "endereco": "Av. Jerônimo de Albuquerque, s/n - Vinhais",
            "similarity": 0.88,
        },
        {
            "id": "sau-001",
            "nome": "Unidade Mista do Itaqui-Bacanga",
            "categoria": "Saúde",
            "descricao": "Atendimento ambulatorial e urgência básica.",
            "endereco": "Av. dos Portugueses, s/n - Vila Bacanga",
            "similarity": 0.82,
        },
    ]
    return mock


@pytest.fixture
def mock_generator():
    mock = MagicMock(spec=AnswerGenerator)
    mock.generate_answer.return_value = (
        "Para emergências médicas em São Luís, você pode se dirigir à UPA Vinhais, "
        "localizada na Av. Jerônimo de Albuquerque, s/n - Vinhais, com atendimento 24h."
    )
    return mock


def test_rag_pipeline_orchestration(mock_embedding_service, mock_retriever, mock_generator):
    pipeline = RAGPipeline(
        embedding_service=mock_embedding_service,
        retriever=mock_retriever,
        generator=mock_generator,
    )

    query = "Onde encontrar atendimento de urgência 24h?"
    result = pipeline.process_query(query)

    mock_embedding_service.generate_embedding.assert_called_once_with(query)
    mock_retriever.search.assert_called_once_with([0.05] * 384)
    mock_generator.generate_answer.assert_called_once_with(query, mock_retriever.search.return_value)

    assert "answer" in result
    assert "sources" in result
    assert "retrieved_chunks" in result
    assert len(result["sources"]) == 2
    assert result["sources"][0]["id"] == "sau-002"
    assert result["sources"][0]["nome"] == "UPA Vinhais"
    assert result["sources"][1]["id"] == "sau-001"


def test_generator_format_context():
    gen = AnswerGenerator(api_key="")
    chunks = [
        {
            "id": "cid-001",
            "nome": "Viva Procon Shopping da Ilha",
            "categoria": "Cidadania",
            "endereco": "Av. Daniel de La Touche",
            "descricao": "Emissão de documentos.",
        }
    ]
    formatted = gen.format_context(chunks)
    assert "Viva Procon Shopping da Ilha" in formatted
    assert "Cidadania" in formatted
    assert "cid-001" in formatted


def test_generator_empty_context():
    gen = AnswerGenerator(api_key="")
    ans = gen.generate_answer("Pergunta qualquer", [])
    assert "não encontrei informações" in ans.lower()
