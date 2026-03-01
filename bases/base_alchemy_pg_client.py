import abc
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    async_scoped_session
)


class BaseAlchemyPGClient(abc.ABC):
    """
    Base SQLAlchemy Postgresql client
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10
    ):
        """
        Init variables
        :param database_url: database url
        :param echo: echo mode
        :param pool_size: connections pool size
        :param max_overflow: max count of additional connections
        """

        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._scoped_session: Optional[async_scoped_session] = None

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @abc.abstractmethod
    async def connect(self) -> None:
        """
        Init db connection
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """
        Close db connection
        """

        raise NotImplementedError

    @asynccontextmanager
    @abc.abstractmethod
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Init alchemy session
        :return: session
        """

        raise NotImplementedError
