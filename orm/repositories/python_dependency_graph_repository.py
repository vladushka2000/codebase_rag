from typing import Optional, List

from sqlalchemy import select

from bases.orm_repositories import base_python_dependency_graph_repository
from dto import python_dependency_graph_node_dto
from orm.models import python_dependency_graph_orm
from orm.repositories import base_repository


class PythonDependencyGraphRepository(
    base_python_dependency_graph_repository.BasePythonDependencyGraphRepository,
    base_repository.BaseAlchemyRepository
):
    """
    Repository for python dependency graph entity
    """

    async def batch_create(
        self,
        nodes: List[python_dependency_graph_node_dto.PythonDependencyGraphNode],
    ) -> List[python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
        """
        Create multiple nodes in DB
        :param nodes: list of nodes to create
        :return: nodes with corresponding ids
        """

        db_objs = [
            python_dependency_graph_orm.PythonDependencyGraphORM(
                file_id=obj.file_id,
                parent_id=obj.parent_id,
            )
            for obj in nodes
        ]

        async with self.pg_client.session() as session:
            session.add_all(db_objs)

            await session.flush()

            for db_obj in db_objs:
                await session.refresh(db_obj)

            await session.commit()

            return [
                python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB(
                    id=db_obj.id,
                    file_id=db_obj.file_id,
                    parent_id=db_obj.parent_id,
                )
                for db_obj in db_objs
            ]


    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
        """
        Get list of nodes
        :param limit: number of files to return
        :param offset: offset of files to return
        :return: nodes
        """

        async with self.pg_client.session() as session:
            query = select(python_dependency_graph_orm.PythonDependencyGraphORM)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            db_objs = await session.execute(query)
            db_objs = db_objs.scalars().all()

            return [
                python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB(
                    id=db_obj.id,
                    file_id=db_obj.file_id,
                    parent_id=db_obj.parent_id,
                )
                for db_obj in db_objs
            ]
