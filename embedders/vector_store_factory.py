from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from bases import base_alchemy_pg_client


async def create_vector_store(
    pg_client: base_alchemy_pg_client.BaseAlchemyPGClient,
    ollama_url: str,
) -> PGVectorStore:
    """
    Create Postgres Vector Store
    :param pg_client: postgres client
    :param ollama_url: ollama url
    :return: Postgres Vector Store instance
    """

    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large:latest",
        base_url=ollama_url
    )
    engine = PGEngine.from_engine(engine=pg_client.engine)

    vector_store = await PGVectorStore.create(
        engine=engine,
        table_name="file_chunks",
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
