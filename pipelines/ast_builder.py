import asyncio
from typing import List

from ast_builders import ast_builder_python
from config import pg_config
from db.repositories import ast_nodes_repository, files_repository
from clients import alchemy_pg_client
from dto import ast_node_dto
from utils import const

pg_config_ = pg_config.PostgresConfig()


async def build_ast() -> None:
    """
    Build AST for python-files
    """

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )

    await pg_client.connect()

    files_repo = files_repository.FilesRepository(pg_client)
    ast_nodes_repo = ast_nodes_repository.ASTNodesRepository(pg_client)

    files_ids = await files_repo.get_ids(
        file_type=const.FileType.CODE,
        extension=".py"
    )
    nodes_batch_size = 100
    nodes: List[ast_node_dto.ASTNode] = []

    for file_id in files_ids:
        file = await files_repo.get_by_id(file_id)
        ast_builder = ast_builder_python.ASTBuilderPython(file)
        nodes.extend(ast_builder.extract())

        if len(nodes) == nodes_batch_size:
            await ast_nodes_repo.batch_create(nodes)
            nodes = []

    if nodes:
        await ast_nodes_repo.batch_create(nodes)

    await pg_client.disconnect()


if __name__ == "__main__":
    asyncio.run(build_ast())
