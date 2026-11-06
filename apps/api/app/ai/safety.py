"""A light check on what a learner types to the AI mentor, before it is sent to a model.

It does two things and deliberately nothing more:

* A message that looks like an attempt to make the mentor ignore or reveal its instructions is not
  refused (it may be curiosity); the model is just reminded not to comply for that reply.
* A message that suggests the learner may be thinking of harming themselves is not sent to the
  model at all: a person in that moment is better served by a kind, fixed reply pointing to people
  who can help than by whatever a model improvises.

This is a seatbelt and not a wall. The model's own rules (app/ai/prompts/mentor_prompt.py) and the
providers' own moderation do the heavy lifting; keyword lists catch the obvious cases only.
"""
import re
from dataclasses import dataclass

INJECTION = re.compile(
    r"("
    r"(ignore|disregard|forget|override|bypass)\s+(all\s+|any\s+|the\s+|your\s+|these\s+|those\s+)*"
    r"(previous|prior|above|earlier|system|initial|original)?\s*"
    r"(instructions?|rules?|prompts?|guidelines?|restrictions?)"
    r"|(reveal|show|print|repeat|tell\s+me|output|leak)\s+(me\s+)?(your|the)\s+"
    r"(system|hidden|secret|initial|original)\s*(prompt|instructions?|message)"
    r"|what\s+(is|are|were)\s+your\s+(system\s+prompt|instructions)"
    r"|you\s+are\s+now\s+(an?\s+)?(unrestricted|unfiltered|uncensored|jailbroken|evil|no\s+longer\s+bound|free\s+(of|from)\s+(all\s+)?(rules|restrictions))"
    r"|developer\s+mode|jailbreak|\bDAN\b\s+mode|do\s+anything\s+now"
    r")",
    re.IGNORECASE,
)

SELF_HARM = re.compile(
    r"\b("
    r"kill\s+myself|end\s+my\s+life|take\s+my\s+(own\s+)?life|suicid\w*|"
    r"(want|wanna)\s+to\s+die(?!\s+(laughing|of\s+(laughter|embarrassment|boredom|cringe)|from\s+(laughing|embarrassment)))|wanna\s+die|"
    r"better\s+off\s+dead|hurt\s+myself|harm\s+myself|self[-\s]?harm|no\s+reason\s+to\s+live|"
    r"don'?t\s+want\s+to\s+(be\s+alive|live)"
    r")\b",
    re.IGNORECASE,
)

SUPPORT_REPLY = (
    "I am really sorry you are feeling this way, and I am glad you told me. You do not have to go through "
    "it alone.\n\n"
    "Please reach out to someone you trust right now: a family member, a friend, a teacher or a doctor. If you "
    "might act on these thoughts or are in immediate danger, contact your local emergency number or go to the "
    "nearest hospital. A mental health professional or a crisis helpline in your area can also talk with you "
    "straight away.\n\n"
    "I am an AI learning mentor, so I cannot give the help a person can, but I am here to talk, and your "
    "roadmap will be waiting whenever you are ready."
)


@dataclass(frozen=True)
class Screen:
    injection: bool = False
    self_harm: bool = False

    @property
    def blocked(self) -> bool:
        """True when the message must not go to a model."""
        return self.self_harm


def screen_message(text: str) -> Screen:
    return Screen(
        injection=bool(INJECTION.search(text or "")),
        self_harm=bool(SELF_HARM.search(text or "")),
    )
