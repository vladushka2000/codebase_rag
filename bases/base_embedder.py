import abc

from langchain_postgres import PGVectorStore


class BaseEmbedder(abc.ABC):
    """
    Base embedder
    """

    def __init__(
        self,
        vector_store: PGVectorStore,
    ):
        """
        Init variables
        :param vector_store: postgres vector store
        """

        self.vector_store = vector_store
        self.embeddings = vector_store.embeddings
        self.engine = getattr(vector_store, "engine", None)

    @abc.abstractmethod
    async def embed(self, *args,**kwargs,) -> None:
        raise NotImplementedError
