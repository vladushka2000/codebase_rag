from typing import List, Optional

from sqlalchemy import select, func

from bases.repositories import base_ast_nodes_repository, base_alchemy_repository
from dto import ast_node_dto
from db.orm_models import ast_node_orm


class ASTNodesRepository(
    base_ast_nodes_repository.BaseASTNodesRepository,
    base_alchemy_repository.BaseAlchemyRepository
):
    """
    Repository for AST nodes
    """

    async def batch_create(
        self,
        files: List[ast_node_dto.ASTNode],
    ) -> List[ast_node_dto.ASTNodeInDB]:
        """
        Create multiple files in DB
        :param files: list of nodes to create
        :return: nodes with corresponding ids
        """

        db_objs = [
            ast_node_orm.ASTNodeORM(
                file_path=obj.file_path,
                object_name=obj.object_name,
                type=obj.type,
                start_line=obj.start_line,
                end_line=obj.end_line,
                content=obj.content,
            )
            for obj in files
        ]

        async with self.pg_client.session() as session:
            session.add_all(db_objs)

            await session.flush()

            for db_obj in db_objs:
                await session.refresh(db_obj)

            await session.commit()

            return [
                ast_node_dto.ASTNodeInDB(
                    id=obj.id,
                    file_path=obj.file_path,
                    object_name=obj.object_name,
                    type=obj.type,
                    start_line=obj.start_line,
                    end_line=obj.end_line,
                    content=obj.content,
                )
                for obj in db_objs
            ]

    async def get_count(self) -> int:
        """
        Get count of all nodes
        :return: nodes count
        """

        async with self.pg_client.session() as session:
            query = select(func.count(ast_node_orm.ASTNodeORM.id))
            result = await session.execute(query)

            return result.scalar()

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ast_node_dto.ASTNodeInDB]:
        """
        Get list of nodes
        :param limit: number of nodes to return
        :param offset: offset of nodes to return
        :return: nodes
        """

        async with self.pg_client.session() as session:
            query = select(ast_node_orm.ASTNodeORM)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            db_objs = await session.execute(query)
            db_objs = db_objs.scalars().all()

            return [
                ast_node_dto.ASTNodeInDB(
                    id=db_obj.id,
                    file_path=db_obj.file_path,
                    object_name=db_obj.object_name,
                    type=db_obj.type,
                    start_line=db_obj.start_line,
                    end_line=db_obj.end_line,
                    content=db_obj.content,
                )
                for db_obj in db_objs
            ]
