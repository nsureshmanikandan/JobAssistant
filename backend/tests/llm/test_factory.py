import pytest
from app.config import settings
from app.llm.factory import get_llm_provider


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "not_a_real_provider")
    get_llm_provider.cache_clear()
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_llm_provider()


def test_azure_openai_provider_selected(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "azure_openai")
    get_llm_provider.cache_clear()
    provider = get_llm_provider()
    assert provider.name == "azure_openai"
