from typing import Optional
from llama_index.core.llms import LLM
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from backend.config import get_settings

class LLMFactory:
    """
    Factory class to create LLM and Embedding instances based on configuration.
    Supports: Gemini, OpenAI, Perplexity (via OpenAI compatible interface), Mock.
    """
    
    @staticmethod
    def get_llm(model_name: Optional[str] = None, temperature: float = 0.1) -> LLM:
        settings = get_settings()
        provider = settings.LLM_PROVIDER.lower()
        model = model_name or settings.LLM_MODEL
        
        if provider == "gemini":
            try:
                from llama_index.llms.gemini import Gemini
            except ImportError:
                raise ImportError("llama-index-llms-gemini is required for Gemini provider")
            
            return Gemini(
                model=model,
                api_key=settings.GOOGLE_API_KEY,
                temperature=temperature
            )
            
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
            
        elif provider == "perplexity":
            if not settings.PERPLEXITY_API_KEY:
                raise ValueError("PERPLEXITY_API_KEY is required for Perplexity provider")
            try:
                from llama_index.llms.openai import OpenAI
            except ImportError:
                raise ImportError("llama-index-llms-openai is required for Perplexity provider")
                
            return OpenAI(
                model=model,
                api_key=settings.PERPLEXITY_API_KEY,
                api_base="https://api.perplexity.ai",
                temperature=temperature
            )
        
        elif provider == "mock":
            from llama_index.core.llms import MockLLM
            return MockLLM()
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def get_embedding_model() -> BaseEmbedding:
        settings = get_settings()
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "gemini":
            try:
                from llama_index.embeddings.gemini import GeminiEmbedding
            except ImportError:
                raise ImportError("llama-index-embeddings-gemini is required for Gemini provider")
                
            return GeminiEmbedding(
                model_name="models/embedding-001",
                api_key=settings.GOOGLE_API_KEY
            )
            
        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            try:
                from llama_index.embeddings.openai import OpenAIEmbedding
            except ImportError:
                raise ImportError("llama-index-embeddings-openai is required for OpenAI provider")
                
            return OpenAIEmbedding(
                api_key=settings.OPENAI_API_KEY
            )
            
        # Perplexity does not offer embeddings usually, fallback to Gemini or OpenAI?
        # For now, default to Gemini if using Perplexity unless OpenAI key is set.
        elif provider == "perplexity":
             # Fallback strategy
             if settings.GOOGLE_API_KEY:
                 try:
                    from llama_index.embeddings.gemini import GeminiEmbedding
                    return GeminiEmbedding(model_name="models/embedding-001", api_key=settings.GOOGLE_API_KEY)
                 except ImportError:
                    pass

             if settings.OPENAI_API_KEY:
                 try:
                    from llama_index.embeddings.openai import OpenAIEmbedding
                    return OpenAIEmbedding(api_key=settings.OPENAI_API_KEY)
                 except ImportError:
                    pass
             
             raise ValueError("Perplexity provider needs GOOGLE_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI) for embeddings fallback, and the respective packages installed.")
                  
        elif provider == "mock":
            from llama_index.core.embeddings import MockEmbedding
            return MockEmbedding(embed_dim=768)
            
        else:
             # Default fallback to Gemini
             try:
                from llama_index.embeddings.gemini import GeminiEmbedding
                return GeminiEmbedding(model_name="models/embedding-001", api_key=settings.GOOGLE_API_KEY)
             except ImportError:
                raise ImportError("llama-index-embeddings-gemini is required for default provider")
