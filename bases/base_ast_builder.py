import abc
from typing import List, Optional

from dto import ast_node_dto, git_file_dto


class BaseASTBuilder(abc.ABC):
    """
    Base AST builder
    """

    def __init__(self, git_file: git_file_dto.GitFileInDB):
        """
        Init variables
        :param git_file: git file data
        """

        self.git_file = git_file
        self.nodes: List[ast_node_dto.ASTNode] = []
        self._current_class: Optional[str] = None

    @abc.abstractmethod
    def extract(self) -> List[ast_node_dto.ASTNode]:
        """
        Extract all nodes from file
        :return: list of AST nodes
        """

        raise NotImplementedError
