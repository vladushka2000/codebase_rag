from typing import Optional, List

from sqlalchemy import update, select
from sqlalchemy.sql.functions import func

from bases.orm_repositories import base_files_repository
from dto import git_file_dto
from orm.models import file_orm
from orm.repositories import base_repository
from utils import const


class FilesRepository(
    base_files_repository.BaseFilesRepository,
    base_repository.BaseAlchemyRepository
):
    """
    Repository for files entity
    """

    async def batch_create(
        self,
        files: List[git_file_dto.GitFile],
    ) -> List[git_file_dto.GitFileInDB]:
        """
        Create multiple files in DB
        :param files: list of files to create
        :return: files with corresponding ids
        """

        db_objs = [
            file_orm.FileORM(
                path=obj.path,
                sha=obj.sha,
                size_bytes=obj.size,
                type=obj.type,
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
                git_file_dto.GitFileInDB(
                    id=db_obj.id,
                    path=db_obj.path,
                    sha=db_obj.sha,
                    size=db_obj.size_bytes,
                    type=db_obj.type,
                    content=db_obj.content,
                )
                for db_obj in db_objs
            ]

    async def get_files_count(
        self,
        file_type: Optional[const.FileType] = None,
        extension: Optional[str] = None,
    ) -> int:
        """
        Get number of files in DB
        :param file_type: file type
        :param extension: file extension
        :return: files count
        """

        async with self.pg_client.session() as session:
            query = select(func.count(file_orm.FileORM.id))

            if file_type is not None:
                query = query.filter(
                    file_orm.FileORM.type == file_type
                )

            if extension is not None:
                extension = f".{extension}" if extension[0] != "." else extension
                query = query.filter(
                    file_orm.FileORM.path.ilike(f"%{extension}")
                )

            result = await session.execute(query)

            return result.scalar()

    async def list(
        self,
        file_type: Optional[const.FileType] = None,
        extension: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[git_file_dto.GitFileInDB]:
        """
        Get list of files
        :param file_type: file type
        :param extension: file extension
        :param limit: number of files to return
        :param offset: offset of files to return
        :return: files
        """

        async with self.pg_client.session() as session:
            query = select(file_orm.FileORM)

            if file_type is not None:
                query = query.filter(
                    file_orm.FileORM.type == file_type
                )

            if extension is not None:
                extension = f".{extension}" if extension[0] != "." else extension
                query = query.filter(
                    file_orm.FileORM.path.ilike(f"%{extension}")
                )

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            db_objs = await session.execute(query)
            db_objs = db_objs.scalars().all()

            return [
                git_file_dto.GitFileInDB(
                    id=db_obj.id,
                    path=db_obj.path,
                    sha=db_obj.sha,
                    size=db_obj.size_bytes,
                    type=db_obj.type,
                    content=db_obj.content,
                )
                for db_obj in db_objs
            ]

    async def batch_update(self, objs_in: List[dict]) -> None:
        """
        Update files
        :param objs_in: files batch
        """

        async with self.pg_client.session() as session:
            await session.execute(update(file_orm.FileORM), objs_in)
            await session.commit()
