from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from config import qdrant_config

qdrant_config_ = qdrant_config.QdrantConfig()


def create_vector_store(
    qdrant_client: QdrantClient,
    embeddings: OllamaEmbeddings,
    collection_name: str,
) -> QdrantVectorStore:
    """
    Create Postgres Vector Store for nodes embeddings
    :param qdrant_client: qdrant client
    :param embeddings: embedding model
    :param collection_name: collection name
    :return: qdrant vector store instance
    """

    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embeddings,
    )
