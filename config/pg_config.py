from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    """
    Postgres connection settings
    """

    user: str = Field(
        alias="POSTGRES_USER",
        description="Postgres user name",
        default="admin",
    )
    password: str = Field(
        alias="POSTGRES_PASSWORD",
        description="Postgres user password",
        default="admin",
    )
    host: str = Field(
        alias="POSTGRES_HOST",
        description="Postgres host",
        default="localhost",
    )
    port: int = Field(
        alias="POSTGRES_PORT",
        description="Postgres port",
        default=5432,
    )
    db_name: str = Field(
        alias="POSTGRES_DB",
        description="Postgres database name",
        default="codebase_rag",
    )
    connection_pool_size: int = Field(
        alias="POOL_SIZE",
        description="Postgres pool size",
        default=10,
    )

    @property
    def postgres_dsn(self) -> PostgresDsn:
        """
        Get Postgres dsn
        :return: dsn
        """

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.db_name,
        )
