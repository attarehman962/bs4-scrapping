import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from security_scanner.scraping.job_scraper import (
    PythonJobBoardScraper,
    ScraperConfig,
)
from security_scanner.scraping.job_storage import save_jobs_to_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Python.org job listings and save them to CSV."
    )
    parser.add_argument(
        "--base-url",
        default="https://www.python.org/jobs/",
        help="Job board URL to scrape.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=2,
        help="Maximum number of result pages to scrape.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between page requests.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "scraped_jobs.csv",
        help="CSV file path for saved listings.",
    )
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Do not check robots.txt before scraping.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the job scraper and save results to CSV."""

    args = parse_args()
    config = ScraperConfig(
        base_url=args.base_url,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        user_agent="AttaSecurityScanner/0.1 (+portfolio project)",
        respect_robots=not args.ignore_robots,
    )

    scraper = PythonJobBoardScraper(config=config)
    result = scraper.scrape()

    new_rows = save_jobs_to_csv(result.listings, args.output)

    print(f"Pages scraped: {result.pages_scraped}")
    print(f"Listings found: {len(result.listings)}")
    print(f"New rows saved: {new_rows}")
    print(f"CSV path: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
