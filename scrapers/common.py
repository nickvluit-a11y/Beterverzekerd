"""Shared helpers for all scrapers: polite HTTP, robots.txt, raw-data paths, link discovery."""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
USER_AGENT = "BeterverzekerdBot/0.1 (+https://github.com/nickvluit-a11y/beterverzekerd)"
DELAY_SECONDS = 2.0
TIMEOUT = 60


class RobotsDisallowed(RuntimeError):
    pass


class PoliteSession:
    """requests.Session that respects robots.txt and waits between requests per host."""

    def __init__(self, delay: float = DELAY_SECONDS):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.delay = delay
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._last_request: dict[str, float] = {}

    def _allowed(self, url: str) -> bool:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            try:
                resp = self.session.get(base + "/robots.txt", timeout=TIMEOUT)
                if resp.status_code >= 500:
                    parser = None  # unknown: be conservative
                elif resp.status_code >= 400:
                    parser.parse([])  # no robots.txt: everything allowed
                else:
                    parser.parse(resp.text.splitlines())
            except requests.RequestException:
                parser = None
            self._robots[base] = parser
        parser = self._robots[base]
        if parser is None:
            return False
        return parser.can_fetch(USER_AGENT, url)

    def _wait(self, url: str) -> None:
        host = urlparse(url).netloc
        elapsed = time.monotonic() - self._last_request.get(host, 0.0)
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request[host] = time.monotonic()

    def get(self, url: str, max_redirects: int = 5, **kwargs) -> requests.Response:
        """GET with robots.txt checked for every hop of a redirect chain."""
        for _ in range(max_redirects + 1):
            if not self._allowed(url):
                raise RobotsDisallowed(f"robots.txt disallows (or could not be read for) {url}")
            self._wait(url)
            resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False, **kwargs)
            if resp.is_redirect and "Location" in resp.headers:
                url = urljoin(url, resp.headers["Location"])
                continue
            resp.raise_for_status()
            return resp
        raise requests.TooManyRedirects(f"more than {max_redirects} redirects for {url}")


def today() -> str:
    return dt.date.today().isoformat()


def raw_dir(source: str, peildatum: str | None = None) -> Path:
    """data/raw/<source>/<peildatum>/ (peildatum defaults to today's date)."""
    path = RAW / source / (peildatum or today())
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_meta(directory: Path, **fields) -> None:
    """Store provenance next to the raw files: source, url, peildatum, fetched_at."""
    fields.setdefault("fetched_at", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    (directory / "meta.json").write_text(json.dumps(fields, indent=2, ensure_ascii=False), encoding="utf-8")


_HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def find_links(html: str, base_url: str, pattern: str) -> list[str]:
    """Absolute URLs of all hrefs matching regex `pattern` (case-insensitive), in page order, unique."""
    regex = re.compile(pattern, re.IGNORECASE)
    seen: dict[str, None] = {}
    for href in _HREF.findall(html):
        href = href.replace("&amp;", "&")
        if regex.search(href):
            seen.setdefault(urljoin(base_url, href), None)
    return list(seen)


def safe_filename(url: str, content_disposition: str | None = None) -> str:
    if content_disposition:
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
        if match:
            return re.sub(r"[^\w.\-]+", "_", match.group(1))
    name = Path(urlparse(url).path).name or "download"
    return re.sub(r"[^\w.\-]+", "_", name)
