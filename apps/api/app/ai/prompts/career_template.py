"""Turns a curated catalogue career into prompt text for the roadmap AI.

The catalogue (admin-maintained) decides WHAT is taught and which free
resources to prefer; the AI decides the order, pacing and projects.
"""


def career_template(career) -> str:
    """'' when the career is not in the catalogue."""
    if career is None:
        return ""

    skills = "\n".join(
        f"{i}. {s.name}"
        for i, s in enumerate(sorted(career.skills, key=lambda s: s.order_number), 1)
    )
    resources = "\n".join(
        f"- {r.title} ({r.provider or r.type}): {r.url}"
        for r in sorted(career.resources, key=lambda r: r.order_number)
    )

    return (
        f"Curated template for {career.name} "
        f"(about {career.estimated_months} months to job-ready):\n"
        "Skills to cover, in a sensible order:\n"
        f"{skills}\n\n"
        "Trusted free resources. Prefer these for matching tasks and put "
        "their exact URLs in resource_links:\n"
        f"{resources}\n\n"
        "Personalise this template: you may reorder topics, change pacing, "
        "add explanations and suggest projects, and you may add a topic if the "
        "learner's goal needs it, but do not drop a core skill."
    )
