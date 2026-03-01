import abc
from typing import List, Optional

from dto import python_dependency_graph_node_dto


class BasePythonDependencyGraphRepository(abc.ABC):
    """
    Base repository for python dependency graph entity
    """

    @abc.abstractmethod
    async def batch_create(
        self,
        nodes: List[python_dependency_graph_node_dto.PythonDependencyGraphNode],
    ) -> List[python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
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
    ) -> List[python_dependency_graph_node_dto.PythonDependencyGraphNodeInDB]:
        """
        Get list of nodes
        :param limit: number of files to return
        :param offset: offset of files to return
        :return: nodes
        """

        raise NotImplementedError
