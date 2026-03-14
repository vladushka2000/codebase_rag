import asyncio

from config import pg_config
from db.repositories import files_repository
from db_clients import alchemy_pg_client
from git_clients import github_client

pg_config_ = pg_config.PostgresConfig()


async def fetch_files() -> None:
    """
    Fetch all git files
    """

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )

    await pg_client.connect()


    files_repo = files_repository.FilesRepository(pg_client)
    git_client = github_client.GitHubClient()

    async with git_client() as git:
        async for batch in git.get_files_batch():
            await files_repo.batch_create(batch)

    await pg_client.disconnect()


if __name__ == "__main__":
    asyncio.run(fetch_files())
