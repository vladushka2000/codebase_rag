import uuid
from typing import Dict, Any

from pydantic import BaseModel, Field

from dto import to_embed_dto
from utils import const


class GitFile(BaseModel, to_embed_dto.ToEmbedDTO):
    """
    Git file metadata
    """

    path: str = Field(title="File path")
    sha: str = Field(title="File hash")
    size: float = Field(title="Size in bytes")
    type: const.FileType = Field(title="File type")
    content: str = Field(title="File content")

    def to_embedding_document(
        self,
        chunk_index: int,
        total_chunks: int,
        chunk_content: str,
    ) -> Dict[str, Any]:
        """
        Transform to embedding document
        """

        return {
            "id": str(uuid.uuid4()),
            "text": chunk_content,
            "metadata": {
                "path": self.path,
                "sha": self.sha,
                "size": self.size,
                "type": self.type.value,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
            }
        }


class GitFileInDB(GitFile):
    """
    Git file metadata as DB object
    """

    id: uuid.UUID = Field(title="Id in DB")
