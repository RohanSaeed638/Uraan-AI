"""Version of each prompt. Bump the number when a prompt changes in a way that
could change what it produces; it is stored with the content it generated and
with every AI request, so output quality can be traced back to a prompt."""

PROMPT_VERSIONS = {
    "roadmap": "roadmap-v3",
    "roadmap_adapt": "roadmap-adapt-v1",
    "lessons": "lessons-v3",
    "quiz": "quiz-v1",
    "document": "document-v1",
    "interview": "interview-v1",
    "portfolio": "portfolio-v1",
    "career": "career-v1",
    "mentor": "mentor-v2",
    "review": "review-v2",
    "motivation": "motivation-v1",
    "planner": "planner-v1",
}


def prompt_version(purpose: str) -> str:
    return PROMPT_VERSIONS[purpose]
