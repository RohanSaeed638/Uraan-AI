"""Finds learning links that no longer work, so a learner never meets a dead one.

The AI writes resource links from memory and some are invented or have moved; this checks them.
Be careful in both directions:

* A link is only called **dead** on strong evidence: the page is gone (404, 410), the site does not
  exist (the name does not resolve), or the page's own title says it was not found. Sites that block
  robots (403, 429, odd status codes), are slow, or are briefly down are **unknown**, and unknown
  links are left alone: removing a good link is worse than keeping a doubtful one.
* The checker fetches addresses the AI chose, so it refuses private and internal addresses at every
  step, including after redirects (server-side request forgery).
"""
import asyncio
import ipaddress
import logging
import re
import socket
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 8.0
MAX_REDIRECTS = 5
MAX_BODY = 30_000
CONCURRENCY = 8
USER_AGENT = "UraanAI-LinkChecker/1.0 (checks that learning resources still exist)"

OK, DEAD, UNKNOWN = "ok", "dead", "unknown"

# What a robot-blocking or overloaded site answers: not evidence that the page is gone.
BLOCKED_STATUSES = {400, 401, 403, 406, 407, 408, 409, 418, 423, 425, 429, 451, 999}
GONE_STATUSES = {404, 410}

TITLE = re.compile(rb"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# A page title that says the page is missing: it STARTS that way ("404 Not Found", "Page not found | Site",
# "Error 404") or ENDS that way ("Courses - Page Not Found"). A title that merely mentions it
# ("Understanding 404 errors in HTTP") does not count.
MISSING_AT_START = re.compile(
    r"^\W*(error\s*[:\-]?\s*)?(404\b|page not found|not found|file not found|"
    r"the page you (are looking for|requested) (could not|can.?t|cannot|was not|is not)|"
    r"this page (doesn.?t|does not|no longer) exist|oops[,!. ]+(page|we can))",
    re.IGNORECASE,
)
MISSING_AT_END = re.compile(r"[\-|–—:·]\s*(404|page not found|not found)\s*$", re.IGNORECASE)


def title_says_missing(title: str) -> bool:
    title = " ".join(title.split())

    return bool(MISSING_AT_START.search(title) or MISSING_AT_END.search(title))

YOUTUBE_WATCH = re.compile(r"^https?://(www\.|m\.)?(youtube\.com/watch|youtu\.be/|youtube\.com/shorts/)", re.IGNORECASE)
SEARCH_PAGES = re.compile(
    r"^https?://(www\.)?(google\.[a-z.]+/search|youtube\.com/results|bing\.com/search|duckduckgo\.com/\?)", re.IGNORECASE
)


@dataclass
class LinkResult:
    status: str  # ok | dead | unknown
    http_status: int | None = None
    reason: str = ""


def fallback_link(title: str) -> str:
    """A search for the topic, used where a task has no working link left."""
    return "https://www.google.com/search?q=" + quote(f"{title} tutorial")


def is_search_link(url: str) -> bool:
    return bool(SEARCH_PAGES.match(url))


async def _resolve(host: str) -> list[str]:
    loop = asyncio.get_running_loop()
    info = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)

    return sorted({item[4][0] for item in info})


def _public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])

    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified
    )


async def public_destination(url: str, resolver=_resolve) -> str | None:
    """None if the address is fine to visit, otherwise why not."""
    parts = urlsplit(url)

    if parts.scheme not in ("http", "https"):
        return "not a web address"

    if not parts.hostname or parts.username or parts.password:
        return "malformed address"

    try:
        addresses = [parts.hostname] if _is_ip(parts.hostname) else await resolver(parts.hostname)
    except socket.gaierror:
        return "does not resolve"
    except Exception:
        return "could not look up"

    if not addresses or not all(_public(a) for a in addresses):
        return "private address"

    return None


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


async def _request(client: httpx.AsyncClient, method: str, url: str, resolver) -> tuple[httpx.Response | None, str]:
    """One request, following redirects by hand so every hop is checked. (response, "") or (None, why)."""
    for _ in range(MAX_REDIRECTS + 1):
        problem = await public_destination(url, resolver)

        if problem:
            return None, problem

        async with client.stream(method, url, follow_redirects=False) as response:
            if response.status_code in (301, 302, 303, 307, 308) and response.headers.get("location"):
                url = str(httpx.URL(url).join(response.headers["location"]))
                continue

            body = b""

            if method == "GET":
                async for chunk in response.aiter_bytes():
                    body += chunk

                    if len(body) >= MAX_BODY:
                        break

            response._content = body  # keep what was read, for the title check

            return response, ""

    return None, "too many redirects"


async def check_url(url: str, client: httpx.AsyncClient | None = None, resolver=_resolve) -> LinkResult:
    """Is this link still good? Never raises."""
    if is_search_link(url):
        return LinkResult(OK, reason="search page")

    own_client = client is None
    client = client or httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})

    try:
        if YOUTUBE_WATCH.match(url):
            return await _check_youtube(client, url, resolver)

        return await _check_page(client, url, resolver)
    except httpx.TimeoutException:
        return LinkResult(UNKNOWN, reason="timed out")
    except Exception as exc:  # a checker must never break what called it
        logger.info("Could not check %s: %s", url, exc)

        return LinkResult(UNKNOWN, reason=type(exc).__name__)
    finally:
        if own_client:
            await client.aclose()


async def _check_page(client: httpx.AsyncClient, url: str, resolver) -> LinkResult:
    # Many sites refuse HEAD, so a refused or failed HEAD is retried as GET.
    response, problem = await _request(client, "HEAD", url, resolver)

    if problem:
        return _from_problem(problem)

    if response.status_code in GONE_STATUSES:
        return LinkResult(DEAD, response.status_code, "page not found")

    if response.status_code >= 400 or response.status_code in (405, 501):
        response, problem = await _request(client, "GET", url, resolver)

        if problem:
            return _from_problem(problem)

        if response.status_code in GONE_STATUSES:
            return LinkResult(DEAD, response.status_code, "page not found")

        if response.status_code >= 400:
            return LinkResult(UNKNOWN, response.status_code, "blocked or unavailable")

        return _judge_body(response)

    # HEAD worked; also read the title of ordinary web pages to catch "200 OK" pages that say "not found".
    if "text/html" in response.headers.get("content-type", "") and response.status_code == 200:
        page, problem = await _request(client, "GET", url, resolver)

        if page is not None and page.status_code == 200:
            return _judge_body(page)

    return LinkResult(OK, response.status_code)


def _judge_body(response: httpx.Response) -> LinkResult:
    if "text/html" in response.headers.get("content-type", ""):
        match = TITLE.search(response.content or b"")

        if match and title_says_missing(match.group(1).decode("utf-8", "ignore")):
            return LinkResult(DEAD, response.status_code, "the page says it was not found")

    return LinkResult(OK, response.status_code)


def _from_problem(problem: str) -> LinkResult:
    if problem == "does not resolve":
        return LinkResult(DEAD, None, "the site does not exist")

    if problem in ("private address", "not a web address", "malformed address"):
        return LinkResult(DEAD, None, problem)

    return LinkResult(UNKNOWN, None, problem)


async def _check_youtube(client: httpx.AsyncClient, url: str, resolver) -> LinkResult:
    """Videos are checked through YouTube's own lookup: it answers 404 for removed videos and 401 for private ones."""
    response = await client.get("https://www.youtube.com/oembed", params={"url": url, "format": "json"})

    if response.status_code == 200:
        return LinkResult(OK, 200, "video exists")

    # 404 removed, 401 private, 400 an id that was never a video (what an AI that invents one gets back).
    if response.status_code in (400, 401, 404):
        return LinkResult(DEAD, response.status_code, "video removed, private or never existed")

    return LinkResult(UNKNOWN, response.status_code, "could not be checked")


async def check_many(urls: list[str], resolver=_resolve) -> dict[str, LinkResult]:
    """Checks each address once, a few at a time."""
    gate = asyncio.Semaphore(CONCURRENCY)
    results: dict[str, LinkResult] = {}

    async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:

        async def one(url: str):
            async with gate:
                results[url] = await check_url(url, client, resolver)

        await asyncio.gather(*(one(url) for url in dict.fromkeys(urls)))

    return results
