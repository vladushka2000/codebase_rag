from dependency_injector import containers, providers

from db.repositories import files_repository


class RepositoryContainer(containers.DeclarativeContainer):
    """
    DI-container for repositories
    """

    db_dependency = providers.DependenciesContainer()

    files_repo = providers.Factory(
        files_repository.FilesRepository,
        pg_client=db_dependency.pg_client,
    )
