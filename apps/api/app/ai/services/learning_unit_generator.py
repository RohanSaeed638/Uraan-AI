from collections import defaultdict
from openai import AsyncOpenAI
from app.core.config import settings

from app.ai.prompts.learning_units_prompt import LEARNING_UNITS_PROMPT
from app.schemas.task import (
    LearningUnitOutput,
    TaskLearningPlanOutput,
)
from app.utils.ai import parse_ai_json

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)

class LearningUnitGenerator:

    async def generate(
        self,
        profile,
        task,
    ) -> TaskLearningPlanOutput:

        learning_style = self._normalize_enum(
            profile.learning_style
        )

        career_stage = self._normalize_enum(
            profile.career_stage
        )

        skill = self._normalize_enum(
            profile.skill_level
        )

        prompt = LEARNING_UNITS_PROMPT.format(
            name=profile.full_name or "",
            career=profile.career_slug or "",
            career_stage=career_stage,
            skill=skill,
            learning_goal=profile.learning_goal or "",
            learning_style=learning_style,
            daily_hours=profile.daily_hours,
            task_title=task.title,
            task_description=task.description or "",
            task_difficulty=task.difficulty,
            task_hours=task.estimated_hours,
            resource_links=task.resource_links or [],
        )

        response = await client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert software engineering "
                        "instructor who creates practical learning plans."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
        )

        raw_content = response.choices[0].message.content

        if not raw_content:
            raise ValueError(
                "AI returned an empty learning plan."
            )

        data = parse_ai_json(raw_content)

        result = TaskLearningPlanOutput(
            **data
        )

        self._validate_learning_plan(
            result,
            profile=profile,
            task=task,
        )

        return result

    @staticmethod
    def _normalize_enum(value) -> str:

        if value is None:
            return ""

        if hasattr(value, "value"):
            return str(value.value)

        return str(value).lower()

    @staticmethod
    def _validate_learning_plan(
        plan: TaskLearningPlanOutput,
        profile,
        task,
    ):

        if not plan.learning_units:
            raise ValueError(
                f"No learning units generated for task: {task.title}"
            )

        allowed_types = {
            "reading",
            "video",
            "practice",
            "project",
        }

        for unit in plan.learning_units:

            if unit.type.value not in allowed_types:
                raise ValueError(
                    f"Invalid learning unit type: {unit.type}"
                )

            if unit.day < 1:
                raise ValueError(
                    "Learning unit day must be >= 1"
                )

            if unit.order < 1:
                raise ValueError(
                    "Learning unit order must be >= 1"
                )

            if unit.estimated_minutes <= 0:
                raise ValueError(
                    "Learning unit duration must be > 0"
                )

        # Make sure reading exists.
        has_reading = any(
            unit.type.value == "reading"
            for unit in plan.learning_units
        )

        if not has_reading:
            raise ValueError(
                f"Learning plan for '{task.title}' "
                "must contain at least one reading unit."
            )

        daily_minutes = defaultdict(int)

        for unit in plan.learning_units:
            daily_minutes[unit.day] += (
                unit.estimated_minutes
            )

        max_daily_minutes = int(
            profile.daily_hours * 60
        )

        # Give AI a 15% tolerance.
        allowed_daily_minutes = int(
            max_daily_minutes * 1.15
        )

        for day, minutes in daily_minutes.items():

            if minutes > allowed_daily_minutes:
                raise ValueError(
                    f"Day {day} contains {minutes} minutes "
                    f"but user has approximately "
                    f"{max_daily_minutes} minutes available."
                )

        # Validate total estimated time.
        total_minutes = sum(
            unit.estimated_minutes
            for unit in plan.learning_units
        )

        expected_minutes = int(
            task.estimated_hours * 60
        )

        # Don't require exact equality.
        # AI estimates are approximate.
        lower_bound = int(
            expected_minutes * 0.70
        )

        upper_bound = int(
            expected_minutes * 1.30
        )

        if not (
            lower_bound
            <= total_minutes
            <= upper_bound
        ):
            raise ValueError(
                f"Generated learning plan for '{task.title}' "
                f"contains {total_minutes} minutes, "
                f"while task duration is approximately "
                f"{expected_minutes} minutes."
            )