import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from security_scanner.scraping.job_models import JobListing


POSTED_DATE_PATTERN = re.compile(
    r"Posted:\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})"
)


def clean_text(value: str | None) -> str | None:
    """Normalize whitespace and return None for empty text."""

    if value is None:
        return None

    cleaned_value = " ".join(value.split())
    return cleaned_value if cleaned_value else None


def select_text(node: Tag, selectors: list[str]) -> str | None:
    """Return cleaned text from the first matching selector."""

    for selector in selectors:
        selected_node = node.select_one(selector)
        if selected_node is not None:
            text = clean_text(selected_node.get_text(" ", strip=True))
            if text:
                return text

    return None


def extract_posted_date(text: str) -> str | None:
    """Extract a posted date from combined listing text."""

    match = POSTED_DATE_PATTERN.search(text)
    if match is None:
        return None

    return match.group(1)


def parse_python_job_board(html: str, base_url: str) -> list[JobListing]:
    """Parse Python.org-style job board HTML into structured listings."""

    soup = BeautifulSoup(html, "html.parser")
    job_nodes = soup.select("ol.list-recent-jobs > li")

    if not job_nodes:
        job_nodes = soup.select("[data-testid='job-card']")

    listings: list[JobListing] = []

    for job_node in job_nodes:
        title_link = job_node.select_one("h2 a, a.job-title")

        if title_link is None:
            continue

        title = clean_text(title_link.get_text(" ", strip=True))
        relative_url = title_link.get("href")

        if title is None or not isinstance(relative_url, str):
            continue

        job_url = urljoin(base_url, relative_url)
        combined_text = clean_text(job_node.get_text(" ", strip=True)) or ""

        location = select_text(
            job_node,
            [
                ".listing-location",
                ".job-location",
                ".location",
                "[data-testid='job-location']",
            ],
        )

        company_name = select_text(
            job_node,
            [
                ".listing-company-name",
                ".company-name",
                ".company",
                "[data-testid='company-name']",
            ],
        )

        if company_name and location:
            company_name = clean_text(company_name.replace(location, ""))

        date_posted = select_text(
            job_node,
            [
                ".listing-posted",
                ".posted-date",
                ".date-posted",
                "[data-testid='posted-date']",
            ],
        )

        if date_posted and "Posted:" in date_posted:
            date_posted = extract_posted_date(date_posted)

        if date_posted is None:
            date_posted = extract_posted_date(combined_text)

        salary = select_text(
            job_node,
            [
                ".listing-salary",
                ".salary",
                ".compensation",
                "[data-testid='salary']",
            ],
        )

        listings.append(
            JobListing(
                title=title,
                company_name=company_name,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                salary=salary,
                source="python.org",
            )
        )

    return listings
