import uuid

from pydantic import BaseModel, Field


class DependencyGraphNode(BaseModel):
    """
    Dependency graph node
    """

    file_id: uuid.UUID = Field(description="Child file id")
    parent_id: uuid.UUID = Field(description="Parent file id")


class PythonDependencyGraphNodeInDB(DependencyGraphNode):
    """
    Dependency graph node as DB object
    """

    id: uuid.UUID = Field(description="Id in DB")
