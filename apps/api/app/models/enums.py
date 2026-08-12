from enum import Enum

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyle(str, Enum):
    VIDEO = "video"
    READING = "reading"
    PROJECT = "project"
    MIXED = "mixed"


class RoadmapStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LessonStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class ResourceType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    DOCUMENTATION = "documentation"
    COURSE = "course"
    BOOK = "book"

class RoadmapStatus(str, Enum):
    GENERATING = "generating"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"

class CareerStage(str, Enum):
    BEGINNER = "beginner"
    JOB_READY = "job_ready"
    STUDENT = "student"
    PROFESSIONAL = "professional"
    CAREER_SWITCHER = "career_switcher"