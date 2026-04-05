from typing import Any, Dict

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Single search result
    """

    text: str = Field(description="Result text content")
    score: float = Field(description="Similarity score")
    metadata: Dict[str, Any] = Field(description="Result metadata", default_factory=dict)


class RAGResponse(BaseModel):
    """
    RAG search response
    """

    results: list[SearchResult] = Field(description="Search results")
    answer: str = Field(description="Generated answer")


class RAGNecessity(BaseModel):
    """
    Is RAG-system required to answer the user's question
    """

    is_required: bool = Field(description="Is RAG-system required")
