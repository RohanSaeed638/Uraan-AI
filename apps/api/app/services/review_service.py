"""Mentor reviews of a learner's work: a public GitHub repository, pasted code,
or their Uraan portfolio."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import AIUnavailableError, complete_text
from app.ai.parser import parse_ai_json
from app.ai.prompts.review_prompt import REVIEW_PROMPT
from app.ai.schemas.review_schema import ReviewOutput
from app.ai.versions import prompt_version
from app.core.config import settings
from app.models.ai_request import AiRequest
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.github_fetch import (
    GithubClient,
    GithubError,
    RepoSnapshot,
    parse_github_url,
)

logger = logging.getLogger(__name__)

# Reviews a learner may run in 24 hours. Failed attempts do not count.
DAILY_LIMIT = 10
MAX_CODE_CHARS = 20_000
MAX_PORTFOLIO_PROJECTS = 8

REVIEW_FAILED = "We could not review that right now. Please try again."

SUBJECT_CODE = "a piece of code the learner pasted"


def work_from_snapshot(snapshot: RepoSnapshot) -> tuple[str, str, str]:
    """(subject, work text, coverage note) for a repository."""
    header = f"Repository {snapshot.name}"

    if snapshot.description:
        header += f": {snapshot.description}"
    if snapshot.language:
        header += f" (main language {snapshot.language})"

    blocks = [f"=== {path} ===\n{text}" for path, text in snapshot.files]
    coverage = f"You were shown {len(snapshot.files)} file(s)."

    if snapshot.skipped_files:
        coverage += (
            f" {snapshot.skipped_files} other file(s) were left out, so do not assume "
            "anything about them."
        )

    return header, "\n\n".join(blocks), coverage


def work_from_projects(projects: list) -> tuple[str, str, str]:
    lines = []

    for p in projects[:MAX_PORTFOLIO_PROJECTS]:
        lines.append(
            f"- {p.title}: {p.description or '(no description)'} "
            f"| tech: {', '.join(p.tech or []) or 'not listed'} "
            f"| repo: {'yes' if p.repo_url else 'no'} | live demo: {'yes' if p.live_url else 'no'}"
        )

    return (
        "the learner's project portfolio (as written on their Uraan AI portfolio)",
        "\n".join(lines),
        "You only see the written descriptions, not the projects themselves: review how "
        "well the portfolio presents their work.",
    )


class ReviewService:
    def __init__(self, db: AsyncSession, github: GithubClient | None = None, ask=None):
        self.db = db
        self.profiles = ProfileRepository(db)
        self.settings = SettingsRepository(db)
        self.portfolio = PortfolioRepository(db)
        self._github = github
        self._ask = ask or complete_text

    async def _require_allowed(self, profile) -> None:
        row = await self.settings.get_by_profile_id(profile.id)

        if row is not None and not row.ai_mentor_enabled:
            raise HTTPException(status_code=403, detail="AI Mentor is turned off in Settings.")

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        used = (
            await self.db.execute(
                select(func.count()).select_from(AiRequest).where(
                    AiRequest.profile_id == profile.id,
                    AiRequest.purpose == "review",
                    AiRequest.success.is_(True),
                    AiRequest.created_at >= since,
                )
            )
        ).scalar_one()

        if used >= DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"You have used today's {DAILY_LIMIT} reviews. Try again tomorrow.",
            )

    async def _gather(self, request: dict, profile) -> tuple[str, str, str, str]:
        """(label shown to the learner, subject, work, coverage)."""
        kind = request["kind"]

        if kind == "code":
            code = request["code"].strip()
            language = (request.get("language") or "").strip()
            subject = SUBJECT_CODE + (f" ({language})" if language else "")

            return "Pasted code", subject, code, "You were shown all of it."

        if kind == "portfolio":
            projects = await self.portfolio.list_projects(profile.id)

            if not projects:
                raise HTTPException(
                    status_code=409,
                    detail="Add a project to your portfolio first, then ask for a review.",
                )

            subject, work, coverage = work_from_projects(projects)

            return "Your portfolio", subject, work, coverage

        try:
            ref = parse_github_url(request["url"])
            github = self._github or GithubClient(settings.GITHUB_TOKEN)

            try:
                snapshot = await github.snapshot(ref)
            finally:
                if self._github is None:
                    await github.close()
        except GithubError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        subject, work, coverage = work_from_snapshot(snapshot)

        return snapshot.label, subject, work, coverage

    async def review(self, auth_user_id, request: dict) -> dict:
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        await self._require_allowed(profile)

        label, subject, work, coverage = await self._gather(request, profile)

        note = (request.get("note") or "").strip()
        prompt = REVIEW_PROMPT.format(
            skill=getattr(profile.skill_level, "value", profile.skill_level) or "beginner",
            career=(profile.career_slug or "software").replace("-", " "),
            subject=subject,
            note=f"The learner asks: {note}" if note else "",
            work=work,
            coverage=coverage,
        )

        for attempt in range(2):
            try:
                text = await self._ask(
                    [
                        {"role": "system", "content": "You review learners' work. You output only JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    purpose="review",
                    temperature=0.3,
                    max_tokens=2000,
                    json_mode=True,
                    profile_id=profile.id,
                    prompt_version=prompt_version("review"),
                )
                output = ReviewOutput(**parse_ai_json(text))

                return {"kind": request["kind"], "reviewed": label, **output.model_dump()}
            except AIUnavailableError:
                break
            except (ValueError, ValidationError):
                logger.warning("Review answer rejected (attempt %s)", attempt + 1)

        raise HTTPException(status_code=502, detail=REVIEW_FAILED)
