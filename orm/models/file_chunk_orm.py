import uuid

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Column, Integer, UUID as SA_UUID, String

from orm.models import base_model_orm


class FileChunkORM(base_model_orm.Base):
    """
    Embedded file chunk ORM model
    """

    __tablename__ = "file_chunks"

    id = Column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id",
    )
    path = Column(String, nullable=False)
    location = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(VECTOR(384))
