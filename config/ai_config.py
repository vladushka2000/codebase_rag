import textwrap

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
    llm_temp: float = Field(
        description="LLM temperature",
        default=0.7
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

    @property
    def rag_sys_message(self) -> str:
        """
        Get RAG system message
        :return: RAG system message
        """

        sys_message = f"""
            You are a RAG assistant answering questions based ONLY on the provided context.
            Answer in {self.language.value}.
            If there is no context, then answer that you cannot provide response.
            """

        return textwrap.dedent(sys_message)

    @property
    def prompt_preprocessor_sys_message(self) -> str:
        """
        Get prompt preprocessor system message
        :return: prompt preprocessor system message
        """

        sys_message = """
        You are an intelligent query preprocessor for a RAG system working with a codebase.
        Your task: take the user's original query and return an enhanced version of that query with English translation, if required, adding explanations in parentheses for informal, transliterated, or slang terms, especially those from software development.
        Rules:
        Do not answer the user's question. Only transform the query.
        If the user uses transliterated terms in other languages (e.g., "мидлваря", "прод", "деплой", "апишка"), add the English equivalent in parentheses.
        If a term could be ambiguous — add a brief clarification from the development context.
        If the query already contains the correct English term, do not duplicate it.
        Preserve the original style and word order.
        If the question is not in English, then add a translation to it below.
        Examples:
        User: "как работает мидлваря в этом проекте"
        You: "Original: как работает мидлваря (middleware) в этом проекте.\nTranslation: How does middleware work in this project?"
        
        User: "найди апишку для юзеров"
        You: "Original: найди апишку (API) для юзеров.\nTranslation: Find the API for users"
        
        If a term needs no explanation — leave it as is.
        Your response must contain only the enhanced query, without any extra comments.
        """

        return textwrap.dedent(sys_message)
