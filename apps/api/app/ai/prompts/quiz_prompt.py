QUIZ_PROMPT = """
You are an expert software engineering instructor.

Write a multiple-choice quiz that checks whether a learner has understood
ONE roadmap task.

LEARNER

Career:
{career}

Current Skill Level:
{skill}

TASK

Title:
{task_title}

Description:
{task_description}

LESSONS COVERED

{lesson_titles}

RULES

1. Write exactly {question_count} questions.
2. Every question has exactly 4 options and exactly one correct option.
3. Questions must test understanding of the concepts taught in this task,
   not trivia.
4. Match the learner's skill level.
5. "correct_option" is the zero-based index of the correct option.
6. Spread the correct answers across different positions.
7. "explanation" is one or two sentences saying why the answer is correct.
8. Do not reference the lessons or the quiz itself inside a question.

RETURN ONLY VALID JSON.

Structure:

{{
  "questions": [
    {{
      "question": "",
      "options": ["", "", "", ""],
      "correct_option": 0,
      "explanation": ""
    }}
  ]
}}

JSON ONLY.

NO MARKDOWN.

NO EXPLANATION OUTSIDE THE JSON.
"""
