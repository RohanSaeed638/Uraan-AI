import asyncio
import re
from urllib.parse import quote_plus

import httpx

_YOUTUBE_ID = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:[^#\s]*&)?v=|embed/|shorts/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})"
)

OEMBED = "https://www.youtube.com/oembed"
TIMEOUT = 6.0


def youtube_id(url: str) -> str | None:
    match = _YOUTUBE_ID.search(url or "")

    return match.group(1) if match else None


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def search_url(query: str) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(
        query.strip()
    )


def is_search_url(url: str | None) -> bool:
    return bool(url) and "youtube.com/results" in url


async def video_exists(client: httpx.AsyncClient, video_id: str) -> bool:
    """True only when YouTube confirms the video exists and can be embedded
    (oEmbed answers 200). Any error counts as not usable."""
    try:
        response = await client.get(
            OEMBED,
            params={"url": canonical_url(video_id), "format": "json"},
        )
    except httpx.HTTPError:
        return False

    return response.status_code == 200


async def resolve_video(
    client: httpx.AsyncClient,
    candidates: list[str],
    search_query: str | None,
    fallback_query: str,
) -> str:
    """The first candidate that exists, else a YouTube search link, so a
    made-up video link never reaches a learner."""
    seen: set[str] = set()

    for candidate in candidates:
        video_id = youtube_id(candidate)

        if not video_id or video_id in seen:
            continue

        seen.add(video_id)

        if await video_exists(client, video_id):
            return canonical_url(video_id)

    return search_url(search_query or fallback_query)


async def resolve_many(
    jobs: list[tuple[list[str], str | None, str]],
) -> list[str]:
    """Resolves several videos concurrently: (candidates, query, fallback)."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return list(
            await asyncio.gather(
                *(
                    resolve_video(client, candidates, query, fallback)
                    for candidates, query, fallback in jobs
                )
            )
        )
