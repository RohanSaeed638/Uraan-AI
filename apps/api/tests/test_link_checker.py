"""The link checker: what counts as dead, and that it can never be pointed at internal addresses.

No real websites are visited: a pretend web answers through httpx's mock transport."""
import asyncio
import selectors
import socket

import httpx
import pytest

from app.services import link_checker
from app.services.link_checker import DEAD, OK, UNKNOWN, check_many, check_url, fallback_link, is_search_link, title_says_missing


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


async def public_resolver(host):
    return ["93.184.216.34"]


def web(handler):
    """A client whose every request is answered by `handler(request) -> httpx.Response`."""
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5)


def check(handler, url="https://example.com/course", resolver=public_resolver):
    async def go():
        async with web(handler) as client:
            return await check_url(url, client, resolver)

    return run(go())


def html(title, status=200):
    return httpx.Response(status, headers={"content-type": "text/html"}, content=f"<html><head><title>{title}</title></head></html>".encode())


def by_method(**answers):
    """Different answers for HEAD and GET."""
    return lambda request: answers[request.method](request) if request.method in answers else httpx.Response(500)


# ---- what is a good link --------------------------------------------------------------------------------------------------


def test_an_ordinary_page_is_ok():
    result = check(lambda r: html("Python Tutorial"))

    assert (result.status, result.http_status) == (OK, 200)


def test_a_page_that_refuses_head_but_answers_get_is_ok():
    result = check(by_method(HEAD=lambda r: httpx.Response(405), GET=lambda r: html("Docs")))

    assert result.status == OK


def test_a_redirect_to_a_working_page_is_ok():
    def handler(request):
        if request.url.path == "/old":
            return httpx.Response(301, headers={"location": "/new"})

        return html("New home")

    assert check(handler, "https://example.com/old").status == OK


def test_pages_that_are_not_html_are_ok_without_reading_them():
    assert check(lambda r: httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF")).status == OK


# ---- what is dead ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("status", [404, 410])
def test_a_missing_page_is_dead(status):
    result = check(lambda r: httpx.Response(status))

    assert result.status == DEAD and result.http_status == status


@pytest.mark.parametrize(
    "title",
    ["404 Not Found", "Page not found | Example Docs", "Courses - Page Not Found", "Error 404", "Oops, page not found"],
)
def test_a_page_whose_title_says_it_is_missing_is_dead_even_with_a_200(title):
    result = check(lambda r: html(title))

    assert result.status == DEAD and "not found" in result.reason


@pytest.mark.parametrize(
    "title", ["Understanding 404 errors in HTTP", "How to fix a not found error", "Python Tutorial", "4040 ways to learn"]
)
def test_a_title_that_only_mentions_the_words_is_fine(title):
    assert check(lambda r: html(title)).status == OK


def test_a_site_that_does_not_exist_is_dead():
    async def gone(host):
        raise socket.gaierror("Name or service not known")

    result = check(lambda r: html("never reached"), "https://no-such-site.example/x", gone)

    assert result.status == DEAD and "does not exist" in result.reason


# ---- what is only doubtful (and so left alone) ----------------------------------------------------------------------------


@pytest.mark.parametrize("status", [401, 403, 429, 999, 500, 502, 503])
def test_sites_that_block_robots_or_are_down_are_unknown_not_dead(status):
    result = check(lambda r: httpx.Response(status))

    assert result.status == UNKNOWN


def test_a_slow_site_is_unknown():
    def slow(request):
        raise httpx.ConnectTimeout("too slow")

    assert check(slow).status == UNKNOWN


def test_a_failed_name_lookup_that_is_not_a_clear_no_is_unknown():
    async def flaky(host):
        raise RuntimeError("resolver hiccup")

    assert check(lambda r: html("x"), resolver=flaky).status == UNKNOWN


def test_whatever_goes_wrong_it_never_raises():
    def boom(request):
        raise ValueError("something odd")

    assert check(boom).status == UNKNOWN


def test_too_many_redirects_is_unknown():
    assert check(lambda r: httpx.Response(302, headers={"location": "/again"})).status == UNKNOWN


# ---- it cannot be used to probe the inside of a network ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost:8000/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/file",
        "https://user:secret@example.com/",
    ],
)
def test_internal_and_non_web_addresses_are_refused_without_any_request(url):
    seen = []

    async def private_resolver(host):
        return ["127.0.0.1"] if host == "localhost" else ["93.184.216.34"]

    def handler(request):
        seen.append(request)
        return html("should not be asked")

    result = check(handler, url, private_resolver)

    assert result.status == DEAD and seen == []


def test_a_name_that_points_at_a_private_address_is_refused():
    async def sneaky(host):
        return ["93.184.216.34", "10.1.2.3"]  # one public answer is not enough

    assert check(lambda r: html("x"), "https://looks-public.example/", sneaky).status == DEAD


def test_a_redirect_into_the_internal_network_is_refused_at_that_step():
    visited = []

    async def resolver(host):
        return ["10.0.0.9"] if host == "internal.example" else ["93.184.216.34"]

    def handler(request):
        visited.append(request.url.host)

        if request.url.host == "example.com":
            return httpx.Response(302, headers={"location": "https://internal.example/secret"})

        return html("internal secret")

    result = check(handler, "https://example.com/start", resolver)

    assert result.status == DEAD and "private" in result.reason and "internal.example" not in visited


# ---- YouTube and search pages ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("status,expected", [(200, OK), (404, DEAD), (401, DEAD), (400, DEAD), (500, UNKNOWN), (429, UNKNOWN)])
def test_a_video_is_checked_through_youtubes_own_lookup(status, expected):
    asked = []

    def handler(request):
        asked.append(str(request.url))
        return httpx.Response(status, json={})

    result = check(handler, "https://www.youtube.com/watch?v=abc123")

    assert result.status == expected
    assert asked and "oembed" in asked[0] and len(asked) == 1


def test_a_search_page_is_never_requested():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(500)

    assert check(handler, "https://www.google.com/search?q=python+tutorial").status == OK
    assert check(handler, "https://www.youtube.com/results?search_query=python").status == OK
    assert seen == []


# ---- helpers -------------------------------------------------------------------------------------------------------------


def test_the_fallback_is_a_search_for_the_topic():
    url = fallback_link("Learn HTTP & REST")

    assert url.startswith("https://www.google.com/search?q=") and "Learn%20HTTP" in url and is_search_link(url)


def test_title_rule_examples():
    assert title_says_missing("  404   Not   Found ") and not title_says_missing("Notes on missing pages")


def test_many_links_are_checked_once_each_and_a_few_at_a_time(monkeypatch):
    running = {"now": 0, "peak": 0}
    calls = []

    async def fake_check(url, client, resolver):
        calls.append(url)
        running["now"] += 1
        running["peak"] = max(running["peak"], running["now"])
        await asyncio.sleep(0.01)
        running["now"] -= 1

        return link_checker.LinkResult(OK)

    monkeypatch.setattr(link_checker, "check_url", fake_check)
    urls = [f"https://example.com/{i}" for i in range(30)] + ["https://example.com/0"]
    results = run(check_many(urls))

    assert len(results) == 30 and len(calls) == 30  # the repeat was checked once
    assert running["peak"] <= link_checker.CONCURRENCY
