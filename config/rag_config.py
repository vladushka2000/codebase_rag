from pydantic import Field
from pydantic_settings import BaseSettings


class RAGConfig(BaseSettings):
    """
    RAG settings
    """

    max_results: int = Field(
        default=5,
        description="Maximum number of search results per collection",
    )
    score_threshold: float = Field(
        default=0.6,
        description="Minimum similarity score threshold",
    )
