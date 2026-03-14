import ast
from typing import List, Optional, Union

import astor

from bases import base_ast_builder
from dto import ast_node_dto
from utils import const


class ASTBuilderPython(base_ast_builder.BaseASTBuilder):
    """
    AST nodes extractor
    """

    def extract(self) -> List[ast_node_dto.ASTNode]:
        """
        Extract ast nodes from file
        :return: ast nodes
        """

        try:
            tree = ast.parse(self.git_file.content)

            self._add_module_node(tree)
            self._process_node(tree)

        except SyntaxError as e:
            print(f"Syntax error in {self.git_file.path}: {e}")
        except Exception as e:
            print(f"Error parsing {self.git_file.path}: {e}")

        return self.nodes

    def _process_node(self, node: ast.AST) -> None:
        """
        Process node recursively
        :param node: node object
        """

        if isinstance(node, ast.ClassDef):
            self._process_class(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._process_function(node)
        elif isinstance(node, ast.Assign):
            self._process_assign(node)
        elif isinstance(node, ast.AnnAssign):
            self._process_ann_assign(node)

        for child in ast.iter_child_nodes(node):
            self._process_node(child)

    def _add_module_node(self, tree: ast.Module) -> None:
        """
        Add node with type module
        :param tree: ast tree
        """

        module_content = self._get_node_content(tree)
        self.nodes.append(
            ast_node_dto.ASTNode(
                file_path=self.git_file.path,
                object_name=f"{self.git_file.path}",
                type=const.ASTNodeType.MODULE,
                start_line=1,
                end_line=len(self.git_file.content.splitlines()),
                content=module_content
            )
        )

    def _process_class(self, node: ast.ClassDef):
        """
        Process node with type class
        :param node: node object
        """

        self._current_class = node.name

        class_content = self._get_node_content(node)
        self.nodes.append(
            ast_node_dto.ASTNode(
                file_path=self.git_file.path,
                object_name=node.name,
                type=const.ASTNodeType.CLASS,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                content=class_content
            )
        )

    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        """
        Process node with type function or method
        :param node: node object
        """

        node_type = const.ASTNodeType.METHOD if self._current_class else const.ASTNodeType.FUNCTION
        object_name = f"{self._current_class}.{node.name}" if self._current_class else node.name
        function_content = self._get_node_content(node)

        self.nodes.append(
            ast_node_dto.ASTNode(
                file_path=self.git_file.path,
                object_name=object_name,
                type=node_type,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                content=function_content
            )
        )

    def _process_assign(self, node: ast.Assign) -> None:
        """
        Process variables assign
        :param node: node object
        """

        for target in node.targets:
            if isinstance(target, ast.Name):
                self._add_variable_node(target.id, node, node.value)  # noqa

    def _process_ann_assign(self, node: ast.AnnAssign) -> None:
        """
        Process annotated assign
        :param node: node object
        """

        if isinstance(node.target, ast.Name):
            self._add_variable_node(node.target.id, node, node.value)

    def _add_variable_node(self, var_name: str, node: ast.AST, value_node: Optional[ast.AST]) -> None:
        """
        Add node with type variable
        :param var_name: variable name
        :param node: node object
        :param value_node: node value
        """

        if self._current_class:
            var_name = f"{self._current_class}.{var_name}"

        var_value = self._get_constant_value(value_node) if value_node else None
        content = f"{var_name} = {var_value}" if var_value else var_name

        self.nodes.append(
            ast_node_dto.ASTNode(
                file_path=self.git_file.path,
                object_name=var_name,
                type=const.ASTNodeType.VARIABLE,
                start_line=node.lineno,  # noqa
                end_line=getattr(node, "end_lineno", node.lineno),  # noqa
                content=content
            )
        )

    def _get_node_content(self, node) -> str:
        """
        Get node content
        :param node: node object
        :return: node content
        """

        try:
            return ast.unparse(node).strip()
        except:
            try:
                return astor.to_source(node).strip()
            except:
                return f"# {getattr(node, 'name', 'unknown')}"

    def _get_constant_value(self, node) -> str:
        """
        Get constant value
        :param node: node object
        :return: constant value
        """

        try:
            if isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.List):
                return '[]'
            elif isinstance(node, ast.Dict):
                return '{}'
            elif isinstance(node, ast.Tuple):
                return '()'
            elif isinstance(node, ast.Set):
                return '{}'
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    return f"{node.func.id}()"
                elif isinstance(node.func, ast.Attribute):
                    return f"{self._get_attribute_chain(node.func)}()"
        except Exception:
            pass

        return "..."

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """
        Get attribute chain
        :param node: node object
        :return: attribute chain
        """

        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return ".".join(reversed(parts))
