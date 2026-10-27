ROADMAP_ADAPT_PROMPT = """
You are an expert career mentor. A learner is part-way through a roadmap and
needs the REST of it re-planned. Their finished work stays exactly as it is.

Learner

Name: {name}
Career: {career}
Career stage: {career_stage}
Skill level: {skill}
Goal: {learning_goal}
Learning style: {learning_style}
Study time per day: {daily_hours} hours
Time left: about {months_left} months ({weeks_left} weeks)

{learner_context}

{career_template}

Why the plan is changing

{reason}

Already finished (do NOT teach these again)

{completed}

Planned but not finished yet (keep what still serves the goal, reword or
reorder it, drop what no longer fits, and add what is missing)

{unfinished}

Write ONLY the remaining roadmap.

- Fit it into the time left at the study time per day. Do not exceed it.
- Start from where the learner is now, not from the beginning.
- Keep a sensible progression and finish with portfolio / job-readiness work
  when the career needs it.
- Every phase has 2 to 4 "milestones": short, concrete outcomes.
- Every task has a "week": the week of THIS remaining plan (1 = next week).
  Weeks must not go backwards and tasks must fall inside their phase's weeks.
- resource_links: only real, well-known URLs (prefer the trusted resources
  above); use [] when unsure. Never invent a URL.

Return ONLY valid JSON, no markdown, no explanation:

{{
  "title": "",
  "description": "",
  "phases": [
    {{
      "title": "",
      "description": "",
      "order": 1,
      "estimated_weeks": 2,
      "milestones": [""],
      "tasks": [
        {{
          "title": "",
          "description": "",
          "difficulty": "easy",
          "resource_links": [],
          "estimated_hours": 5,
          "week": 1
        }}
      ]
    }}
  ]
}}
"""

ADAPT_REASONS = {
    "study_time": "The learner's available study time changed, so the pace "
    "and the amount planned per week must change with it.",
    "behind": "The learner has fallen behind schedule. Make the remaining "
    "plan realistic: trim or merge lower-value tasks and keep the essentials, "
    "rather than just stretching everything.",
    "goal": "The learner's goal changed. Re-aim the remaining plan at the new "
    "goal while keeping the foundations they still need.",
}
