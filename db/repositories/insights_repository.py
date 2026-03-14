import uuid
from typing import Optional, List

from sqlalchemy import select, func

from bases.repositories import base_insights_repository, base_alchemy_repository
from dto import insight_dto
from db.orm_models import insight_orm
from utils import const


class InsightsRepository(
    base_insights_repository.BaseInsightsRepository,
    base_alchemy_repository.BaseAlchemyRepository
):
    """
    Repository for insight entity
    """

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[insight_dto.InsightInDB]:
        """
        Get list of insights
        :param limit: number of insights to return
        :param offset: offset of insights to return
        :return: files
        """

        async with self.pg_client.session() as session:
            query = select(insight_orm.InsightORM)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            db_objs = await session.execute(query)
            db_objs = db_objs.scalars().all()

            return [
                insight_dto.InsightInDB(
                    id=db_obj.id,
                    content=db_obj.content,
                    insight_type=db_obj.insight_type,
                    severity=db_obj.severity,
                    confidence=db_obj.confidence,
                )
                for db_obj in db_objs
            ]

    async def batch_create(
        self,
        insights: List[insight_dto.Insight],
    ) -> List[insight_dto.InsightInDB]:
        """
        Create insights
        :param insights: list of insights
        :return: list of insights as db objects
        """

        db_objs: list[insight_orm.InsightORM] = []

        for insight in insights:
            db_objs.append(
                insight_orm.InsightORM(
                    content=insight.content,
                    insight_type=insight.insight_type.value,
                    severity=insight.severity.value,
                    confidence=insight.confidence,
                )
            )

        async with self.pg_client.session() as session:
            session.add_all(db_objs)
            await session.flush()

            for db_obj in db_objs:
                await session.refresh(db_obj)

            await session.commit()

            return [
                insight_dto.InsightInDB(
                    id=db_obj.id,
                    content=db_obj.content,
                    insight_type=const.InsightType(db_obj.insight_type),
                    severity=const.InsightSeverity(db_obj.severity),
                    confidence=db_obj.confidence,
                )
                for db_obj in db_objs
            ]

    async def get_count(self) -> int:
        """
        Get count of all insights
        :return: insights count
        """

        async with self.pg_client.session() as session:
            query = select(func.count(insight_orm.InsightORM.id))
            result = await session.execute(query)

            return result.scalar()
