"""Check that every data source in sources.json is reachable and allowed by robots.txt.

Writes a Markdown report to docs/source_check/<YYYY-MM-DD>/report.md.
Standard library only, so it runs on a bare GitHub Actions runner.

Usage: python scrapers/check_sources.py
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "scrapers" / "sources.json"
USER_AGENT = "BeterverzekerdBot/0.1 (+https://github.com/nickvluit-a11y/beterverzekerd)"
DELAY_SECONDS = 2  # politeness delay between requests
TIMEOUT = 30
MAX_BYTES = 2_000_000  # only read the start of large files
LINK_PATTERN = re.compile(r'href="([^"]+\.(?:xlsx?|csv|zip|pdf)[^"]*)"', re.IGNORECASE)
DOWNLOAD_HANDLER = re.compile(r'href="([^"]*DownloadDocument\.ashx[^"]*)"', re.IGNORECASE)


def robots_allowed(url: str, cache: dict) -> str:
    """Return 'yes', 'no' or 'unknown' for whether robots.txt allows fetching url."""
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in cache:
        parser = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                parser.parse(resp.read().decode("utf-8", errors="replace").splitlines())
        except urllib.error.HTTPError as exc:
            # 4xx on robots.txt means no restrictions; 5xx means unknown
            parser = "allow_all" if 400 <= exc.code < 500 else None
        except Exception:
            parser = None
        cache[base] = parser
    parser = cache[base]
    if parser is None:
        return "unknown"
    if parser == "allow_all":
        return "yes"
    return "yes" if parser.can_fetch(USER_AGENT, url) else "no"


def check(source: dict, robots_cache: dict) -> dict:
    url = source["url"]
    result = {"id": source["id"], "layer": source["layer"], "url": url, "links": []}
    result["robots"] = robots_allowed(url, robots_cache)
    if result["robots"] == "no":
        result["status"] = "skipped (robots.txt)"
        return result
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(MAX_BYTES)
            result["status"] = resp.status
            result["final_url"] = resp.geturl()
            result["content_type"] = resp.headers.get("Content-Type", "")
            result["bytes_read"] = len(body)
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        return result
    except Exception as exc:  # network errors must not stop the other checks
        result["status"] = f"error: {type(exc).__name__}: {exc}"
        return result

    if source.get("list_links") and "html" in result["content_type"]:
        html = body.decode("utf-8", errors="replace")
        found = LINK_PATTERN.findall(html) + DOWNLOAD_HANDLER.findall(html)
        result["links"] = sorted({urljoin(result["final_url"], h.replace("&amp;", "&")) for h in found})
    return result


def write_report(results: list[dict], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Source check {dt.date.today().isoformat()}",
        "",
        "| id | layer | status | robots | content type | url |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['layer']} | {r['status']} | {r['robots']} | "
            f"{r.get('content_type', '')} | {r.get('final_url', r['url'])} |"
        )
    for r in results:
        if r["links"]:
            lines += ["", f"## Download links on {r['id']}", ""]
            lines += [f"- {link}" for link in r["links"]]
    path = out_dir / "report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return path


def main() -> None:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    robots_cache: dict = {}
    results = []
    for i, source in enumerate(sources):
        if i:
            time.sleep(DELAY_SECONDS)
        result = check(source, robots_cache)
        print(f"{result['status']!s:>6}  {result['id']}")
        results.append(result)
    out_dir = ROOT / "docs" / "source_check" / dt.date.today().isoformat()
    print(f"Report: {write_report(results, out_dir)}")


if __name__ == "__main__":
    main()
