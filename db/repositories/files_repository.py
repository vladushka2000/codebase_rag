import uuid
from typing import Optional, List, Dict

from sqlalchemy import update, select
from sqlalchemy.sql.functions import func

from bases.repositories import base_files_repository, base_alchemy_repository
from config import pg_config
from db.orm_models import file_orm
from dto import git_file_dto
from utils import const

pg_config_ = pg_config.PostgresConfig()


class FilesRepository(
    base_files_repository.BaseFilesRepository,
    base_alchemy_repository.BaseAlchemyRepository
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

    async def get_by_id(self, file_id: uuid.UUID) -> Optional[git_file_dto.GitFileInDB]:
        """
        Get file by id
        :param file_id: file id
        :return: file if found, None otherwise
        """

        async with self.pg_client.session() as session:
            query = select(file_orm.FileORM).where(file_orm.FileORM.id == file_id)
            result = await session.execute(query)
            db_obj = result.scalar_one_or_none()

            if not db_obj:
                return None

            return git_file_dto.GitFileInDB(
                id=db_obj.id,
                path=db_obj.path,
                sha=db_obj.sha,
                size=db_obj.size_bytes,
                type=db_obj.type,
                content=db_obj.content,
            )

    async def get_by_ids(self, file_ids: List[uuid.UUID]) -> Dict[uuid.UUID, git_file_dto.GitFileInDB]:
        """
        Get multiple files by their ids in a single query
        :param file_ids: list of file ids
        :return: dict of files. Key - id, value - data
        """

        async with self.pg_client.session() as session:
            query = select(file_orm.FileORM).where(
                file_orm.FileORM.id.in_(file_ids)
            )
            result = await session.execute(query)
            db_objs = result.scalars().all()

            return {
                db_obj.id: git_file_dto.GitFileInDB(
                    id=db_obj.id,
                    path=db_obj.path,
                    sha=db_obj.sha,
                    size=db_obj.size_bytes,
                    type=db_obj.type,
                    content=db_obj.content,
                )
                for db_obj in db_objs
            }

    async def get_ids(
        self,
        file_type: Optional[const.FileType] = None,
        extension: Optional[str] = None,
    ) -> List[uuid.UUID]:
        """
        Get ids of all files
        :param file_type: file type
        :param extension: file extension
        :return: list of ids
        """

        async with self.pg_client.session() as session:
            query = select(file_orm.FileORM.id)

            if file_type:
                query = query.where(file_orm.FileORM.type == file_type)

            if extension is not None:
                extension = f".{extension}" if extension[0] != "." else extension
                query = query.filter(
                    file_orm.FileORM.path.ilike(f"%{extension}")
                )

            result = await session.execute(query)

            return list(result.scalars().all())

    async def get_files_count(
        self,
        file_types: Optional[List[const.FileType]] = None,
        extension: Optional[str] = None,
    ) -> int:
        """
        Get number of files in DB
        :param file_types: file types
        :param extension: file extension
        :return: files count
        """

        async with self.pg_client.session() as session:
            query = select(func.count(file_orm.FileORM.id))

            if file_types is not None:
                query = query.filter(
                    file_orm.FileORM.type.in_(file_types)
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
        file_types: Optional[List[const.FileType]] = None,
        extension: Optional[str] = None,
        paths: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[git_file_dto.GitFileInDB]:
        """
        Get list of files
        :param file_types: file types
        :param extension: file extension
        :param paths: file paths
        :param limit: number of files to return
        :param offset: offset of files to return
        :return: files
        """

        async with self.pg_client.session() as session:
            query = select(file_orm.FileORM)

            if file_types is not None:
                query = query.filter(
                    file_orm.FileORM.type.in_(file_types)
                )

            if extension is not None:
                extension = f".{extension}" if extension[0] != "." else extension
                query = query.filter(
                    file_orm.FileORM.path.ilike(f"%{extension}")
                )

            if paths is not None:
                query = query.filter(
                    file_orm.FileORM.path.in_(paths)
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

    async def search(
        self,
        search_query: str,
        file_types: Optional[List[const.FileType]] = None,
        extension: Optional[str] = None,
    ) -> List[git_file_dto.GitFileInDB]:
        """
        Search files using both full-text search (TSVECTOR) and trigram search (GIN index).
        Results are combined and duplicates are removed.
        :param search_query: search query string
        :param file_types: filter by file types
        :param extension: filter by file extension
        :return: list of matching files without duplicates
        """

        async with self.pg_client.session() as session:
            words = search_query.split()
            tsquery_parts = []

            for word in words:
                tsquery_parts.append(f"{word}:*")

            tsquery_str = " | ".join(tsquery_parts)

            query_vector = select(
                file_orm.FileORM,
                func.ts_rank(
                    file_orm.FileORM.search_vector,
                    func.to_tsquery("simple", tsquery_str)
                ).label("relevance")
            ).where(
                file_orm.FileORM.search_vector.op("@@")(func.to_tsquery("simple", tsquery_str))
            ).order_by(
                func.ts_rank(
                    file_orm.FileORM.search_vector,
                    func.to_tsquery("simple", tsquery_str)
                ).desc()
            )

            if words:
                trigram_score = func.greatest(
                    *[func.similarity(file_orm.FileORM.content, word) for word in words if len(word) >= 3]
                )

                query_trigram = select(
                    file_orm.FileORM,
                    trigram_score.label("relevance")
                ).where(
                    trigram_score > pg_config_.search_score
                ).order_by(
                    trigram_score.desc()
                )
            else:
                query_trigram = select(file_orm.FileORM, func.literal(0.0).label("relevance")).where(False)  # noqa

            for query in [query_vector, query_trigram]:
                if file_types is not None:
                    query = query.filter(file_orm.FileORM.type.in_(file_types))

                if extension is not None:
                    ext = f".{extension}" if extension[0] != "." else extension
                    query = query.filter(file_orm.FileORM.path.ilike(f"%{ext}"))

            vector_result = await session.execute(query_vector)
            trigram_result = await session.execute(query_trigram)

            # Key - file id, value - file data
            files = {}

            for db_obj, relevance in vector_result:
                if db_obj.id not in files and relevance > pg_config_.search_score:
                    files[db_obj.id] = (db_obj, relevance)

            for db_obj, relevance in trigram_result:
                if db_obj.id not in files and relevance > pg_config_.search_score:
                    files[db_obj.id] = (db_obj, relevance)

            return [
                git_file_dto.GitFileInDB(
                    id=db_obj.id,
                    path=db_obj.path,
                    sha=db_obj.sha,
                    size=db_obj.size_bytes,
                    type=db_obj.type,
                    content=db_obj.content,
                )
                for db_obj, _ in files
            ]
