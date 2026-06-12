import time
from dataclasses import dataclass
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx

from .job_models import ScrapeResult
from .job_parser import parse_python_job_board


@dataclass(frozen=True, slots=True)
class ScraperConfig:
    """Configuration for a polite job board scraper."""

    base_url: str = "https://www.python.org/jobs/"
    max_pages: int = 2
    delay_seconds: float = 2.0
    timeout_seconds: float = 10.0
    user_agent: str = "AttaSecurityScanner/0.1 (+portfolio project)"
    respect_robots: bool = True


class RobotsPolicy:
    """Loads and checks robots.txt rules for a target website."""

    def __init__(self) -> None:
        self._parser = RobotFileParser()
        self._loaded = False

    def load(self, client: httpx.Client, base_url: str) -> None:
        """Fetch robots.txt and parse its rules."""

        robots_url = urljoin(base_url, "/robots.txt")

        try:
            response = client.get(robots_url)
            response.raise_for_status()
        except httpx.HTTPStatusError:
            self._loaded = False
            return
        except httpx.RequestError:
            self._loaded = False
            return

        self._parser.set_url(robots_url)
        self._parser.parse(response.text.splitlines())
        self._loaded = True

    def can_fetch(self, user_agent: str, url: str) -> bool:
        """Return True if the URL is allowed by robots.txt."""

        if not self._loaded:
            return True

        return self._parser.can_fetch(user_agent, url)


class PythonJobBoardScraper:
    """Scrapes job listings from the Python.org job board."""

    def __init__(
        self,
        config: ScraperConfig | None = None,
        transport: httpx.BaseTransport | None = None,
        robots_policy: RobotsPolicy | None = None,
    ) -> None:
        self.config = config or ScraperConfig()
        self.robots_policy = robots_policy or RobotsPolicy()
        self._transport = transport

    def scrape(self) -> ScrapeResult:
        """Scrape configured job board pages and return structured results."""

        headers = {"User-Agent": self.config.user_agent}
        listings = []
        pages_scraped = 0

        with httpx.Client(
            headers=headers,
            timeout=self.config.timeout_seconds,
            follow_redirects=True,
            transport=self._transport,
        ) as client:
            if self.config.respect_robots:
                self.robots_policy.load(client, self.config.base_url)

            for page_number in range(1, self.config.max_pages + 1):
                page_url = self._build_page_url(page_number)

                if not self.robots_policy.can_fetch(
                    self.config.user_agent,
                    page_url,
                ):
                    raise PermissionError(
                        f"robots.txt does not allow scraping: {page_url}"
                    )

                html = self._fetch_page(client, page_url)
                page_listings = parse_python_job_board(
                    html=html,
                    base_url=self.config.base_url,
                )

                if not page_listings:
                    break

                listings.extend(page_listings)
                pages_scraped += 1

                if page_number < self.config.max_pages:
                    time.sleep(self.config.delay_seconds)

        return ScrapeResult(
            source_url=self.config.base_url,
            listings=listings,
            pages_scraped=pages_scraped,
        )

    def _fetch_page(self, client: httpx.Client, url: str) -> str:
        """Fetch one page and return HTML text."""

        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Request timed out for {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Unexpected HTTP status for {url}: "
                f"{exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request failed for {url}: {exc}") from exc

        return response.text

    def _build_page_url(self, page_number: int) -> str:
        """Build paginated URL for the configured job board."""

        if page_number == 1:
            return self.config.base_url

        return f"{self.config.base_url}?page={page_number}"
