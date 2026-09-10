from typing import Any, Dict, List, Optional
import google.generativeai as genai
from app.core.config import get_settings
from app.observability.logger import logger
from app.observability.metrics import rag_llm_errors_total

SYSTEM_PROMPT = """Você é o assistente virtual oficial de informações sobre serviços públicos da cidade de São Luís/MA.
Sua missão é responder à dúvida do cidadão de forma clara, empática e estritamente precisa.

REGRAS OBRIGATÓRIAS:
1. Responda ÚNICA e EXCLUSIVAMENTE com base nos serviços públicos informados no CONTEXTO RECUPERADO abaixo.
2. NÃO INVENTE, NÃO SUPONHA E NÃO ALUCINE locais, horários, telefones ou informações que não estejam expressamente descritos no contexto.
3. Se o contexto não contiver informações suficientes para responder à pergunta, responda exatamente:
   "Desculpe, não encontrei informações sobre esse serviço em nossa base oficial de serviços públicos de São Luís."
4. Sempre que citar um serviço ou órgão público, mencione seu nome e seu endereço completo conforme o contexto.
5. Responda em Português do Brasil de forma concisa e organizada."""


class AnswerGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self._model = None
        if self.api_key and self.api_key.strip() and self.api_key != "sua_chave_gemini_aqui":
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Formata os trechos recuperados em texto legível para o LLM."""
        if not chunks:
            return "Nenhum serviço relevante foi encontrado na base de dados."

        lines = []
        for i, c in enumerate(chunks, 1):
            lines.append(
                f"[Serviço {i}]\n"
                f"- ID: {c.get('id', '')}\n"
                f"- Nome: {c.get('nome', '')}\n"
                f"- Categoria: {c.get('categoria', '')}\n"
                f"- Endereço: {c.get('endereco', '')}\n"
                f"- Descrição: {c.get('descricao', '')}\n"
            )
        return "\n".join(lines)

    def generate_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Gera a resposta final fundamentada nos dados reais recuperados.
        Se GEMINI_API_KEY não estiver configurada, retorna uma resposta estruturada informativa.
        """
        context_text = self.format_context(chunks)

        if not chunks:
            return (
                "Desculpe, não encontrei informações sobre esse serviço em nossa base "
                "oficial de serviços públicos de São Luís."
            )

        if not self._model:
            logger.info("gemini_api_key_missing_using_fallback_grounded_summary")
            summary_services = [f"• **{c['nome']}** ({c['categoria']}) - {c['endereco']}: {c['descricao']}" for c in chunks]
            return (
                f"[Aviso: Chave GEMINI_API_KEY não configurada no .env. Apresentando dados recuperados diretamente]\n\n"
                f"Encontrei os seguintes serviços públicos relacionados em São Luís:\n\n"
                + "\n\n".join(summary_services)
            )

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- CONTEXTO RECUPERADO DA BASE OFICIAL ---\n"
            f"{context_text}\n"
            f"-------------------------------------------\n\n"
            f"Pergunta do cidadão: {query}\n\n"
            f"Resposta fundamentada:"
        )

        models_to_try = [self.model_name, "gemini-2.5-flash", "gemini-flash-latest", "gemini-pro-latest"]
        unique_models = list(dict.fromkeys(models_to_try))

        last_error = None
        for m_name in unique_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning("gemini_model_attempt_failed", model=m_name, error=str(e))
                last_error = e

        logger.error("all_gemini_models_failed_using_grounded_fallback", error=str(last_error))
        if last_error:
            rag_llm_errors_total.labels(error_type=type(last_error).__name__).inc()

        summary_services = [f"• **{c['nome']}** ({c['categoria']}) - {c['endereco']}: {c['descricao']}" for c in chunks]
        return (
            f"Encontrei as seguintes opções oficiais em nossa base de serviços de São Luís:\n\n"
            + "\n\n".join(summary_services)
        )


def get_generator() -> AnswerGenerator:
    return AnswerGenerator()
