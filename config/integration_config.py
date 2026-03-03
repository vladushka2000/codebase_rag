from pydantic import Field
from pydantic_settings import BaseSettings


class IntegrationConfig(BaseSettings):
    """
    Integration settings
    """

    repo_name: str = Field(
        description="Repository name",
        default="repo",
    )
    owner_name: str = Field(
        description="Repository owner name",
        default="owner",
    )
    token: str = Field(
        description="Git token",
        default="token",
    )
