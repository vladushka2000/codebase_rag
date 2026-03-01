import datetime
import uuid
from typing import Optional

from sqlalchemy import UUID as SA_UUID, String, Float, Enum as SA_Enum, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from config import app_config
from orm.models import base_model_orm
from utils import const

app_config_ = app_config.AppConfig()


class FileORM(base_model_orm.Base):
    """
    File ORM model
    """

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id",
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Relative file path",
    )
    sha: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="File hash",
    )
    size_bytes: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="File size in bytes",
    )
    type: Mapped[const.FileType] = mapped_column(
        SA_Enum(const.FileType),
        nullable=False,
        comment="File type",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="File content"
    )
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        server_default=f"""
            to_tsvector('{app_config_.language}', {content})
        """,
        comment="Full-text search vector",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(
            datetime.UTC
        ),
    )

    __table_args__ = (
        Index(
            "idx_files_search_vector",
            "search_vector",
            postgresql_using="gin"
        ),
    )
