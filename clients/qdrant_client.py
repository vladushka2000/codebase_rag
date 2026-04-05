from contextlib import contextmanager
from typing import Generator

from qdrant_client import QdrantClient as QdrantClient_

from bases import base_qdrant_client
from config import qdrant_config

qdrant_config_ = qdrant_config.QdrantConfig()


class QdrantClient(base_qdrant_client.BaseQdrantClient):
    """
    Qdrant client
    """

    @property
    def client(self) -> QdrantClient_:
        """
        Get qdrant client
        """

        if self._client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        return self._client

    def connect(self) -> None:
        """
        Connect to qdrant
        """

        if self._client is not None:
            return

        self._client = QdrantClient_(
            host=qdrant_config_.host,
            port=qdrant_config_.http_port,
            grpc_port=qdrant_config_.grpc_port,
        )

    def disconnect(self) -> None:
        """
        Disconnect from qdrant
        """

        if self._client is None:
            return

        self._client.close()
        self._client = None

    @contextmanager
    def session(self) -> Generator[QdrantClient_, None]:
        """
        Get qdrant session
        :return: qdrant session
        """

        if self._client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            yield self._client
        except Exception as e:
            raise e
