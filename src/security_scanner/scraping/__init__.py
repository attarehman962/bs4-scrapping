"""Public API for job scraping utilities."""

from security_scanner.scraping.job_models import JobListing, ScrapeResult
from security_scanner.scraping.job_parser import parse_python_job_board
from security_scanner.scraping.job_scraper import (
    PythonJobBoardScraper,
    RobotsPolicy,
    ScraperConfig,
)
from security_scanner.scraping.job_storage import (
    load_existing_urls,
    save_jobs_to_csv,
)

__all__ = [
    "JobListing",
    "PythonJobBoardScraper",
    "RobotsPolicy",
    "ScrapeResult",
    "ScraperConfig",
    "load_existing_urls",
    "parse_python_job_board",
    "save_jobs_to_csv",
]
