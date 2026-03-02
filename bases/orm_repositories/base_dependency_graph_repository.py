import abc
import uuid
from typing import List, Optional

from dto import dependency_graph_node_dto


class BaseDependencyGraphRepository(abc.ABC):
    """
    Base repository for dependency graph entity
    """

    @abc.abstractmethod
    async def batch_create(
        self,
        nodes: List[dependency_graph_node_dto.DependencyGraphNode],
    ) -> List[dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
        """
        Create multiple nodes in DB
        :param nodes: list of nodes to create
        :return: nodes with corresponding ids
        """

        raise NotImplementedError

    @abc.abstractmethod
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

        raise NotImplementedError

    @abc.abstractmethod
    async def get_dependencies(self, file_id: uuid.UUID) -> set[uuid.UUID]:
        """
        Get all direct dependencies for a file (what this file imports)
        :param file_id: file id
        :return: set of dependency file ids
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def get_dependents(self, file_id: uuid.UUID) -> set[uuid.UUID]:
        """
        Get all files that depend on this file (who imports this file)
        :param file_id: file id
        :return: set of dependent file ids
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def get_dependency_graph(self, file_id: uuid.UUID, depth: int = 2) -> dict:
        """
        Get full dependency graph up to specified depth
        :param file_id: starting file id
        :param depth: max depth to traverse
        :return: nested dict representing dependency tree
        """

        raise NotImplementedError
