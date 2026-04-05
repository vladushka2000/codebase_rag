from pydantic import BaseModel


class InputPrompt(BaseModel):
    """
    User's input prompt
    """

    prompt: str


class SimpleAnswer(BaseModel):
    """
    Simple LLM answer
    """

    answer: str
