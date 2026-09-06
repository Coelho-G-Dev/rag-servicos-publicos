from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.observability.logger import logger

_model_instance: Optional[SentenceTransformer] = None


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or get_settings().EMBEDDING_MODEL_NAME

    def _get_model(self) -> SentenceTransformer:
        global _model_instance
        if _model_instance is None:
            logger.info("loading_embedding_model", model_name=self.model_name)
            _model_instance = SentenceTransformer(self.model_name)
        return _model_instance

    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding vetorial normalizado de 384 dimensões localmente."""
        model = self._get_model()
        cleaned_text = text.strip()
        if not cleaned_text:
            cleaned_text = "vazio"
        vector = model.encode(cleaned_text, normalize_embeddings=True)
        return vector.tolist()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
