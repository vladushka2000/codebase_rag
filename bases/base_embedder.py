import abc

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

from config import ai_config

ai_config_ = ai_config.AIConfig()


class BaseEmbedder(abc.ABC):
    """
    Base embedder
    """

    def __init__(self) -> None:
        """
        Init variables
        """

        self.embeddings = OllamaEmbeddings(model=ai_config_.embedding_model)

    @abc.abstractmethod
    def embed(
        self,
        files_to_embed: list[Document],
        vector_store: QdrantVectorStore,
    ) -> None:
        raise NotImplementedError
