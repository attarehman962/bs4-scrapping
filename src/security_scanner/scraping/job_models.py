from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class JobListing:
    """Represents one job listing extracted from a job board."""

    title: str
    company_name: str | None
    location: str | None
    date_posted: str | None
    job_url: str
    salary: str | None = None
    source: str = "python.org"


@dataclass(frozen=True, slots=True)
class ScrapeResult:
    """Represents the result of one scraping run."""

    source_url: str
    listings: list[JobListing]
    pages_scraped: int
    scraped_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )