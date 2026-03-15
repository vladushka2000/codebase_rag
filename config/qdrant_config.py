from pydantic import Field
from pydantic_settings import BaseSettings


class QdrantConfig(BaseSettings):
    """
    Qdrant connection settings
    """

    host: str = Field(
        alias="QDRANT_HOST",
        description="Qdrant host",
        default="localhost",
    )
    http_port: int = Field(
        alias="QDRANT_HTTP_PORT",
        description="Qdrant HTTP port",
        default=6333,
    )
    grpc_port: int = Field(
        alias="QDRANT_GRPC_PORT",
        description="Qdrant grpc port",
        default=6334,
    )

    ast_collection_python: str = Field(
        description="Python AST collection name",
        default="ast_python",
    )
    insights_collection: str = Field(
        description="Insights collection name",
        default="insights",
    )
    docs_collection: str = Field(
        description="Documents collection name",
        default="docs",
    )
