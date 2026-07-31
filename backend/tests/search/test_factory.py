import pytest
from app.config import settings
from app.search.factory import get_search_provider


def test_unknown_search_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "search_provider", "not_real")
    get_search_provider.cache_clear()
    with pytest.raises(ValueError, match="Unknown SEARCH_PROVIDER"):
        get_search_provider()
