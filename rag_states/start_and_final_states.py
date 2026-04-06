from pydantic import BaseModel


class InputPrompt(BaseModel):
    """
    User's input prompt
    """

    prompt: str
    key_words: list[str]


class RAGAnswer(BaseModel):
    """
    RAG-system answer
    """

    answer: str
    used_paths: list[str]
