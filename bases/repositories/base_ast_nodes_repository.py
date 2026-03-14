import abc
from typing import List, Optional

from dto import ast_node_dto


class BaseASTNodesRepository(abc.ABC):
    """
    Base repository for AST nodes
    """

    @abc.abstractmethod
    async def batch_create(
        self,
        files: List[ast_node_dto.ASTNode],
    ) -> List[ast_node_dto.ASTNodeInDB]:
        """
        Create multiple files in DB
        :param files: list of nodes to create
        :return: nodes with corresponding ids
        """

        raise NotImplementedError

    @abc.abstractmethod
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

        raise NotImplementedError

    @abc.abstractmethod
    async def get_count(self) -> int:
        """
        Get count of all nodes
        :return: nodes count
        """

        raise NotImplementedError
