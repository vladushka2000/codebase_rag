from pydantic import BaseModel, Field


class RAGNecessity(BaseModel):
    """
    Is RAG-system required to answer the user's question
    """

    is_required: bool = Field(description="Is RAG-system required")
