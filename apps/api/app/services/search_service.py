"""One search box for the whole app.

Looks a few words up across the learner's own roadmaps, tasks, lessons,
documents and mentor chats, and the shared careers and resource library. It is
a single database query (one round trip) that joins the sources with UNION ALL,
because each trip to the database is the slow part of a request.

Everything personal is filtered by the learner's profile, so one learner never
sees another's titles.
"""
from uuid import UUID

from sqlalchemy import String, cast, func, literal, null, select, union_all
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import Career
from app.models.document import Document
from app.models.library import LibraryResource
from app.models.mentor_conversation import MentorConversation
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit

MIN_LENGTH = 2
MAX_LENGTH = 100
PER_KIND = 5

# The order the kinds are shown in.
KINDS = ["roadmap", "task", "lesson", "career", "resource", "document", "conversation"]


def like_pattern(query: str) -> str:
    """"50%" must search for a literal percent sign, not everything."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    return f"%{escaped}%"


def result_url(kind: str, row) -> str:
    """Where clicking a result goes."""
    if kind == "roadmap":
        return f"/roadmaps/{row.id}"

    if kind == "task":
        return f"/roadmaps/{row.roadmap_id}/task/{row.id}"

    if kind == "lesson":
        return f"/roadmaps/{row.roadmap_id}/task/{row.task_id}/learn/{row.id}"

    if kind == "career":
        return f"/careers/{row.slug}"

    if kind == "resource":
        return f"/resources?q={row.title}"

    if kind == "document":
        return f"/resume?d={row.id}"

    return f"/mentor?c={row.id}"


def _uuid_null():
    return cast(null(), PG_UUID(as_uuid=True))


def _text_null():
    return cast(null(), String)


def _columns(kind, id_, title, subtitle=None, roadmap_id=None, task_id=None, slug=None):
    """Every source returns the same columns so they can be stacked."""
    return (
        literal(kind).label("kind"),
        id_.label("id"),
        title.label("title"),
        (subtitle if subtitle is not None else _text_null()).label("subtitle"),
        (roadmap_id if roadmap_id is not None else _uuid_null()).label("roadmap_id"),
        (task_id if task_id is not None else _uuid_null()).label("task_id"),
        (slug if slug is not None else _text_null()).label("slug"),
    )


class SearchService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, auth_user_id: UUID, query: str) -> list[dict]:
        query = (query or "").strip()[:MAX_LENGTH]

        if len(query) < MIN_LENGTH:
            return []

        profile_id = (
            await self.db.execute(
                select(Profile.id).where(Profile.auth_user_id == auth_user_id)
            )
        ).scalar_one_or_none()

        if profile_id is None:
            return []

        like = like_pattern(query)

        def mine(select_stmt, order):
            return select_stmt.order_by(order).limit(PER_KIND).subquery()

        sources = [
            mine(
                select(
                    *_columns("roadmap", Roadmap.id, Roadmap.title, cast(Roadmap.status, String))
                )
                .where(Roadmap.profile_id == profile_id, Roadmap.title.ilike(like, escape="\\")),
                Roadmap.updated_at.desc(),
            ),
            mine(
                select(
                    *_columns(
                        "task", RoadmapTask.id, RoadmapTask.title, Roadmap.title, roadmap_id=Roadmap.id
                    )
                )
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(Roadmap.profile_id == profile_id, RoadmapTask.title.ilike(like, escape="\\")),
                RoadmapTask.updated_at.desc(),
            ),
            mine(
                select(
                    *_columns(
                        "lesson", TaskLearningUnit.id, TaskLearningUnit.title, RoadmapTask.title,
                        roadmap_id=Roadmap.id, task_id=RoadmapTask.id,
                    )
                )
                .join(RoadmapTask, RoadmapTask.id == TaskLearningUnit.task_id)
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(Roadmap.profile_id == profile_id, TaskLearningUnit.title.ilike(like, escape="\\")),
                TaskLearningUnit.updated_at.desc(),
            ),
            mine(
                select(*_columns("career", Career.id, Career.name, Career.category, slug=Career.slug))
                .where(
                    Career.is_active.is_(True),
                    Career.name.ilike(like, escape="\\") | Career.slug.ilike(like, escape="\\"),
                ),
                Career.name.asc(),
            ),
            mine(
                select(*_columns("resource", LibraryResource.id, LibraryResource.title, LibraryResource.provider))
                .where(LibraryResource.is_active.is_(True), LibraryResource.title.ilike(like, escape="\\")),
                LibraryResource.title.asc(),
            ),
            mine(
                select(*_columns("document", Document.id, Document.title, cast(Document.kind, String)))
                .where(Document.profile_id == profile_id, Document.title.ilike(like, escape="\\")),
                Document.updated_at.desc(),
            ),
            mine(
                select(*_columns("conversation", MentorConversation.id, MentorConversation.title))
                .where(
                    MentorConversation.profile_id == profile_id,
                    MentorConversation.title.ilike(like, escape="\\"),
                ),
                MentorConversation.updated_at.desc(),
            ),
        ]

        rows = (
            await self.db.execute(union_all(*[select(source) for source in sources]))
        ).all()

        order = {kind: index for index, kind in enumerate(KINDS)}
        rows.sort(key=lambda row: order[row.kind])

        return [
            {
                "kind": row.kind,
                "id": row.id,
                "title": row.title,
                "subtitle": row.subtitle,
                "url": result_url(row.kind, row),
            }
            for row in rows
        ]
