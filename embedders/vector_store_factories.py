from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from bases import base_alchemy_pg_client
from config import ai_config

ai_config_ = ai_config.AIConfig()


async def create_file_vector_store(
    pg_client: base_alchemy_pg_client.BaseAlchemyPGClient,
    ollama_url: str,
) -> PGVectorStore:
    """
    Create Postgres Vector Store for files embeddings
    :param pg_client: postgres client
    :param ollama_url: ollama url
    :return: Postgres Vector Store instance
    """

    embeddings = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ollama_url
    )
    engine = PGEngine.from_engine(engine=pg_client.engine)

    vector_store = await PGVectorStore.create(
        engine=engine,
        table_name="embed_chunks",
        embedding_service=embeddings,
        id_column="id",
        content_column="content",
        embedding_column="embedding",
        metadata_columns=[
            "file_id",
            "chunk_index",
        ],
    )

    return vector_store


async def create_insight_vector_store(
    pg_client: base_alchemy_pg_client.BaseAlchemyPGClient,
    ollama_url: str,
) -> PGVectorStore:
    """
    Create Postgres Vector Store for insight embeddings
    :param pg_client: postgres client
    :param ollama_url: ollama url
    :return: Postgres Vector Store instance
    """

    embeddings = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ollama_url
    )
    engine = PGEngine.from_engine(engine=pg_client.engine)

    vector_store = await PGVectorStore.create(
        engine=engine,
        table_name="embed_chunks",
        embedding_service=embeddings,
        id_column="id",
        content_column="content",
        embedding_column="embedding",
        metadata_columns=[
            "chunk_index",
        ],
    )

    return vector_store
