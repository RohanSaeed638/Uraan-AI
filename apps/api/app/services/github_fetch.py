"""Reads a public GitHub repository so the mentor can review it.

Safety rules, because the URL comes from a user:
- Only https://github.com/<owner>/<repo>[/tree|blob/<ref>/<path>] is accepted.
  The owner and repo names are checked against GitHub's own character rules
  and the requests are then built from those parts, never from the pasted URL.
- Requests go to api.github.com only. Redirects are not followed blindly: one
  redirect is allowed, and only to another api.github.com path.
- Hard limits on files, bytes, time and total text.
"""
import base64
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

API = "https://api.github.com"

OWNER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
REPO = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
REF = re.compile(r"^[A-Za-z0-9._/@+-]{1,200}$")

MAX_FILES = 8
MAX_FILE_BYTES = 100_000       # larger files are skipped, not read
MAX_FILE_CHARS = 12_000        # per file, after reading
MAX_TOTAL_CHARS = 40_000
TIMEOUT = 10.0

SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "out", ".next", ".git", "venv", ".venv",
    "__pycache__", "target", "coverage", ".idea", ".vscode", "migrations", "assets", "public",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
    "composer.lock", "Cargo.lock", "go.sum",
}
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".cs",
    ".cpp", ".c", ".h", ".kt", ".swift", ".dart", ".sql", ".sh", ".html", ".css", ".vue",
}
MANIFESTS = {
    "package.json", "pyproject.toml", "requirements.txt", "pubspec.yaml", "pom.xml",
    "build.gradle", "go.mod", "Cargo.toml", "composer.json", "Gemfile", "Dockerfile",
}


class GithubError(Exception):
    """A problem with the repository or with reaching it; the message is safe
    to show to the learner."""


@dataclass
class GithubRef:
    owner: str
    repo: str
    ref: str | None = None
    path: str | None = None


@dataclass
class RepoSnapshot:
    name: str
    description: str | None
    language: str | None
    topics: list[str]
    files: list[tuple[str, str]] = field(default_factory=list)
    skipped_files: int = 0

    @property
    def label(self) -> str:
        return f"{self.name} ({len(self.files)} files read)"


def parse_github_url(url: str) -> GithubRef:
    """The repository a pasted link points at, or GithubError."""
    bad = GithubError("Paste a link like https://github.com/owner/repository")
    url = (url or "").strip()

    try:
        parsed = urlparse(url)
    except ValueError:
        raise bad

    if (
        parsed.scheme != "https"
        or parsed.hostname not in ("github.com", "www.github.com")
        or parsed.username
        or parsed.password
        or parsed.port
    ):
        raise bad

    parts = [p for p in parsed.path.split("/") if p]

    if len(parts) < 2:
        raise bad

    owner, repo = parts[0], parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    if not OWNER.match(owner) or not REPO.match(repo) or repo in (".", ".."):
        raise bad

    ref = path = None

    if len(parts) > 2:
        if parts[2] not in ("tree", "blob") or len(parts) < 4:
            raise bad

        ref = parts[3]
        path = "/".join(parts[4:]) or None

        if not REF.match(ref) or ".." in ref or (path and ".." in path.split("/")):
            raise bad

    return GithubRef(owner=owner, repo=repo, ref=ref, path=path)


def pick_files(tree: list[dict], path_prefix: str | None = None) -> tuple[list[str], int]:
    """The files worth reading, best first, and how many were left out."""
    candidates: list[tuple[int, int, str]] = []

    for item in tree:
        if item.get("type") != "blob":
            continue

        path = item["path"]
        parts = path.split("/")
        name = parts[-1]

        if path_prefix and not path.startswith(path_prefix.rstrip("/") + "/") and path != path_prefix:
            continue
        if any(p in SKIP_DIRS for p in parts[:-1]) or name in SKIP_FILES:
            continue
        if (item.get("size") or 0) > MAX_FILE_BYTES or (item.get("size") or 0) == 0:
            continue

        lower = name.lower()
        ext = "." + lower.rsplit(".", 1)[-1] if "." in lower else ""

        if lower.startswith("readme"):
            rank = 0
        elif name in MANIFESTS:
            rank = 1
        elif ext in SOURCE_EXTENSIONS:
            rank = 2
        else:
            continue

        # Shallow files first: entry points live near the top.
        candidates.append((rank, len(parts), path))

    candidates.sort()
    chosen = [p for _, _, p in candidates[:MAX_FILES]]

    return chosen, max(0, len(candidates) - len(chosen))


class GithubClient:
    def __init__(self, token: str = "", transport=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "UraanAI-ProjectReview",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._http = httpx.AsyncClient(
            base_url=API,
            headers=headers,
            timeout=TIMEOUT,
            follow_redirects=False,
            transport=transport,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        try:
            response = await self._http.get(path, params=params)

            # A renamed repository answers with a redirect to its numeric id.
            if response.status_code in (301, 302, 307, 308):
                target = urlparse(response.headers.get("location", ""))

                if target.hostname != "api.github.com" or not target.path.startswith("/repositories/"):
                    raise GithubError("GitHub sent us somewhere unexpected.")

                response = await self._http.get(target.path, params=params)
        except httpx.HTTPError:
            raise GithubError("We could not reach GitHub. Try again in a moment.")

        if response.status_code == 404:
            raise GithubError("We could not find that repository. Is it public?")

        if response.status_code in (403, 429):
            raise GithubError("GitHub is limiting requests right now. Try again in a few minutes.")

        if response.status_code >= 400:
            raise GithubError("GitHub could not give us that repository.")

        return response

    async def snapshot(self, ref: GithubRef) -> RepoSnapshot:
        base = f"/repos/{ref.owner}/{ref.repo}"

        meta = (await self._get(base)).json()

        if meta.get("private"):
            raise GithubError("That repository is private. Only public ones can be reviewed.")

        branch = ref.ref or meta.get("default_branch") or "main"
        tree = (await self._get(f"{base}/git/trees/{branch}", {"recursive": "1"})).json()
        paths, skipped = pick_files(tree.get("tree") or [], ref.path)

        if not paths:
            raise GithubError("We found no readable code or README in that repository.")

        files: list[tuple[str, str]] = []
        used = 0

        for path in paths:
            if used >= MAX_TOTAL_CHARS:
                skipped += 1
                continue

            data = (await self._get(f"{base}/contents/{path}", {"ref": branch})).json()

            if data.get("encoding") != "base64" or not data.get("content"):
                skipped += 1
                continue

            text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            text = text[: min(MAX_FILE_CHARS, MAX_TOTAL_CHARS - used)]
            files.append((path, text))
            used += len(text)

        return RepoSnapshot(
            name=f"{ref.owner}/{ref.repo}",
            description=meta.get("description"),
            language=meta.get("language"),
            topics=list(meta.get("topics") or [])[:8],
            files=files,
            skipped_files=skipped,
        )
