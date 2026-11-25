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
ROBOTS_TIMEOUT = 20


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
        self.robots_reason: dict[str, str] = {}

    def _allowed(self, url: str) -> bool:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            self._robots[base], self.robots_reason[base] = self._load_robots(base)
        parser = self._robots[base]
        if parser is None:
            return False
        if not parser.can_fetch(USER_AGENT, url):
            self.robots_reason[base] = "robots.txt disallows this path for our user agent"
            return False
        return True

    def _load_robots(self, base: str) -> tuple[urllib.robotparser.RobotFileParser | None, str]:
        """Parse robots.txt. Per RFC 9309: 4xx = no rules (allowed); 5xx or unreachable = disallow.
        Unreachable gets one retry, because a single timeout is common."""
        reason = ""
        for attempt in range(2):
            try:
                resp = self.session.get(base + "/robots.txt", timeout=ROBOTS_TIMEOUT)
            except requests.RequestException as exc:
                reason = f"robots.txt unreachable: {type(exc).__name__}"
                time.sleep(3 * (attempt + 1))
                continue
            parser = urllib.robotparser.RobotFileParser()
            if resp.status_code >= 500:
                reason = f"robots.txt returned HTTP {resp.status_code}"
                time.sleep(3 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                parser.parse([])
                return parser, f"no robots.txt (HTTP {resp.status_code})"
            parser.parse(resp.text.splitlines())
            return parser, "robots.txt read"
        return None, reason

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
                parts = urlparse(url)
                reason = self.robots_reason.get(f"{parts.scheme}://{parts.netloc}", "")
                raise RobotsDisallowed(f"not fetching {url}: {reason}")
            self._wait(url)
            resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=False, **kwargs)
            if resp.is_redirect and "Location" in resp.headers:
                url = urljoin(url, resp.headers["Location"])
                continue
            resp.raise_for_status()
            return resp
        raise requests.TooManyRedirects(f"more than {max_redirects} redirects for {url}")

    def post_json(self, url: str, body: dict) -> requests.Response:
        """POST a JSON query (as a finder page does for its own search), robots.txt checked."""
        if not self._allowed(url):
            parts = urlparse(url)
            raise RobotsDisallowed(f"not fetching {url}: {self.robots_reason.get(f'{parts.scheme}://{parts.netloc}', '')}")
        self._wait(url)
        resp = self.session.post(url, json=body, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp


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


_ANCHOR = re.compile(r"""<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""", re.IGNORECASE | re.DOTALL)


def all_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """(absolute url, link text) for every <a href> on the page, in page order."""
    out = []
    for href, inner in _ANCHOR.findall(html):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inner)).strip()
        out.append((urljoin(base_url, href.replace("&amp;", "&")), text))
    return out


def write_link_inventory(name: str, page_url: str, links: list[tuple[str, str]]) -> Path:
    """docs/data_inventory/<name>_links.md: every link on a source page, so a changed page
    layout can be diagnosed from the repository without fetching the page again."""
    path = ROOT / "docs" / "data_inventory" / f"{name}_links.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Links on {page_url}", "", f"Fetched {today()}.", "", "| text | url |", "|---|---|"]
    lines += [f"| {text[:80].replace('|', '/')} | {url} |" for url, text in links]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


DATA_TYPES = ("spreadsheetml", "ms-excel", "zip", "csv", "octet-stream")


def looks_like_data(resp: requests.Response) -> bool:
    """True when a response is a data file (Excel/zip/CSV) rather than an HTML page."""
    ctype = resp.headers.get("Content-Type", "").lower()
    if "html" in ctype:
        return False
    head = resp.content[:4]
    return any(t in ctype for t in DATA_TYPES) or head[:2] == b"PK" or head == b"\xd0\xcf\x11\xe0"


def safe_filename(url: str, content_disposition: str | None = None) -> str:
    if content_disposition:
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
        if match:
            return re.sub(r"[^\w.\-]+", "_", match.group(1))
    name = Path(urlparse(url).path).name or "download"
    return re.sub(r"[^\w.\-]+", "_", name)
