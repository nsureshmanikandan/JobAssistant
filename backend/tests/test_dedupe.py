from app.services.dedupe import job_dedupe_key


def test_dedupe_key_is_case_and_whitespace_insensitive():
    key1 = job_dedupe_key(company="Acme Corp", title="GenAI Architect", location="Chennai")
    key2 = job_dedupe_key(company="  ACME CORP ", title="genai architect", location="chennai ")
    assert key1 == key2


def test_dedupe_key_differs_for_different_jobs():
    key1 = job_dedupe_key(company="Acme Corp", title="GenAI Architect", location="Chennai")
    key2 = job_dedupe_key(company="Acme Corp", title="Data Scientist", location="Chennai")
    assert key1 != key2
