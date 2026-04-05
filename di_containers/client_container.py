from dependency_injector import containers, providers
from langchain_ollama import ChatOllama

from clients import alchemy_pg_client, qdrant_client
from config import ai_config, pg_config

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()


class ClientContainer(containers.DeclarativeContainer):
    """
    DI-container for clients
    """

    ollama_client = providers.Singleton(
        ChatOllama,
        model=ai_config_.llm,
        base_url=ai_config_.ollama_url,
        temperature=ai_config_.llm_temp,
    )
    qdrant_client = providers.Singleton(
        qdrant_client.QdrantClient,
    )
    pg_client = providers.Singleton(
        alchemy_pg_client.AlchemyPGClient,
        database_url=str(pg_config_.postgres_dsn),
    )