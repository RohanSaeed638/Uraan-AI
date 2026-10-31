"""Composite indexes for the queries every page runs.

Postgres does not index a foreign key on its own: before these, the roadmap,
phase, task and lesson lookups scanned whole tables. Declared here, away from
the models, so the list of what is indexed (and why) reads in one place."""
from sqlalchemy import Index

from app.models.ai_request import AiRequest
from app.models.mentor_message import MentorMessage
from app.models.notification import Notification
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit
from app.models.xp_event import XPEvent

# A learner's roadmaps, newest first (the roadmap list and the dashboard).
Index("ix_roadmaps_profile_updated", Roadmap.profile_id, Roadmap.updated_at.desc())

# A roadmap's phases, a phase's tasks, a task's lessons: always read in order.
Index("ix_roadmap_phases_roadmap_order", RoadmapPhase.roadmap_id, RoadmapPhase.order)
Index("ix_roadmap_tasks_phase_order", RoadmapTask.phase_id, RoadmapTask.order)
Index("ix_task_units_task_day_order", TaskLearningUnit.task_id, TaskLearningUnit.day, TaskLearningUnit.order)

# Weekly XP, the leaderboard and streak checks read a learner's recent events.
Index("ix_xp_events_profile_created", XPEvent.profile_id, XPEvent.created_at)

# The notification list (newest first) and the unread count.
Index("ix_notifications_profile_created", Notification.profile_id, Notification.created_at.desc())
Index(
    "ix_notifications_unread",
    Notification.profile_id,
    postgresql_where=Notification.read_at.is_(None),
)

# Daily AI limits per learner and the admin usage numbers by day.
Index("ix_ai_requests_profile_purpose_created", AiRequest.profile_id, AiRequest.purpose, AiRequest.created_at)
Index("ix_ai_requests_created", AiRequest.created_at)

# A conversation's messages in the order they were sent.
Index("ix_mentor_messages_conversation_created", MentorMessage.conversation_id, MentorMessage.created_at)
