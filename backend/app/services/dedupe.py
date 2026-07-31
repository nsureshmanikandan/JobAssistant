import re


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def job_dedupe_key(company: str, title: str, location: str) -> str:
    return f"{_normalize(company)}|{_normalize(title)}|{_normalize(location)}"
