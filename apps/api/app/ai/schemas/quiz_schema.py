from pydantic import BaseModel, Field, model_validator


class QuizQuestionOutput(BaseModel):
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option: int = Field(ge=0, le=3)
    explanation: str | None = None

    @model_validator(mode="after")
    def options_are_distinct(self):
        if len({o.strip().lower() for o in self.options}) != len(self.options):
            raise ValueError("Quiz options must be distinct")
        return self


class QuizOutput(BaseModel):
    questions: list[QuizQuestionOutput] = Field(min_length=1)
