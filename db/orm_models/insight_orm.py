import uuid
from typing import List

from sqlalchemy import Text, JSON, Enum as SA_Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from config import ai_config
from db.orm_models import base_model_orm
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
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score [0-1]"
    )
