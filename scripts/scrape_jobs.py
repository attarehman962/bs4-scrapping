from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from security_scanner.scraping.job_parser import parse_python_job_board


DEFAULT_BASE_URL = "https://www.python.org/jobs/"

SAMPLE_HTML = """
<ol class="list-recent-jobs">
  <li>
    <h2><a href="/jobs/123/">Python Backend Developer</a></h2>
    <span class="listing-company-name">ABC Software</span>
    <span class="listing-location">Lahore, Pakistan</span>
    <span class="listing-posted">Posted: 12 June 2026</span>
  </li>
</ol>
"""


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; PythonJobScraper/1.0; "
                "+https://www.python.org/jobs/)"
            )
        },
    )

    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def load_html(args: argparse.Namespace) -> tuple[str, str]:
    if args.html_file:
        html_path = Path(args.html_file)
        return html_path.read_text(encoding="utf-8"), args.base_url

    if args.url:
        return fetch_html(args.url), args.url

    return SAMPLE_HTML, args.base_url


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse Python.org-style job board HTML."
    )
    parser.add_argument(
        "--html-file",
        help="Path to a saved HTML file to parse.",
    )
    parser.add_argument(
        "--url",
        help="URL to download and parse.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL used to convert relative job links into full URLs.",
    )

    args = parser.parse_args()

    try:
        html, base_url = load_html(args)
        jobs = parse_python_job_board(html, base_url)
    except ModuleNotFoundError as error:
        if error.name == "bs4":
            print(
                "Missing dependency: install it with "
                "`.venv/bin/python -m pip install beautifulsoup4`.",
                file=sys.stderr,
            )
            return 1
        raise

    if not jobs:
        print("No jobs found.")
        return 0

    for index, job in enumerate(jobs, start=1):
        print(f"{index}. {job.title}")
        print(f"   Company: {job.company_name or 'Unknown'}")
        print(f"   Location: {job.location or 'Unknown'}")
        print(f"   Posted: {job.date_posted or 'Unknown'}")
        print(f"   URL: {job.job_url}")

        if job.salary:
            print(f"   Salary: {job.salary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
