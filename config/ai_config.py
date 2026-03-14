from pydantic import Field
from pydantic_settings import BaseSettings

from utils import const


class AIConfig(BaseSettings):
    """
    AI settings
    """

    language: const.Language = Field(
        default=const.Language.RU,
        description="App language",
    )
    ollama_host: str = Field(
        default="spb99-vkc-dhwgpu07.devzone.local",
        description="Ollama host",
    )
    ollama_port: int = Field(
        default=11434,
        description="Ollama port",
    )

    llm: str = Field(
        description="LLM name",
        default="qwen3-coder-next:latest"
    )
    embedding_model: str = Field(
        description="Embedding model",
        default="qwen3-embedding:latest",
    )
    embedder_chunk_size: int = Field(
        description="Embedder chunk size",
        default=4096,
    )
    embedder_chunk_overlap: int = Field(
        description="Embedder chunk overlap",
        default=50,
    )

    @property
    def ollama_url(self) -> str:
        """
        Get Ollama url
        :return: ollama url
        """

        return f"http://{self.ollama_host}:{self.ollama_port}"
