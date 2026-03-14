import uuid

from sqlalchemy import Text, Enum as SA_Enum, String, Integer, Column, UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column

from config import ai_config
from db.orm_models import base_model_orm
from utils import const

ai_config_ = ai_config.AIConfig()


class ASTNodeORM(base_model_orm.Base):
    """
    AST node ORM
    """

    __tablename__ = "ast_nodes"

    id: Mapped[uuid.UUID] = Column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id",
    )
    file_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="File path"
    )
    object_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Object name"
    )
    type: Mapped[const.ASTNodeType] = mapped_column(
        SA_Enum(
            const.ASTNodeType,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        comment="Object type"
    )
    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Code start line"
    )
    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Code end line"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Insight text"
    )
