# ROADMAP_PROMPT = """
# You are an expert software career mentor.

# Generate a COMPLETE learning roadmap.

# Profile

# Name: {name}

# Career:
# {career}

# Current Skill:
# {skill}

# Learning Style:
# {learning_style}

# Daily Hours:
# {daily_hours}

# Target Duration:
# {duration}

# Return ONLY valid JSON.

# The structure must be

# {{
#   "title":"",
#   "description":"",
#   "phases":[
#       {{
#         "title":"",
#         "description":"",
#         "order":1,
#         "estimated_weeks":2,
#         "tasks":[
#             {{
#                 "title":"",
#                 "description":"",
#                 "difficulty":"easy",
#                 "estimated_hours":5
#             }}
#         ]
#       }}
#   ]
# }}

# No markdown.

# No explanation.

# JSON only.
# """

ROADMAP_PROMPT = """
You are an expert career mentor.

Generate a COMPLETE and personalized learning roadmap based on the user's profile.

Profile

Name:
{name}

Career:
{career}

{career_template}

Career Stage:
{career_stage}

Current Skill Level:
{skill}

Learning Goal:
{learning_goal}

Learning Style:
{learning_style}

Daily Hours Available:
{daily_hours}

Target Duration:
{duration} months

IMPORTANT:

The roadmap must be appropriate for the user's career stage.

If the user is a beginner:
- Start with fundamentals.
- Do not assume prior professional knowledge.
- Build skills progressively.

If the user is a student:
- Focus on building strong foundations.
- Include practical projects.
- Prepare the user for internships and entry-level opportunities.

If the user is job_ready:
- Focus on closing practical skill gaps.
- Include production-level development.
- Include interview preparation.
- Include portfolio and job-readiness tasks.

If the user is a professional:
- Focus on advanced skills.
- Include architecture, scalability, best practices and real-world engineering.

If the user is a career_switcher:
- Focus on transferable skills.
- Build the required technical foundation.
- Include practical projects and job preparation.

The roadmap must respect the user's available daily hours and target duration.

{learner_context}

The roadmap should directly support the user's learning goal.

WEEKS AND MILESTONES

- Every phase has 2 to 4 "milestones": short, concrete outcomes ("Build and
  deploy a REST API"), not topics.
- Every task has a "week": the week of the whole roadmap (1 = first week) in
  which the learner starts it. Weeks must not go backwards, and the tasks of a
  phase must fall inside that phase's weeks. The phases' estimated_weeks
  together should roughly match the target duration.

Return ONLY valid JSON.

The structure must be:

{{
  "title": "",
  "description": "",
  "phases": [
    {{
      "title": "",
      "description": "",
      "order": 1,
      "estimated_weeks": 2,
      "milestones": [
        "What the learner can do by the end of this phase",
        "Another concrete outcome"
      ],
      "tasks": [
        {{
          "title": "",
          "description": "",
          "difficulty": "easy",
          "resource_links": [
            "https://example.com/resource1",
            "https://example.com/resource2"
          ],
          "estimated_hours": 5,
          "week": 1
        }}
      ]
    }}
  ]
}}

No markdown.

No explanation.

JSON only.
"""