from pydantic import BaseModel, Field


class GitFile(BaseModel):
    """
    Git file metadata
    """

    path: str = Field(title="File path")
    sha: str = Field(title="File hash")
    size: int = Field(title="Size in bytes")
    type: str = Field(title="File extension")
    content: str = Field(title="File content")
