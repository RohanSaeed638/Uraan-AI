OUTLINE_PROMPT = """
You are an expert instructor planning the lessons for ONE roadmap task.
This step produces the OUTLINE only; each lesson is written in full later.

LEARNER

Career: {career}
Skill level: {skill}
Goal: {learning_goal}
Study time per day: {daily_hours} hours
Learning style: {style_label}
{learner_context}

TASK

Title: {task_title}
Description: {task_description}
Estimated total time: {task_hours} hours
Reference links already attached to the task: {resource_links}

WHAT TO PRODUCE

Split the task over as many days as the study time per day and the estimated
total time need (days numbered 1, 2, 3 with no gaps). Each day holds a few
lessons whose minutes add up to roughly the daily study time. Start with
fundamentals and move toward practice. Do not assume knowledge beyond the
learner's skill level. Every lesson must directly support this task, with no
filler and no overlap between lessons.

Lesson types you may use: {allowed_types}

{type_rules}

Never invent URLs. Only video links go in "video_urls", and only if you are
confident the exact video exists.

RETURN ONLY VALID JSON in this shape (no markdown fences):

{{
  "units": [
    {{
      "day": 1,
      "order": 1,
      "type": "reading",
      "title": "",
      "description": "one sentence on what the learner gets from this",
      "outline": ["a point this lesson must cover", "another point"],
      "notes": null,
      "video_urls": [],
      "search_query": null,
      "estimated_minutes": 30
    }}
  ]
}}
"""

READING_RULES = """READING lessons ("type": "reading"):
- "outline": 4 to 7 specific points the lesson must teach, in teaching order.
- "notes" is null, "video_urls" is [] and "search_query" is null."""

VIDEO_RULES = """VIDEO lessons ("type": "video"):
- At most one video per day, only where a video genuinely helps. Videos are
  supplementary: the day must still make sense without them.
- "video_urls": up to 2 YouTube watch links (https://www.youtube.com/watch?v=...)
  to well-known, high-quality videos on exactly this topic, ONLY if you are
  confident they exist. Otherwise [].
- "search_query": a specific phrase that finds a good video if the links are
  unavailable, e.g. "git branching explained for beginners". Always provide it.
- "description": what to watch for and what to take away.
- "notes": 2 to 4 sentences in Markdown to follow along with.
- "outline" is []."""

PROJECT_RULES = """PROJECT lesson ("type": "project"):
- Exactly ONE project, on the last day, that applies what the task teaches and
  is doable in the minutes given.
- "outline": 4 to 6 points: what to build, the main requirements, and the
  skills it practises.
- Add these keys to the project unit only: "difficulty": "beginner", "intermediate" or "advanced", for THIS learner.
- "skills": 2 to 5 short skill names the project practises.
- "portfolio_value": one sentence on what an employer or client learns about
  the learner from seeing this project.
- "notes" is null, "video_urls" is [] and "search_query" is null."""

EXERCISE_RULES = """EXERCISE lessons ("type": "exercise"): a small coding problem the
learner solves themselves, with starter code.
- Use 1 to 3 per task (never more than 3), at most one per day, placed after
  the reading that teaches what the problem needs. Not every day needs one.
- Add the key "language" to exercise units only: the language the exercise is
  written in, lower case ("python", "javascript", "sql", "bash").
- "outline": 2 to 4 points: what the problem asks and the idea it practises.
- "estimated_minutes": 10 to 40.
- "notes" is null, "video_urls" is [] and "search_query" is null."""

STYLE_LABELS = {
    "reading": "reading only",
    "reading_video": "reading and videos",
    "reading_video_project": "reading, videos and a hands-on project",
}


def rules_for(style: str, coding: bool = False) -> str:
    parts = [READING_RULES]

    if coding:
        parts.append(EXERCISE_RULES)

    if style in ("reading_video", "reading_video_project"):
        parts.append(VIDEO_RULES)

    if style == "reading_video_project":
        parts.append(PROJECT_RULES)

    return "\n\n".join(parts)


READING_PROMPT = """
Write one complete lesson for a learner. They will study only from your text.

Task: {task_title}
Lesson: {title}
What this lesson is for: {description}
Skill level: {skill}   Career: {career}   Time: about {minutes} minutes

Cover these points, in this order:
{outline}

The other lessons in this task (do not repeat them, build on earlier ones):
{siblings}

Requirements:
- Markdown, {target}+ words, at most 700.
- Begin with a short intro on why this matters. Use "##" headings for the
  sections. Give concrete examples, with fenced code blocks when the topic
  involves code or commands. Explain terms the first time you use them.
- End with "## Key takeaways" (bullets) and "## Check yourself" (2 or 3
  questions answerable from the lesson).
- Only Markdown headings, lists, **bold**, `inline code`, fenced code blocks,
  > quotes and [text](https://...) links to official documentation you are
  sure exists. No tables, no images.
- Be accurate. Leave out anything you are unsure of.

Output only the lesson, with no preamble.
"""

PROJECT_PROMPT = """
Write the brief for a hands-on project that ends this task. The learner builds
it themselves.

Task: {task_title}
Project: {title}
What it is for: {description}
Skill level: {skill}   Career: {career}   Time: about {minutes} minutes

It should cover:
{outline}

Requirements:
- Markdown with exactly these "##" sections, in this order:
  1. Goal
  2. Requirements (a checklist of "- [ ]" items)
  3. Steps (numbered hints, not full solutions)
  4. What to submit
  5. Stretch goal
- {target}+ words, at most 500. Make requirements specific and checkable.
- No invented links.

Output only the brief, with no preamble.
"""

EXPAND_NOTE = (
    "\n\nYour previous answer was too short ({words} words). Write the full "
    "lesson again with more depth and more examples, at least {target} words."
)

EXERCISE_PROMPT = """
Write one coding exercise for a learner. They solve it on their own computer
(or in an online editor); nothing is run for them, so it must be unambiguous.

Task: {task_title}
Exercise: {title}
What it is for: {description}
Language: {language}
Skill level: {skill}   Career: {career}   Time: about {minutes} minutes

It should practise:
{outline}

Return ONLY valid JSON, no markdown fences:

{{
  "language": "{language}",
  "problem": "Markdown. State exactly what to write, the inputs and outputs, and one or two worked examples. 40 to 150 words.",
  "starter_code": "Code with the structure already there and the part to write left as a clearly marked TODO. It must be valid {language}.",
  "hints": ["a gentle nudge", "a more specific one", "almost the answer, without the code"],
  "solution": "A complete, correct, readable solution that keeps the starter code structure.",
  "expected_output": "What running the solution prints for the example, or null."
}}

Rules:
- 2 to 4 hints, each more revealing than the one before. Hints are plain text.
- The solution must really solve the problem as stated. If you are unsure it is
  correct, make the problem simpler.
- Use only the standard library of the language. No installs, no network, no
  files, no input from the keyboard.
- Fit the time given: a small, focused problem, not a project.
"""
