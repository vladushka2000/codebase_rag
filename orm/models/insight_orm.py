import datetime
import uuid
from typing import List, Optional

from sqlalchemy import Text, DateTime, JSON, Enum as SA_Enum, Float, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from config import ai_config
from orm.models import base_model_orm
from utils import const

ai_config_ = ai_config.AIConfig()


class InsightORM(base_model_orm.Base):
    """
    Project insights ORM
    """

    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id"
    )
    file_ids: Mapped[List[uuid.UUID]] = mapped_column(
        JSON,
        nullable=False,
        comment="List of related file"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Insight text"
    )
    insight_type: Mapped[const.InsightType] = mapped_column(
        SA_Enum(
            const.InsightType,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        comment="Insight type"
    )
    severity: Mapped[const.InsightSeverity] = mapped_column(
        SA_Enum(
            const.InsightSeverity,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        comment="Insight severity"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        comment="Creation time"
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score [0-1]"
    )
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        server_default=f"""
            to_tsvector('{ai_config_.language}', {content})
        """,
        comment="Full-text search vector",
    )

    __table_args__ = (
        Index(
            "idx_insights_search_vector",
            "search_vector",
            postgresql_using="gin"
        ),
    )
