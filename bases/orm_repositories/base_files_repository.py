import abc
from typing import Optional, List

from dto import git_file_dto
from utils import const


class BaseFilesRepository(abc.ABC):
    """
    Base repository for files entity
    """

    @abc.abstractmethod
    async def batch_create(
        self,
        files: List[git_file_dto.GitFile],
    ) -> List[git_file_dto.GitFileInDB]:
        """
        Create multiple files in DB
        :param files: list of files to create
        :return: files with corresponding ids
        """

        raise NotImplementedError

    @abc.abstractmethod
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

        raise NotImplementedError

    @abc.abstractmethod
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

        raise NotImplementedError

    @abc.abstractmethod
    async def batch_update(self, objs_in: List[dict]) -> None:
        """
        Update files
        :param objs_in: files batch
        """

        raise NotImplementedError
