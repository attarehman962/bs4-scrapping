from pathlib import Path

import httpx
import pytest

from security_scanner.scraping.job_models import JobListing
from security_scanner.scraping.job_parser import parse_python_job_board
from security_scanner.scraping.job_scraper import (
    PythonJobBoardScraper,
    ScraperConfig,
)
from security_scanner.scraping.job_storage import save_jobs_to_csv


PAGE_ONE_HTML = """
<ol class="list-recent-jobs">
  <li>
    <h2><a href="/jobs/1/">Python Backend Developer</a></h2>
    <span class="listing-company-name">ABC Software</span>
    <span class="listing-location">Lahore, Pakistan</span>
    <span class="listing-posted">Posted: 12 June 2026</span>
    <span class="listing-salary">PKR 250,000 - 400,000</span>
  </li>
</ol>
"""

PAGE_TWO_HTML = """
<ol class="list-recent-jobs">
  <li>
    <h2><a href="/jobs/2/">Security Automation Engineer</a></h2>
    <span class="listing-company-name">SecureTech</span>
    <span class="listing-location">Remote</span>
    <span class="listing-posted">Posted: 11 June 2026</span>
  </li>
</ol>
"""

EMPTY_PAGE_HTML = """
<ol class="list-recent-jobs"></ol>
"""

MISSING_FIELDS_HTML = """
<ol class="list-recent-jobs">
  <li>
    <h2><a href="/jobs/3/">Junior Python Developer</a></h2>
  </li>
</ol>
"""


def test_parse_python_job_board_extracts_required_fields() -> None:
    """Parser should extract title, company, location, date, and absolute URL."""

    jobs = parse_python_job_board(
        html=PAGE_ONE_HTML,
        base_url="https://www.python.org/jobs/",
    )

    assert len(jobs) == 1
    assert jobs[0].title == "Python Backend Developer"
    assert jobs[0].company_name == "ABC Software"
    assert jobs[0].location == "Lahore, Pakistan"
    assert jobs[0].date_posted == "12 June 2026"
    assert jobs[0].job_url == "https://www.python.org/jobs/1/"
    assert jobs[0].salary == "PKR 250,000 - 400,000"


def test_parse_python_job_board_handles_missing_fields() -> None:
    """Parser should not crash when optional fields are missing."""

    jobs = parse_python_job_board(
        html=MISSING_FIELDS_HTML,
        base_url="https://www.python.org/jobs/",
    )

    assert len(jobs) == 1
    assert jobs[0].title == "Junior Python Developer"
    assert jobs[0].company_name is None
    assert jobs[0].location is None
    assert jobs[0].date_posted is None


def test_save_jobs_to_csv_writes_rows(tmp_path: Path) -> None:
    """CSV writer should create a file and write job rows."""

    csv_path = tmp_path / "jobs.csv"
    jobs = [
        JobListing(
            title="Python Developer",
            company_name="ABC",
            location="Remote",
            date_posted="12 June 2026",
            job_url="https://example.com/jobs/1",
        )
    ]

    rows_written = save_jobs_to_csv(jobs, csv_path)

    assert rows_written == 1
    assert csv_path.exists()
    assert "Python Developer" in csv_path.read_text(encoding="utf-8")


def test_save_jobs_to_csv_deduplicates_existing_urls(
    tmp_path: Path,
) -> None:
    """CSV writer should not append the same job URL twice."""

    csv_path = tmp_path / "jobs.csv"
    job = JobListing(
        title="Python Developer",
        company_name="ABC",
        location="Remote",
        date_posted="12 June 2026",
        job_url="https://example.com/jobs/1",
    )

    first_count = save_jobs_to_csv([job], csv_path)
    second_count = save_jobs_to_csv([job], csv_path)

    assert first_count == 1
    assert second_count == 0


def test_save_jobs_to_csv_deduplicates_urls_in_same_batch(
    tmp_path: Path,
) -> None:
    """CSV writer should not write duplicate URLs from one input batch."""

    csv_path = tmp_path / "jobs.csv"
    job = JobListing(
        title="Python Developer",
        company_name="ABC",
        location="Remote",
        date_posted="12 June 2026",
        job_url="https://example.com/jobs/1",
        salary="PKR 250,000 - 400,000",
    )

    rows_written = save_jobs_to_csv([job, job], csv_path)

    csv_lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert rows_written == 1
    assert len(csv_lines) == 2


def test_save_jobs_to_csv_writes_header_to_empty_file(
    tmp_path: Path,
) -> None:
    """CSV writer should add a header when the target file is empty."""

    csv_path = tmp_path / "jobs.csv"
    csv_path.touch()
    job = JobListing(
        title="Python Developer",
        company_name="ABC",
        location="Remote",
        date_posted="12 June 2026",
        job_url="https://example.com/jobs/1",
    )

    rows_written = save_jobs_to_csv([job], csv_path)

    csv_lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert rows_written == 1
    assert csv_lines[0].startswith("title,company_name,location")


def test_scraping_package_exports_public_api() -> None:
    """Package init should expose the main public classes and functions."""

    from security_scanner.scraping import JobListing as ExportedJobListing
    from security_scanner.scraping import PythonJobBoardScraper as ExportedScraper
    from security_scanner.scraping import parse_python_job_board as exported_parse

    assert ExportedJobListing is JobListing
    assert ExportedScraper is PythonJobBoardScraper
    assert exported_parse is parse_python_job_board


def test_scraper_handles_pagination_without_real_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scraper should fetch multiple pages using mocked HTTP responses."""

    def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("time.sleep", fake_sleep)

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)

        if url.endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nAllow: /")

        if url == "https://www.python.org/jobs/":
            return httpx.Response(200, text=PAGE_ONE_HTML)

        if url == "https://www.python.org/jobs/?page=2":
            return httpx.Response(200, text=PAGE_TWO_HTML)

        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(handler)

    scraper = PythonJobBoardScraper(
        config=ScraperConfig(
            base_url="https://www.python.org/jobs/",
            max_pages=2,
            delay_seconds=0.01,
            respect_robots=True,
        ),
        transport=transport,
    )

    result = scraper.scrape()

    assert result.pages_scraped == 2
    assert len(result.listings) == 2
    assert result.listings[0].title == "Python Backend Developer"
    assert result.listings[1].title == "Security Automation Engineer"


def test_scraper_stops_when_page_has_no_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scraper should stop pagination when a page returns no listings."""

    monkeypatch.setattr("time.sleep", lambda seconds: None)

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)

        if url.endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nAllow: /")

        if url == "https://www.python.org/jobs/":
            return httpx.Response(200, text=PAGE_ONE_HTML)

        if url == "https://www.python.org/jobs/?page=2":
            return httpx.Response(200, text=EMPTY_PAGE_HTML)

        return httpx.Response(404, text="Not Found")

    scraper = PythonJobBoardScraper(
        config=ScraperConfig(
            base_url="https://www.python.org/jobs/",
            max_pages=5,
            delay_seconds=0.01,
            respect_robots=True,
        ),
        transport=httpx.MockTransport(handler),
    )

    result = scraper.scrape()

    assert result.pages_scraped == 1
    assert len(result.listings) == 1


def test_scraper_blocks_disallowed_robots_path() -> None:
    """Scraper should refuse to scrape when robots.txt disallows the path."""

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(
                200,
                text="User-agent: *\nDisallow: /jobs/",
            )

        return httpx.Response(200, text=PAGE_ONE_HTML)

    scraper = PythonJobBoardScraper(
        config=ScraperConfig(
            base_url="https://www.python.org/jobs/",
            max_pages=1,
            respect_robots=True,
        ),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(PermissionError):
        scraper.scrape()
