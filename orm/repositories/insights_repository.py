import datetime
import uuid
from typing import Optional, List

from sqlalchemy import select

from bases.orm_repositories import base_insights_repository
from dto import insight_dto
from orm.models import insight_orm
from orm.repositories import base_repository
from utils import const


class InsightsRepository(
    base_insights_repository.BaseInsightsRepository,
    base_repository.BaseAlchemyRepository
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
                    file_ids=[
                        id_ for id_ in db_obj.file_ids
                    ],
                    insight_type=db_obj.insight_type,
                    severity=db_obj.severity,
                    created_at=db_obj.created_at,
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
                    file_ids=[str(id_) for id_ in insight.file_ids],
                    content=insight.content,
                    insight_type=insight.insight_type.value,
                    severity=insight.severity.value,
                    created_at=insight.created_at or datetime.datetime.now(datetime.UTC),
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
                    file_ids=[uuid.UUID(id_) for id_ in db_obj.file_ids],  # noqa
                    content=db_obj.content,
                    insight_type=const.InsightType(db_obj.insight_type),
                    severity=const.InsightSeverity(db_obj.severity),
                    created_at=db_obj.created_at,
                    confidence=db_obj.confidence,
                )
                for db_obj in db_objs
            ]
