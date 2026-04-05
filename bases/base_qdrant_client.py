import abc
from contextlib import contextmanager
from typing import Optional, Generator

from qdrant_client import QdrantClient

from bases import base_db_client


class BaseQdrantClient(base_db_client.BaseDBClient):
    """
    Base qdrant client
    """

    def __init__(self):
        """
        Init variables
        """

        self._client: Optional[QdrantClient] = None

    @property
    @abc.abstractmethod
    def client(self) -> QdrantClient:
        """
        Get qdrant client
        """

        raise NotImplementedError

    @abc.abstractmethod
    def connect(self) -> None:
        """
        Connect to qdrant
        """

        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect from qdrant
        """

        raise NotImplementedError

    @contextmanager
    @abc.abstractmethod
    def session(self) -> Generator[QdrantClient, None]:
        """
        Get qdrant session
        :return: qdrant session
        """

        raise NotImplementedError
