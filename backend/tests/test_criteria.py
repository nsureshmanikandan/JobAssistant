from sqlmodel import SQLModel, create_engine, Session
from app.criteria import (
    build_criteria_text, build_queries, get_or_create_criteria, location_list, primary_location, title_list,
)
from app.db.models import SearchCriteria


def test_get_or_create_criteria_creates_default_row_once():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        first = get_or_create_criteria(session)
        second = get_or_create_criteria(session)
        assert first.id == second.id


def test_title_list_splits_and_trims():
    criteria = SearchCriteria(titles="GenAI Architect, Agentic AI Architect ,  ")
    assert title_list(criteria) == ["GenAI Architect", "Agentic AI Architect"]


def test_build_criteria_text_includes_all_fields():
    criteria = SearchCriteria(
        titles="GenAI Architect",
        location="Chennai",
        salary_min_lakhs=45,
        salary_max_lakhs=60,
        industry="MNC",
        min_company_size=5000,
        exclude_sponsorship=True,
    )
    text = build_criteria_text(criteria)
    assert "GenAI Architect" in text
    assert "Chennai" in text
    assert "45L-60L" in text
    assert "MNC" in text
    assert "5000" in text
    assert "sponsorship" in text.lower()


def test_build_criteria_text_omits_sponsorship_line_when_not_excluded():
    criteria = SearchCriteria(titles="GenAI Architect", exclude_sponsorship=False)
    text = build_criteria_text(criteria)
    assert "sponsorship" not in text.lower()


def test_build_queries_covers_every_title_and_site():
    criteria = SearchCriteria(titles="GenAI Architect,Agentic AI Architect", location="Chennai")
    queries = build_queries(criteria)
    assert len(queries) == 6  # 2 titles x 1 location x 3 sites
    assert any("linkedin.com/jobs" in q and "GenAI Architect" in q for q in queries)
    assert any("naukri.com" in q and "Agentic AI Architect" in q for q in queries)


def test_location_list_splits_and_trims():
    criteria = SearchCriteria(location="Chennai, Bangalore ,  ")
    assert location_list(criteria) == ["Chennai", "Bangalore"]


def test_primary_location_returns_first_entry():
    criteria = SearchCriteria(location="Bangalore,Chennai")
    assert primary_location(criteria) == "Bangalore"


def test_build_queries_covers_every_title_location_and_site():
    criteria = SearchCriteria(titles="GenAI Architect", location="Chennai,Bangalore")
    queries = build_queries(criteria)
    assert len(queries) == 6  # 1 title x 2 locations x 3 sites
    assert any("Chennai" in q for q in queries)
    assert any("Bangalore" in q for q in queries)


def test_build_criteria_text_includes_all_locations():
    criteria = SearchCriteria(titles="GenAI Architect", location="Chennai,Bangalore")
    text = build_criteria_text(criteria)
    assert "Chennai" in text
    assert "Bangalore" in text
