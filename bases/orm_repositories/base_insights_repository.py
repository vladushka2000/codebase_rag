import abc
from typing import Optional, List

from dto import insight_dto


class BaseInsightsRepository(abc.ABC):
    """
    Base repository for insight entity
    """

    @abc.abstractmethod
    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[insight_dto.InsightInDB]:
        """
        Get list of insights
        :param limit: number of insights to return
        :param offset: offset of insights to return
        :return: insights
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def batch_create(
        self,
        insights: List[insight_dto.Insight],
    ) -> List[insight_dto.InsightInDB]:
        """
        Create insights
        :param insights: list of insights
        :return: list of insights as db objects
        """

        raise NotImplementedError
