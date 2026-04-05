import asyncio
from typing import AsyncGenerator

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http.models import VectorParams, Distance

from bases.repositories import base_insights_repository
from config import ai_config, pg_config, qdrant_config
from db.repositories import insights_repository, qdrant_repository
from clients import alchemy_pg_client, qdrant_client
from dto import insight_dto
from factories import vector_store_factories

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()
qdrant_config_ = qdrant_config.QdrantConfig()


async def _get_insights(
    repo: base_insights_repository.BaseInsightsRepository,
    limit: int,
) -> AsyncGenerator[
    list[insight_dto.InsightInDB],
]:
    """
    Get insights from DB
    :param repo: insight repository
    :return: list of insights
    """

    offset = 0
    insights_count = await repo.get_count()

    while offset < insights_count:
        insights = await repo.list(
            limit=limit,
            offset=offset,
        )
        offset += limit

        yield insights


def _split_insight(
    splitter: RecursiveCharacterTextSplitter,
    insight: insight_dto.InsightInDB,
    chunk_size: int,
) -> list[Document]:
    """
    Split insight by chunks
    :param splitter: text splitter
    :param insight: insight data
    :param chunk_size: chunk size
    :return: chunks
    """

    if len(insight.content) <= chunk_size:
        doc_dict = insight.to_embedding_document(
            chunk_index=0,
            total_chunks=1,
            chunk_content=insight.content,
        )

        return [
            Document(
                page_content=doc_dict["text"],
                metadata=doc_dict["metadata"]
            )
        ]

    chunks = splitter.split_text(insight.content)
    documents = []

    for i, chunk in enumerate(chunks):
        doc_dict = insight.to_embedding_document(
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


async def embed_insights() -> None:
    """
    Embed all insights
    """

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )
    qdrant_client_ = qdrant_client.QdrantClient()

    await pg_client.connect()
    qdrant_client_.connect()

    insights_repo = insights_repository.InsightsRepository(pg_client)
    qdrant_repo = qdrant_repository.QdrantRepository(qdrant_client_)

    if not qdrant_repo.is_collection_exists(qdrant_config_.insights_collection):
        qdrant_repo.create_collection(
            qdrant_config_.insights_collection,
            VectorParams(
                size=ai_config_.embedder_chunk_size,
                distance=Distance.COSINE,
            )
        )

    embedder = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ai_config_.ollama_url
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=ai_config_.embedder_chunk_size,
        chunk_overlap=ai_config_.embedder_chunk_overlap,
    )
    insights_vector_store = vector_store_factories.create_vector_store(
        qdrant_client=qdrant_client_.client,
        embeddings=embedder,
        collection_name=qdrant_config_.insights_collection,
    )

    async for insights in _get_insights(repo=insights_repo, limit=50):
        for insight in insights:
            chunks = _split_insight(
                splitter=splitter,
                insight=insight,
                chunk_size=ai_config_.embedder_chunk_size,
            )
            insights_vector_store.add_documents(chunks)

    await pg_client.disconnect()
    qdrant_client_.disconnect()
    insights_vector_store.client.close()


if __name__ == "__main__":
    asyncio.run(embed_insights())
