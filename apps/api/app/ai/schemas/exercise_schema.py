"""A coding exercise as the AI writes it, checked before it is saved."""
import ast

from pydantic import BaseModel, Field, field_validator

MIN_PROBLEM_WORDS = 25


class ExerciseOutput(BaseModel):
    language: str = Field(min_length=1, max_length=30)
    problem: str
    starter_code: str
    hints: list[str] = Field(min_length=2, max_length=4)
    solution: str
    expected_output: str | None = None

    @field_validator("language")
    @classmethod
    def lower_language(cls, value: str):
        return value.strip().lower()

    @field_validator("problem", "starter_code", "solution")
    @classmethod
    def not_blank(cls, value: str):
        value = value.strip("\n").rstrip()

        if not value.strip():
            raise ValueError("must not be empty")

        return value

    @field_validator("hints")
    @classmethod
    def clean_hints(cls, value: list[str]):
        hints = [h.strip() for h in value if h and h.strip()]

        if len(hints) < 2:
            raise ValueError("needs at least two hints")

        return hints

    def check(self) -> None:
        """Raises ValueError when the exercise is not usable as written."""
        if len(self.problem.split()) < MIN_PROBLEM_WORDS:
            raise ValueError("The problem statement is too short")

        if self.starter_code.strip() == self.solution.strip():
            raise ValueError("The starter code already is the solution")

        # Python is the one language we can check without running it.
        if self.language in ("python", "py"):
            for name, code in (("starter code", self.starter_code), ("solution", self.solution)):
                try:
                    ast.parse(code)
                except SyntaxError as exc:
                    raise ValueError(f"The {name} is not valid Python: {exc.msg}")

    def as_details(self) -> dict:
        return {
            "language": self.language,
            "starter_code": self.starter_code,
            "hints": self.hints,
            "solution": self.solution,
            "expected_output": self.expected_output,
        }
