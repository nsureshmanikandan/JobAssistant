from sqlmodel import Session, select
from app.db.models import SearchCriteria

SEARCH_SITES = ["linkedin.com/jobs", "naukri.com", "indeed.com"]


def get_or_create_criteria(session: Session) -> SearchCriteria:
    criteria = session.exec(select(SearchCriteria)).first()
    if criteria is None:
        criteria = SearchCriteria()
        session.add(criteria)
        session.commit()
        session.refresh(criteria)
    return criteria


def title_list(criteria: SearchCriteria) -> list[str]:
    return [t.strip() for t in criteria.titles.split(",") if t.strip()]


def location_list(criteria: SearchCriteria) -> list[str]:
    return [loc.strip() for loc in criteria.location.split(",") if loc.strip()]


def primary_location(criteria: SearchCriteria) -> str:
    locations = location_list(criteria)
    return locations[0] if locations else "Chennai"


def build_criteria_text(criteria: SearchCriteria) -> str:
    parts = [
        f"Titles: {', '.join(title_list(criteria))}.",
        f"Location: {', '.join(location_list(criteria))}, India" + (", FTE only." if criteria.fte_only else "."),
        f"Salary: INR {criteria.salary_min_lakhs}L-{criteria.salary_max_lakhs}L.",
        f"Industry: {criteria.industry} only, company size >= {criteria.min_company_size} employees.",
    ]
    if criteria.exclude_sponsorship:
        parts.append("Skip roles requiring visa/work sponsorship.")
    return " ".join(parts)


def build_queries(criteria: SearchCriteria) -> list[str]:
    return [
        f'site:{site} "{title}" {location}'
        for title in title_list(criteria)
        for location in location_list(criteria)
        for site in SEARCH_SITES
    ]
