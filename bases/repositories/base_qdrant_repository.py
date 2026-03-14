from qdrant_client import models

from bases import base_qdrant_client


class BaseQdrantRepository:
    """
    Base repository for qdrant
    """

    def __init__(self, qdrant_client: base_qdrant_client.BaseQdrantClient) -> None:
        """
        Init variables
        :param qdrant_client: qdrant client
        """

        self.qdrant_client = qdrant_client

    def is_collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists
        :param collection_name: collection name
        :return: True if collection exists else False
        """

        raise NotImplementedError

    def create_collection(
        self,
        collection_name: str,
        vectors_config: models.VectorParams,
        **kwargs
    ) -> None:
        """
        Create collection
        :param collection_name: collection name
        :param vectors_config: vector params
        """

        raise NotImplementedError

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete collection
        :param collection_name: collection name
        """

        raise NotImplementedError
