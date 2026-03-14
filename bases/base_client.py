import abc


class BaseClient(abc.ABC):
    """
    Base client
    """

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
