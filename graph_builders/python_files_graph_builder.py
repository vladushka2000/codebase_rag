import ast
import uuid
from collections import defaultdict
from math import ceil
from typing import Dict, Set, List

from bases.orm_repositories import base_files_repository, base_python_dependency_graph_repository
from dto import git_file_dto, python_dependency_graph_node_dto
from utils import const


async def update_python_dependencies(
    files_repo: base_files_repository.BaseFilesRepository,
    python_deps_repo: base_python_dependency_graph_repository.BasePythonDependencyGraphRepository,
    batch_size: int = 10
) -> None:
    """
    Update python files dependencies
    :param files_repo: repository for files
    :param python_deps_repo: repository for python dependencies graph
    :param batch_size: files to traverse by one iteration
    """

    all_files = await _get_all_python_files(files_repo, batch_size)

    if not all_files:
        return

    global_path_map = {f.path: f.id for f in all_files}
    all_dependencies = defaultdict(set)

    total_batches = ceil(len(all_files) / batch_size)

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(all_files))

        batch_files = all_files[start_idx:end_idx]
        batch_deps = _process_files_batch(batch_files, global_path_map)

        for file_id, deps in batch_deps.items():
            all_dependencies[file_id].update(deps)

    await _create_dependency_graph_nodes(all_dependencies, python_deps_repo)


async def _get_all_python_files(
    files_repo: base_files_repository.BaseFilesRepository,
    batch_size: int
) -> List[git_file_dto.GitFileInDB]:
    """
    Get all Python files from database using pagination
    :param files_repo: repository for files
    :param batch_size: size of batches for pagination
    :return: list of all Python files
    """

    total = await files_repo.get_files_count(
        file_type=const.FileType.CODE,
        extension=".py"
    )

    if total == 0:
        return []

    all_files = []
    total_batches = ceil(total / batch_size)

    for batch_num in range(total_batches):
        files = await files_repo.list(
            file_type=const.FileType.CODE,
            extension=".py",
            limit=batch_size,
            offset=batch_num * batch_size
        )
        all_files.extend(files)

    return all_files


def _process_files_batch(
    files: List[git_file_dto.GitFileInDB],
    global_path_map: Dict[str, uuid.UUID]
) -> Dict[uuid.UUID, Set[uuid.UUID]]:
    """
    Process a batch of files to find dependencies between them using global path map
    :param files: list of files to process
    :param global_path_map: global mapping from file paths to IDs for ALL files
    :return: dictionary mapping file IDs to sets of dependency file IDs
    """

    batch_deps = defaultdict(set)

    for file in files:
        file_deps = _find_file_dependencies(file, global_path_map)
        if file_deps:
            batch_deps[file.id] = file_deps

    return batch_deps


def _find_file_dependencies(
    file: git_file_dto.GitFileInDB,
    global_path_map: Dict[str, uuid.UUID]
) -> Set[uuid.UUID]:
    """
    Find all dependencies for a single file by parsing its AST using global path map
    :param file: file to analyze
    :param global_path_map: global mapping from file paths to IDs for ALL files
    :return: set of dependency file IDs
    """

    dependencies = set()

    try:
        tree = ast.parse(file.content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_path = alias.name.replace(".", "/")
                    dep_path = f"{module_path}.py"

                    if dep_path in global_path_map and global_path_map[dep_path] != file.id:
                        dependencies.add(global_path_map[dep_path])

            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level > 0:
                    path_parts = file.path.split("/")

                    if len(path_parts) > node.level:
                        base = "/".join(path_parts[:-node.level])

                        if node.module:
                            module_path = node.module.replace(".", "/")
                            dep_path = f"{base}/{module_path}.py"
                        else:
                            dep_path = f"{base}/__init__.py"

                        if dep_path in global_path_map:
                            dependencies.add(global_path_map[dep_path])
                else:
                    dep_path = f"{node.module.replace('.', '/')}.py"
                    if dep_path in global_path_map:
                        dependencies.add(global_path_map[dep_path])
    except Exception as e:
        print(f"Error while dependency resolving: {e}")

    return dependencies


async def _create_dependency_graph_nodes(
    all_dependencies: Dict[uuid.UUID, Set[uuid.UUID]],
    python_deps_repo
) -> None:
    """
    Create nodes in python_dependency_graph table for all dependencies
    :param all_dependencies: dictionary mapping file IDs to sets of dependency file IDs
    :param python_deps_repo: repository for python dependencies graph
    """

    nodes_to_create: List[
        python_dependency_graph_node_dto.PythonDependencyGraphNode
    ] = []

    for file_id, deps in all_dependencies.items():
        for dep_id in deps:
            nodes_to_create.append(
                python_dependency_graph_node_dto.PythonDependencyGraphNode(
                    file_id=file_id,
                    parent_id=dep_id,
                )
            )

    if nodes_to_create:
        await python_deps_repo.batch_create(nodes_to_create)
