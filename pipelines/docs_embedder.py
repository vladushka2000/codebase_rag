import asyncio
from logging import getLogger
from typing import AsyncGenerator

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http.models import VectorParams, Distance

from bases.repositories import base_files_repository
from config import ai_config, pg_config, qdrant_config
from db.repositories import files_repository, qdrant_repository
from clients import alchemy_pg_client, qdrant_client
from dto import git_file_dto
from factories import vector_store_factories
from utils import const

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()
qdrant_config_ = qdrant_config.QdrantConfig()

logger = getLogger(__name__)


async def _get_docs(
    repo: base_files_repository.BaseFilesRepository,
    limit: int,
) -> AsyncGenerator[
    list[git_file_dto.GitFileInDB],
]:
    """
    Get docs from DB
    :param repo: files repository
    :return: list of docs
    """

    offset = 0
    docs_count = await repo.get_files_count(file_types=[const.FileType.DOC, const.FileType.UNKNOWN])

    while offset < docs_count:
        nodes = await repo.list(
            file_types=[const.FileType.DOC, const.FileType.UNKNOWN],
            limit=limit,
            offset=offset,
        )
        offset += limit

        yield nodes


def _split_doc(
    splitter: RecursiveCharacterTextSplitter,
    doc: git_file_dto.GitFileInDB,
    chunk_size: int,
) -> list[Document]:
    """
    Split doc by chunks
    :param splitter: text splitter
    :param doc: file object
    :param chunk_size: chunk size
    :return: chunks
    """

    if len(doc.content) <= chunk_size:
        doc_dict = doc.to_embedding_document(
            chunk_index=0,
            total_chunks=1,
            chunk_content=doc.content,
        )

        return [
            Document(
                page_content=doc_dict["text"],
                metadata=doc_dict["metadata"]
            )
        ]

    chunks = splitter.split_text(doc.content)
    documents = []

    for i, chunk in enumerate(chunks):
        doc_dict = doc.to_embedding_document(
            chunk_index=i,
            total_chunks=len(chunks),
            chunk_content=chunk
        )
        document = Document(
            page_content=doc_dict["text"],
            metadata=doc_dict["metadata"]
        )
        documents.append(document)

    return documents


async def embed_docs() -> None:
    """
    Embed all docs
    """

    logger.info("Embedding all docs...")

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )
    qdrant_client_ = qdrant_client.QdrantClient()

    await pg_client.connect()
    qdrant_client_.connect()

    files_repo = files_repository.FilesRepository(pg_client)
    qdrant_repo = qdrant_repository.QdrantRepository(qdrant_client_)

    if not qdrant_repo.is_collection_exists(qdrant_config_.docs_collection):
        qdrant_repo.create_collection(
            qdrant_config_.docs_collection,
            VectorParams(
                size=ai_config_.embedder_chunk_size,
                distance=Distance.COSINE,
            )
        )

    embedder = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ai_config_.ollama_url
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=ai_config_.embedder_chunk_size,
        chunk_overlap=ai_config_.embedder_chunk_overlap,
    )
    docs_vector_store = vector_store_factories.create_vector_store(
        qdrant_client=qdrant_client_.client,
        embeddings=embedder,
        collection_name=qdrant_config_.docs_collection,
    )

    async for documents in _get_docs(repo=files_repo, limit=50):
        for doc in documents:
            logger.info("Splitting %s", doc.path)

            chunks = _split_doc(
                splitter=text_splitter,
                doc=doc,
                chunk_size=ai_config_.embedder_chunk_size,
            )
            docs_vector_store.add_documents(chunks)

            logger.info("%s added to vector store", doc.path)

    await pg_client.disconnect()
    qdrant_client_.disconnect()
    docs_vector_store.client.close()


if __name__ == "__main__":
    asyncio.run(embed_docs())
