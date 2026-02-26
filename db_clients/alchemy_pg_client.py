import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session
)


class AlchemyPGClient:
    """
    SQLAlchemy Postgresql client
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

    async def connect(self) -> None:
        """
        Init db connection
        """

        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

        self._scoped_session = async_scoped_session(
            self._session_factory,
            scopefunc=asyncio.current_task
        )

    async def disconnect(self) -> None:
        """
        Close db connection
        """

        if self._engine is None:
            return

        if self._scoped_session is not None:
            await self._scoped_session.close()
            self._scoped_session = None

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Init alchemy session
        :return: session
        """

        if self._session_factory is None:
            raise RuntimeError("Init session factory")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
