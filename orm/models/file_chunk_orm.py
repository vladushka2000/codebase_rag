import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, Text, ForeignKey, JSON, Index, UUID as SA_UUID

from orm.models import base_model_orm


class FileChunkORM(base_model_orm.Base):
    __tablename__ = "file_chunks"

    id = Column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id",
    )
    file_id = Column(
        SA_UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        comment="File id"
    )
    chunk_index = Column(Integer, nullable=False, comment="Index of chunk")
    content = Column(Text, nullable=False, comment="Content of chunk")
    embedding = Column(Vector(1024), nullable=False, comment="Embedding of chunk")

    __table_args__ = (
        Index("idx_file_chunks_embedding", "embedding", postgresql_using="ivfflat"),
    )
