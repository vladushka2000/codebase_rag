from qdrant_client import models

from bases.repositories import base_qdrant_repository


class QdrantRepository(base_qdrant_repository.BaseQdrantRepository):
    """
    Qdrant repository
    """

    def is_collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists
        :param collection_name: collection name
        :return: True if collection exists else False
        """

        with self.qdrant_client.session() as client:
            collections = client.get_collections()

            return any(c.name == collection_name for c in collections.collections)

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

        with self.qdrant_client.session() as client:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                **kwargs
            )

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete collection
        :param collection_name: collection name
        """

        with self.qdrant_client.session() as client:
            client.delete_collection(collection_name)
