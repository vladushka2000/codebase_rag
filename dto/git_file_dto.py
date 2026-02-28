import uuid

from pydantic import BaseModel, Field

from utils import const


class GitFile(BaseModel):
    """
    Git file metadata
    """

    path: str = Field(title="File path")
    sha: str = Field(title="File hash")
    size: float = Field(title="Size in bytes")
    type: const.FileType = Field(title="File type")
    content: str = Field(title="File content")


class GitFileInDB(GitFile):
    """
    Git file metadata as DB object
    """

    id: uuid.UUID = Field(title="Id in DB")
