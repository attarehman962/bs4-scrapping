import csv
from pathlib import Path

from security_scanner.scraping.job_models import JobListing


CSV_FIELDS = [
    "title",
    "company_name",
    "location",
    "date_posted",
    "job_url",
    "source",
    "salary",
]


def load_existing_urls(csv_path: Path) -> set[str]:
    """Load existing job URLs from a CSV file for deduplication."""

    if not csv_path.exists():
        return set()

    existing_urls: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            job_url = row.get("job_url")
            if job_url:
                existing_urls.add(job_url)

    return existing_urls


def save_jobs_to_csv(listings: list[JobListing], csv_path: Path) -> int:
    """Save unique job listings to CSV and return number of new rows."""

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    seen_urls = load_existing_urls(csv_path)
    new_listings: list[JobListing] = []

    for listing in listings:
        if listing.job_url in seen_urls:
            continue

        seen_urls.add(listing.job_url)
        new_listings.append(listing)

    file_exists = csv_path.exists()

    with csv_path.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        for listing in new_listings:
            writer.writerow(
                {
                    "title": listing.title,
                    "company_name": listing.company_name or "",
                    "location": listing.location or "",
                    "date_posted": listing.date_posted or "",
                    "job_url": listing.job_url,
                    "source": listing.source,
                    "salary": listing.salary or "",
                }
            )

    return len(new_listings)
