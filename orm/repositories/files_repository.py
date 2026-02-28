from dto import git_file_dto
from orm.models import file_orm
from orm.repositories import base_repository


class FilesRepository(base_repository.BaseAlchemyRepository):
    """
    Repository for files entity
    """

    async def batch_create(
        self,
        files: list[git_file_dto.GitFile],
    ) -> list[git_file_dto.GitFileInDB]:
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
