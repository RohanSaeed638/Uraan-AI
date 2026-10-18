OUTLINE_PROMPT = """
You are an expert instructor planning the lessons for ONE roadmap task.
This step produces the OUTLINE only; each lesson is written in full later.

LEARNER

Career: {career}
Skill level: {skill}
Goal: {learning_goal}
Study time per day: {daily_hours} hours
Learning style: {style_label}

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
- "notes" is null, "video_urls" is [] and "search_query" is null."""

STYLE_LABELS = {
    "reading": "reading only",
    "reading_video": "reading and videos",
    "reading_video_project": "reading, videos and a hands-on project",
}


def rules_for(style: str) -> str:
    parts = [READING_RULES]

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
