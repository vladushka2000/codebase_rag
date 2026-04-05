from pydantic import BaseModel, Field


class RAGNecessity(BaseModel):
    """
    Is RAG-system required to answer the user's question
    """

    is_required: bool = Field(description="Is RAG-system required")


class FileTraverseInfo(BaseModel):
    """
    File traverse info
    """

    file_valid_score: float = Field(
        description="File score based on how it's content is similar to user's unput",
        ge=0,
        le=1,
    )
    file_snippet: str = Field(description="File snippet")
    potential_paths: list[str] = Field(
        description="List of potential file paths to check next"
    )


class PotentialFilePaths(BaseModel):
    """
    Potential file paths
    """

    paths: list[str]


class RAGAnswer(BaseModel):
    """
    RAG-system answer
    """

    answer: str = Field(description="RAG-system answer")
    used_paths: list[str] = Field(description="List of file references used in answer")
