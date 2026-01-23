from typing import Optional
from llama_index.core.llms import LLM
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory class to create LLM and Embedding instances based on configuration.
    Supports: Gemini, OpenAI, Perplexity, Anthropic (Claude), Mock.
    """
    
    @staticmethod
    def get_llm(model_name: Optional[str] = None, temperature: float = 0.1) -> LLM:
        settings = get_settings()
        provider = settings.LLM_PROVIDER.lower()
        model = model_name or settings.LLM_MODEL
        
        # 1. Google Gemini
        if provider == "gemini":
            try:
                from llama_index.llms.gemini import Gemini
            except ImportError:
                raise ImportError("llama-index-llms-gemini is required for Gemini provider. pip install llama-index-llms-gemini")
            
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Gemini provider")
            
            return Gemini(
                model=model,
                api_key=settings.GOOGLE_API_KEY,
                temperature=temperature
            )
            
        # 2. OpenAI
        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            try:
                from llama_index.llms.openai import OpenAI
            except ImportError:
                raise ImportError("llama-index-llms-openai is required for OpenAI provider")
                
            return OpenAI(
                model=model,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
        
        # 3. Perplexity AI (via OpenAI-Like Interface)
        elif provider == "perplexity":
            if not settings.PERPLEXITY_API_KEY:
                raise ValueError("PERPLEXITY_API_KEY is required for Perplexity provider")
            try:
                from llama_index.llms.openai_like import OpenAILike
            except ImportError:
                raise ImportError("llama-index-llms-openai-like is required for Perplexity provider")
            
            # Perplexity models: llama-3.1-sonar-large-128k-online, etc.
            return OpenAILike(
                model=model,
                api_key=settings.PERPLEXITY_API_KEY,
                api_base="https://api.perplexity.ai",
                temperature=temperature,
                is_chat_model=True
            )
            
        # 4. Anthropic (Claude)
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            try:
                from llama_index.llms.anthropic import Anthropic
            except ImportError:
                raise ImportError("llama-index-llms-anthropic is required for Anthropic provider")
                
            return Anthropic(
                model=model,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=temperature
            )
        
        # 5. Mock (Testing)
        elif provider == "mock":
            logger.warning("⚠️ Using Mock LLM Provider")
            from llama_index.core.llms import MockLLM
            return MockLLM()
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def get_embedding_model() -> BaseEmbedding:
        settings = get_settings()
        provider = settings.LLM_PROVIDER.lower()
        
        # 1. Gemini (Native)
        if provider == "gemini":
            return LLMFactory._get_gemini_embedding(settings)
            
        # 2. OpenAI (Native)
        elif provider == "openai":
            return LLMFactory._get_openai_embedding(settings)
            
        # 3. Fallback / Perplexity / Anthropic -> USE LOCAL HuggingFace (Decoupled)
        try:
            # Prefer Local HuggingFace to avoid Rate Limits and enable offline capability
            # BAAI/bge-small-en-v1.5 is SOTA for small models, fast on CPU (~133MB)
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            return HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except ImportError:
            logger.warning("llama-index-embeddings-huggingface not found. Falling back to API.")
        except Exception as e:
            logger.warning(f"Could not load HuggingFaceEmbedding: {e}. Falling back to Gemini.")

        # 4. Final Fallback to Gemini if native key exists
        if settings.GOOGLE_API_KEY:
            return LLMFactory._get_gemini_embedding(settings)

        # 5. Fallback to OpenAI
        if settings.OPENAI_API_KEY:
            return LLMFactory._get_openai_embedding(settings)

        # 6. Mock
        if provider == "mock":
            from llama_index.core.embeddings import MockEmbedding
            return MockEmbedding(embed_dim=768)
            
        raise ValueError("Could not instantiate any embedding model. Please install llama-index-embeddings-huggingface or set GOOGLE_API_KEY.")

    @staticmethod
    def _get_gemini_embedding(settings) -> BaseEmbedding:
        try:
            from llama_index.embeddings.gemini import GeminiEmbedding
        except ImportError:
            raise ImportError("llama-index-embeddings-gemini is required")
        
        if not settings.GOOGLE_API_KEY:
             raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings")
             
        return GeminiEmbedding(
            model_name="models/embedding-001",
            api_key=settings.GOOGLE_API_KEY
        )

    @staticmethod
    def _get_openai_embedding(settings) -> BaseEmbedding:
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding
        except ImportError:
            raise ImportError("llama-index-embeddings-openai is required")
            
        if not settings.OPENAI_API_KEY:
             raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
             
        return OpenAIEmbedding(
            api_key=settings.OPENAI_API_KEY
        )
