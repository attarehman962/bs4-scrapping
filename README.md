# Python Job Scraper

A small, professional Python scraping project for extracting job listings from a Python.org-style job board.

The project parses job listing HTML into structured Python dataclasses, optionally fetches real pages with `httpx`, respects `robots.txt`, and saves unique jobs to CSV.

## Features

- Parse Python.org-style job cards from HTML
- Extract title, company name, location, posted date, salary, job URL, and source
- Convert relative job links into absolute URLs
- Scrape multiple pages with configurable delay and timeout
- Check `robots.txt` before scraping by default
- Save listings to CSV
- Deduplicate jobs by `job_url`
- Includes pytest coverage for parser, scraper, storage, package exports, and salary handling

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── pytest.ini
├── scripts/
│   └── scrape_jobs.py
├── src/
│   └── security_scanner/
│       ├── __init__.py
│       └── scraping/
│           ├── __init__.py
│           ├── job_models.py
│           ├── job_parser.py
│           ├── job_scraper.py
│           └── job_storage.py
└── tests/
    └── test_job_scraper.py
```

## Requirements

- Python 3.14+
- `beautifulsoup4`
- `httpx`
- `pytest` for running tests

Runtime dependencies are listed in:

```text
requirements.txt
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install runtime dependencies:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Install pytest if it is not already installed:

```bash
.venv/bin/python -m pip install pytest
```

Important: use the project virtualenv when running scripts or tests. Do not use the system `pytest`, because it may not have `bs4` installed.

Correct:

```bash
.venv/bin/python -m pytest -q
```

Avoid:

```bash
pytest
```

## Usage

Run the scraper with default settings:

```bash
.venv/bin/python scripts/scrape_jobs.py
```

By default, it scrapes:

```text
https://www.python.org/jobs/
```

and saves results to:

```text
data/scraped_jobs.csv
```

Show available CLI options:

```bash
.venv/bin/python scripts/scrape_jobs.py --help
```

Example with custom options:

```bash
.venv/bin/python scripts/scrape_jobs.py \
  --base-url https://www.python.org/jobs/ \
  --max-pages 3 \
  --delay 1.5 \
  --timeout 15 \
  --output data/python_jobs.csv
```

If you intentionally do not want to check `robots.txt`:

```bash
.venv/bin/python scripts/scrape_jobs.py --ignore-robots
```

## Library Examples

### Parse HTML directly

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from security_scanner.scraping import parse_python_job_board

html = """
<ol class="list-recent-jobs">
  <li>
    <h2><a href="/jobs/123/">Python Backend Developer</a></h2>
    <span class="listing-company-name">ABC Software</span>
    <span class="listing-location">Lahore, Pakistan</span>
    <span class="listing-posted">Posted: 12 June 2026</span>
    <span class="listing-salary">PKR 250,000 - 400,000</span>
  </li>
</ol>
"""

jobs = parse_python_job_board(html, "https://www.python.org/jobs/")
print(jobs[0])
PY
```

Expected output shape:

```text
JobListing(title='Python Backend Developer', company_name='ABC Software', location='Lahore, Pakistan', date_posted='12 June 2026', job_url='https://www.python.org/jobs/123/', salary='PKR 250,000 - 400,000', source='python.org')
```

### Save jobs to CSV

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from security_scanner.scraping import JobListing, save_jobs_to_csv

jobs = [
    JobListing(
        title="Python Developer",
        company_name="ABC",
        location="Remote",
        date_posted="12 June 2026",
        job_url="https://example.com/jobs/1",
        salary="PKR 250,000 - 400,000",
    )
]

count = save_jobs_to_csv(jobs, Path("data/scraped_jobs.csv"))
print(f"New rows written: {count}")
PY
```

## Public API

The main public imports are available from `security_scanner.scraping`:

```python
from security_scanner.scraping import (
    JobListing,
    PythonJobBoardScraper,
    RobotsPolicy,
    ScrapeResult,
    ScraperConfig,
    load_existing_urls,
    parse_python_job_board,
    save_jobs_to_csv,
)
```

### `JobListing`

Represents one scraped job:

```python
JobListing(
    title="Python Developer",
    company_name="ABC",
    location="Remote",
    date_posted="12 June 2026",
    job_url="https://example.com/jobs/1",
    salary="PKR 250,000 - 400,000",
)
```

Fields:

```text
title: str
company_name: str | None
location: str | None
date_posted: str | None
job_url: str
salary: str | None
source: str
```

### `ScraperConfig`

Controls scraper behavior:

```python
ScraperConfig(
    base_url="https://www.python.org/jobs/",
    max_pages=2,
    delay_seconds=2.0,
    timeout_seconds=10.0,
    user_agent="AttaSecurityScanner/0.1 (+portfolio project)",
    respect_robots=True,
)
```

## Running Tests

Run the test suite using the virtualenv Python:

```bash
.venv/bin/python -m pytest -q
```

Current expected result:

```text
10 passed
```

The project includes `pytest.ini`:

```ini
[pytest]
pythonpath = src
testpaths = tests
```

That lets pytest find the `src/security_scanner` package without manually setting `PYTHONPATH`.

## CSV Output

CSV rows include:

```text
title,company_name,location,date_posted,job_url,source,salary
```

The storage layer deduplicates jobs by `job_url`. If the same URL is passed twice in one run, only one row is written.

## Troubleshooting

### `ModuleNotFoundError: No module named 'security_scanner.scraping'`

You are probably running Python without the `src` directory on the import path.

For tests, use:

```bash
.venv/bin/python -m pytest -q
```

For one-shot scripts, use:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from security_scanner.scraping import JobListing
print(JobListing)
PY
```

### `ModuleNotFoundError: No module named 'bs4'`

Install runtime dependencies into the project virtualenv:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Also make sure you are not running the system `pytest`:

```bash
which pytest
```

If it prints `/usr/bin/pytest`, use this instead:

```bash
.venv/bin/python -m pytest -q
```

### `python: command not found`

Use `python3` or the virtualenv interpreter:

```bash
python3 --version
.venv/bin/python --version
```

### `__pycache__` keeps appearing

Python creates `__pycache__` folders when it imports modules. This project ignores them in `.gitignore`.

To remove project cache folders:

```bash
find scripts src tests -type d -name __pycache__ -prune -exec rm -r {} +
```

## Notes on Responsible Scraping

- Keep `respect_robots=True` unless you have a clear reason not to.
- Use a polite delay between requests.
- Avoid high `max_pages` values unless you understand the target site limits.
- Do not scrape private or restricted content.

## Status

This is a focused learning/portfolio project with a clean parser, scraper, CSV storage layer, CLI script, and tests.
