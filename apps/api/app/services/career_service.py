import logging
from app.ai.llm import use_profile

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.career_recommender import CareerRecommender
from app.repositories.career_repository import CareerRepository
from app.repositories.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)

LEVELS = {"beginner", "intermediate", "advanced"}
DEMANDS = {"low", "medium", "high", "very_high"}

RECOMMEND_FAILED = "We could not get recommendations right now. Try again."


class CareerService:
    def __init__(self, db: AsyncSession, recommender=None):
        self.repository = CareerRepository(db)
        self.profiles = ProfileRepository(db)
        self.recommender = recommender or CareerRecommender()

    async def search(self, **filters):
        if filters.get("difficulty") and filters["difficulty"] not in LEVELS:
            raise HTTPException(status_code=422, detail="Unknown difficulty")
        if filters.get("demand") and filters["demand"] not in DEMANDS:
            raise HTTPException(status_code=422, detail="Unknown demand level")

        careers, total = await self.repository.search(**filters)

        return {
            "items": careers,
            "total": total,
            "page": filters["page"],
            "page_size": filters["page_size"],
        }

    async def get(self, slug: str):
        career = await self.repository.get_by_slug(slug)

        if career is None:
            raise HTTPException(status_code=404, detail="Career not found")

        return career

    async def compare(self, slugs: list[str]):
        unique = list(dict.fromkeys(slugs))

        if len(unique) < 2:
            raise HTTPException(
                status_code=422, detail="Pick at least two different careers"
            )

        found = await self.repository.get_many(unique)
        missing = [s for s in unique if s not in found]

        if missing:
            raise HTTPException(
                status_code=404, detail=f"Career not found: {', '.join(missing)}"
            )

        return {"careers": [found[s] for s in unique]}

    async def recommend(self, auth_user_id, answers: dict):
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)

        # Whatever the learner did not type comes from their profile.
        if profile is not None:
            answers = {
                **answers,
                "education": answers.get("education") or profile.education,
                "daily_hours": answers.get("daily_hours") or profile.daily_hours,
                "goal": answers.get("goal") or profile.learning_goal,
            }

        careers = await self.repository.list_active()

        if profile is not None:
            use_profile(profile.id, profile.language)

        try:
            picks = await self.recommender.recommend(careers, answers)
        except Exception:
            logger.exception("Career recommendation failed")
            raise HTTPException(status_code=502, detail=RECOMMEND_FAILED)

        if not picks:
            raise HTTPException(status_code=502, detail=RECOMMEND_FAILED)

        by_slug = {c.slug: c for c in careers}

        return {
            "recommendations": [
                {"career": by_slug[p["slug"]], "reason": p["reason"]}
                for p in picks
            ]
        }
