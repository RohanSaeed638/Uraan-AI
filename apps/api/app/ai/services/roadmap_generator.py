from openai import AsyncOpenAI

from app.core.config import settings

from app.ai.prompts.roadmap_prompt import ROADMAP_PROMPT
from app.ai.prompts.learning_units_prompt import LEARNING_UNITS_PROMPT
from app.ai.parser import parse_ai_json
from app.ai.schemas.roadmap_schema import RoadmapOutput, TaskLearningPlanOutput


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)


class RoadmapGenerator:

    async def generate(
        self,
        profile,
        data
    ) -> RoadmapOutput:

        # prompt = ROADMAP_PROMPT.format(

        #     name=profile.full_name,

        #     career=profile.career_slug,

        #     skill=profile.skill_level,

        #     learning_style=profile.learning_style,

        #     daily_hours=profile.daily_hours,

        #     duration=profile.target_duration,

        # )
        prompt = ROADMAP_PROMPT.format(
            name=profile.full_name,

            career=data.career_slug,

            career_stage=data.career_stage,

            skill=data.skill_level,

            learning_goal=data.learning_goal,

            learning_style=data.learning_style,

            daily_hours=data.daily_hours,

            duration=data.target_duration,
        )

        response = await client.chat.completions.create(

            model="gpt-5.4-nano",

            messages=[
                {
                    "role": "system",
                    "content": "You generate career roadmaps."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.5,
        )

        data = parse_ai_json(
            response.choices[0].message.content
        )

        return RoadmapOutput(**data)

    async def generate_learning_units(
        self,
        profile,
        task,
    ) -> TaskLearningPlanOutput:

        prompt = LEARNING_UNITS_PROMPT.format(
            career=profile.career_slug,
            career_stage=profile.career_stage,
            skill=profile.skill_level,
            learning_goal=profile.learning_goal,
            learning_style=profile.learning_style,
            daily_hours=profile.daily_hours,
            task_title=task.title,
            task_description=task.description,
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
                    "instructor who creates structured learning plans."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.4,
        )

        data = parse_ai_json(
            response.choices[0].message.content
        )

        return TaskLearningPlanOutput(**data)