"""Turns the onboarding answers into guidance lines for the AI prompts."""

_EDUCATION = {
    "school": "is still in school",
    "college": "is in college",
    "bachelors": "holds a bachelor's degree",
    "masters": "holds a master's degree",
    "self_taught": "is self-taught",
}

_GOAL = {
    "local_job": "get a job with a local company",
    "remote_job": "get a remote job with an international company",
    "freelancing": "earn through freelancing",
    "startup": "build their own startup",
    "study_abroad": "prepare for study abroad",
}

_PACE = {
    "relaxed": "a relaxed pace with room to catch up",
    "steady": "a steady, balanced pace",
    "intensive": "an intensive pace with a fast, demanding schedule",
}


def learner_context(profile) -> str:
    """Extra prompt text from the optional profile answers; '' when none set."""
    lines: list[str] = []

    if profile is None:
        return ""

    if profile.device == "mobile":
        lines.append(
            "- The learner only has a mobile phone. Recommend phone-friendly "
            "resources and browser-based tools. Do NOT require installing "
            "software locally or running a desktop development environment."
        )
    elif profile.device in ("laptop", "desktop"):
        lines.append(f"- The learner has a {profile.device} computer.")

    if profile.education in _EDUCATION or profile.age:
        who = "The learner"
        if profile.age:
            who += f" is {profile.age} years old"
            who += f" and {_EDUCATION[profile.education]}" if profile.education in _EDUCATION else ""
        else:
            who += f" {_EDUCATION[profile.education]}"
        lines.append(f"- {who}. Pitch explanations accordingly.")

    if profile.goal_type in _GOAL:
        lines.append(
            f"- Their goal is to {_GOAL[profile.goal_type]}; favour skills and "
            "projects that serve it."
        )

    if profile.learning_pace in _PACE:
        lines.append(f"- They want {_PACE[profile.learning_pace]}.")

    if profile.weekend_study is False:
        lines.append("- They do not study on weekends; plan for weekdays only.")

    if not lines:
        return ""

    return "Learner context:\n" + "\n".join(lines)
