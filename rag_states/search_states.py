from typing import Dict, Any

from pydantic import BaseModel, Field

from dto import git_file_dto


class VectorStoreSearchResult(BaseModel):
    """
    Single search result
    """

    text: str = Field(description="Result text content")
    score: float = Field(description="Similarity score")
    metadata: Dict[str, Any] = Field(description="Result metadata", default_factory=dict)


class VectorStoreSearchResults(BaseModel):
    """
    RAG search response
    """

    results: list[VectorStoreSearchResult] = Field(description="Search results")


class PossibleFilesEntrypoints(BaseModel):
    """
    Possible entrypoints
    """

    files: list[git_file_dto.GitFileInDB] = Field(description="List of paths")
    paths_list: list[str] = Field(description="List of all code paths")
