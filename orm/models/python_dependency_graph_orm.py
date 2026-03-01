import uuid

from sqlalchemy import UUID as SA_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from config import app_config
from orm.models import base_model_orm

app_config_ = app_config.AppConfig()


class PythonDependencyGraphORM(base_model_orm.Base):
    """
    Python dependency graph ORM model
    """

    __tablename__ = "python_dependency_graph"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Id",
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        ForeignKey("files.id"),
        comment="Child file id"
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        ForeignKey("files.id"),
        comment="Parent file id"
    )
