DOCUMENT_PROMPT = """
You are an expert career coach and professional writer helping a learner
in Pakistan and similar markets write a {kind_label}.

{kind_instructions}

CANDIDATE

Name: {name}
Target role: {target_role}
Skill level: {skill}
Learning goal: {learning_goal}

Skills the candidate has worked on (completed roadmap tasks):
{completed_tasks}

Projects the candidate has completed:
{projects}

Details the candidate provided (education, experience, links, contact):
{details}

Job description to tailor for (may be empty):
{job_description}

STRICT RULES

1. Use ONLY the facts above. Never invent employers, job titles, degrees,
   institutions, dates, grades, certifications, numbers or links.
2. Where a needed fact is missing, write a clear placeholder in square
   brackets, for example [Your email], [University name, years].
3. Do not claim experience level beyond the skill level given.
4. Write in plain, confident, honest language. No buzzword padding.
5. Output ONLY the document, in simple Markdown (# for the name, ## for
   sections, - for bullets, **bold** sparingly). No commentary before or
   after, and no code fences.
"""

KIND_LABELS = {
    "resume": "resume",
    "cover_letter": "cover letter",
    "linkedin_summary": "LinkedIn About summary",
}

KIND_INSTRUCTIONS = {
    "resume": (
        "Write a one-page resume with these sections: header (name and "
        "contact placeholders), Summary (2 to 3 lines), Skills, Projects "
        "(each with 1 to 2 bullets describing what was built and the "
        "skills used), Education, and Experience only if the candidate "
        "gave any. Order sections to favor a junior or fresher candidate."
    ),
    "cover_letter": (
        "Write a cover letter of 3 short paragraphs: why this role, "
        "relevant projects and skills, and a polite close. Address it to "
        "[Hiring manager]. If a job description is given, tailor to it "
        "without claiming skills the candidate lacks."
    ),
    "linkedin_summary": (
        "Write a LinkedIn About section of 90 to 140 words in the first "
        "person: who the candidate is, what they are learning and have "
        "built, and what they are looking for. End with one line of "
        "relevant skills."
    ),
}
