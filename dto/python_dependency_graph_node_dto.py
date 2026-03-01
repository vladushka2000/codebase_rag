import uuid

from pydantic import BaseModel, Field


class PythonDependencyGraphNode(BaseModel):
    """
    Python dependency graph node
    """

    file_id: uuid.UUID = Field(description="Child file id")
    parent_id: uuid.UUID = Field(description="Parent file id")


class PythonDependencyGraphNodeInDB(PythonDependencyGraphNode):
    """
    Python dependency graph node as DB object
    """

    id: uuid.UUID = Field(description="Id in DB")
