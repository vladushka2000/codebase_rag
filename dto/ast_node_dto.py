import uuid
from typing import Dict, Any

from pydantic import BaseModel, Field

from dto import to_embed_dto
from utils import const


class ASTNode(BaseModel, to_embed_dto.ToEmbedDTO):
    """
    AST node
    """

    file_path: str = Field(description="File path")
    object_name: str = Field(description="Object name")
    type: const.ASTNodeType = Field(description="Object type")
    start_line: int = Field(description="Code start line")
    end_line: int = Field(description="Code end line")
    content: str = Field(description="Insight text")

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
                "file_path": self.file_path,
                "object_name": self.object_name,
                "node_type": self.type.value,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
            }
        }


class ASTNodeInDB(ASTNode):
    """
    AST node as DB object
    """

    id: uuid.UUID = Field(description="Id")
