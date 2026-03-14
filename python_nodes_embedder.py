import asyncio
from typing import AsyncGenerator

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from qdrant_client.http.models import VectorParams, Distance

from bases.repositories import base_ast_nodes_repository
from config import ai_config, pg_config, qdrant_config
from db.repositories import ast_nodes_repository, qdrant_repository
from db_clients import alchemy_pg_client, qdrant_client
from dto import ast_node_dto
from factories import vector_store_factories

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()
qdrant_config_ = qdrant_config.QdrantConfig()


async def _get_nodes(
    repo: base_ast_nodes_repository.BaseASTNodesRepository,
    limit: int,
) -> AsyncGenerator[
    list[ast_node_dto.ASTNodeInDB],
]:
    """
    Get nodes from DB
    :param repo: ast repository
    :return: list of nodes
    """

    offset = 0
    nodes_count = await repo.get_count()

    while offset < nodes_count:
        nodes = await repo.list(
            limit=limit,
            offset=offset,
        )
        offset += limit

        yield nodes


def _split_node(
    splitter: RecursiveCharacterTextSplitter,
    node: ast_node_dto.ASTNodeInDB,
    chunk_size: int,
) -> list[Document]:
    """
    Split node by chunks
    :param splitter: text splitter
    :param node: node data
    :param chunk_size: chunk size
    :return: chunks
    """

    if len(node.content) <= chunk_size:
        doc_dict = node.to_embedding_document(
            chunk_index=0,
            total_chunks=1,
            chunk_content=node.content,
        )

        return [
            Document(
                page_content=doc_dict["text"],
                metadata=doc_dict["metadata"]
            )
        ]

    chunks = splitter.split_text(node.content)
    documents = []

    for i, chunk in enumerate(chunks):
        doc_dict = node.to_embedding_document(
            chunk_index=i,
            total_chunks=len(chunks),
            chunk_content=chunk
        )
        doc = Document(
            page_content=doc_dict["text"],
            metadata=doc_dict["metadata"]
        )
        documents.append(doc)

    return documents


async def embed_python_nodes() -> None:
    """
    Embed all python nodes
    """

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )
    qdrant_client_ = qdrant_client.QdrantClient()

    await pg_client.connect()
    qdrant_client_.connect()

    ast_nodes_repo = ast_nodes_repository.ASTNodesRepository(pg_client)
    qdrant_repo = qdrant_repository.QdrantRepository(qdrant_client_)

    if not qdrant_repo.is_collection_exists(qdrant_config_.ast_collection_python):
        qdrant_repo.create_collection(
            qdrant_config_.ast_collection_python,
            VectorParams(
                size=ai_config_.embedder_chunk_size,
                distance=Distance.COSINE,
            )
        )

    embedder = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ai_config_.ollama_url
    )
    python_code_splitter = RecursiveCharacterTextSplitter(
        chunk_size=ai_config_.embedder_chunk_size,
        chunk_overlap=ai_config_.embedder_chunk_overlap,
    ).from_language(language=Language.PYTHON)
    nodes_vector_store = vector_store_factories.create_vector_store(
        qdrant_client=qdrant_client_.client,
        embeddings=embedder,
        collection_name=qdrant_config_.ast_collection_python,
    )

    async for nodes in _get_nodes(repo=ast_nodes_repo, limit=50):
        for node in nodes:
            chunks = _split_node(
                splitter=python_code_splitter,
                node=node,
                chunk_size=ai_config_.embedder_chunk_size,
            )
            nodes_vector_store.add_documents(chunks)

    await pg_client.disconnect()
    qdrant_client_.disconnect()
    nodes_vector_store.client.close()


if __name__ == "__main__":
    asyncio.run(embed_python_nodes())
