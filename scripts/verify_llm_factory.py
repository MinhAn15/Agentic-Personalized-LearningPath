
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import Settings, get_settings
from backend.core.llm_factory import LLMFactory

class TestLLMFactory(unittest.TestCase):
    
    def setUp(self):
        # Reset lru_cache of get_settings to ensure fresh config
        get_settings.cache_clear()

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "gemini", 
        "GOOGLE_API_KEY": "fake_gemini_key",
        "LLM_MODEL": "models/gemini-pro"
    })
    def test_gemini_factory(self):
        print("\nTesting Gemini Factory...")
        with patch("llama_index.llms.gemini.Gemini") as MockGemini:
            llm = LLMFactory.get_llm()
            MockGemini.assert_called()
            print("[OK] Gemini instatiated")

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "openai", 
        "OPENAI_API_KEY": "fake_openai_key",
        "LLM_MODEL": "gpt-4o"
    })
    def test_openai_factory(self):
        print("\nTesting OpenAI Factory...")
        with patch("llama_index.llms.openai.OpenAI") as MockOpenAI:
            llm = LLMFactory.get_llm()
            MockOpenAI.assert_called_with(
                model="gpt-4o",
                api_key="fake_openai_key",
                temperature=0.1
            )
            print("[OK] OpenAI instatiated")

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "perplexity", 
        "PERPLEXITY_API_KEY": "fake_pplx_key",
        "LLM_MODEL": "sonar-medium"
    })
    def test_perplexity_factory(self):
        print("\nTesting Perplexity Factory...")
        # Ensure imports
        try:
             import llama_index.llms.openai_like
        except ImportError:
            pass

        with patch("llama_index.llms.openai_like.OpenAILike") as MockOpenAILike:
            llm = LLMFactory.get_llm()
            MockOpenAILike.assert_called_with(
                model="sonar-medium",
                api_key="fake_pplx_key",
                api_base="https://api.perplexity.ai",
                temperature=0.1,
                is_chat_model=True
            )
            print("[OK] Perplexity (via OpenAILike) instatiated")

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "anthropic", 
        "ANTHROPIC_API_KEY": "fake_claude_key",
        "LLM_MODEL": "claude-3-opus"
    })
    def test_anthropic_factory(self):
        print("\nTesting Anthropic Factory...")
        # Ensure module is imported so patch can find it
        try:
            import llama_index.llms.anthropic
        except ImportError:
            pass # Mock might handle it, or it will fail inside if not installed
            
        with patch("llama_index.llms.anthropic.Anthropic") as MockAnthropic:
            llm = LLMFactory.get_llm()
            MockAnthropic.assert_called_with(
                model="claude-3-opus",
                api_key="fake_claude_key",
                temperature=0.1
            )
            print("[OK] Anthropic instatiated")

if __name__ == "__main__":
    unittest.main()
