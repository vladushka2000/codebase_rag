import uuid
from typing import Optional, List

from sqlalchemy import select

from bases.orm_repositories import base_dependency_graph_repository
from dto import dependency_graph_node_dto
from orm.models import python_dependency_graph_orm
from orm.repositories import base_repository


class DependencyGraphRepository(
    base_dependency_graph_repository.BaseDependencyGraphRepository,
    base_repository.BaseAlchemyRepository
):
    """
    Repository for python dependency graph entity
    """

    async def batch_create(
        self,
        nodes: List[dependency_graph_node_dto.DependencyGraphNode],
    ) -> List[dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
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
                dependency_graph_node_dto.PythonDependencyGraphNodeInDB(
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
    ) -> List[dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
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
                dependency_graph_node_dto.PythonDependencyGraphNodeInDB(
                    id=db_obj.id,
                    file_id=db_obj.file_id,
                    parent_id=db_obj.parent_id,
                )
                for db_obj in db_objs
            ]

    async def get_dependencies(self, file_id: uuid.UUID) -> set[uuid.UUID]:
        """
        Get all direct dependencies for a file (what this file imports)
        :param file_id: file id
        :return: set of dependency file ids
        """

        async with self.pg_client.session() as session:
            query = select(
                python_dependency_graph_orm.PythonDependencyGraphORM.parent_id
            ).where(
                python_dependency_graph_orm.PythonDependencyGraphORM.file_id == file_id
            )

            result = await session.execute(query)

            return {row[0] for row in result.all()}

    async def get_dependents(self, file_id: uuid.UUID) -> set[uuid.UUID]:
        """
        Get all files that depend on this file (who imports this file)
        :param file_id: file id
        :return: set of dependent file ids
        """

        async with self.pg_client.session() as session:
            query = select(
                python_dependency_graph_orm.PythonDependencyGraphORM.file_id
            ).where(
                python_dependency_graph_orm.PythonDependencyGraphORM.parent_id == file_id
            )

            result = await session.execute(query)
            return {row[0] for row in result.all()}

    async def get_dependency_graph(self, file_id: uuid.UUID, depth: int = 2) -> dict:
        """
        Get full dependency graph up to specified depth
        :param file_id: starting file id
        :param depth: max depth to traverse
        :return: nested dict representing dependency tree
        """

        async def _traverse(current_id: uuid.UUID, current_depth: int, visited: set) -> dict:
            if current_depth > depth or current_id in visited:
                return {}

            visited.add(current_id)
            deps = await self.get_dependencies(current_id)

            result = {}
            for dep_id in deps:
                if dep_id not in visited:
                    result[str(dep_id)] = await _traverse(dep_id, current_depth + 1, visited)

            return result

        return await _traverse(file_id, 0, set())
