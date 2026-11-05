from app.models.profile import Profile
from app.models.career import Career
from app.models.roadmap import Roadmap
from .roadmap_phase import RoadmapPhase
from .roadmap_task import RoadmapTask
from .task_learning_unit import TaskLearningUnit
from app.models.mentor_conversation import MentorConversation
from app.models.mentor_message import MentorMessage
from .achievement import Achievement, BossChallenge, UserAchievement
from .quiz import Quiz
from .quiz_question import QuizQuestion
from .quiz_attempt import QuizAttempt
from .resource import Resource
from .career import Career, CareerSkill, CareerResource
from .learning_activity import LearningActivity
# from .learning_session import LearningSession
from .mentor_conversation import MentorConversation
from .mentor_message import MentorMessage
from .profile import Profile
from .task_learning_unit import TaskLearningUnit
from .user_task_progress import UserTaskProgress
from .user_settings import UserSettings
from .xp_event import XPEvent
from .push_subscription import PushSubscription
from .notification import Notification
from .document import Document
from .portfolio import Portfolio, PortfolioProject
from .interview import InterviewSession, InterviewTurn

from .roadmap_version import RoadmapVersion
from .library import LibraryResource, ResourceBookmark, ResourceRating
from .ai_request import AiRequest
from .daily_motivation import DailyMotivation
from .planner import ScheduleOverride, SchedulePreference, ScheduleSnapshot
from .admin import AuditLog, Announcement
from . import indexes  # noqa: F401  (registers the composite indexes)
