MOTIVATION_PROMPT = """
Write today's short motivational message for a learner. It appears on their
dashboard and in their daily reminder.

{tone}
{language}

Facts about them (use at most two, exactly as given; never add others):
{facts}

Rules:
- At most 35 words, one to three short sentences. Plain text only, no markdown
  and no quotation marks around it.
- Specific to the facts above, not a generic quote.
- Never guilt, shame or pressure. If the streak is 0, be gently welcoming.
- Do not promise results, and do not invent numbers, dates or lessons.

Output only the message.
"""
