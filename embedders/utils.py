import cocoindex
from cocoindex import llm

from config import ai_config

ai_config_ = ai_config.AIConfig()


@cocoindex.op.function()
def extract_extension_from_path(filepath: str) -> str:
    """
    Extract extension from filename
    :param filepath: file path
    :return: extension
    """

    return filepath.split("/")[-1].split(".")[-1]


@cocoindex.op.function()
def get_language(extension: str) -> str:
    """
    Get coding language from extension
    :param extension: file extension
    :return: coding language
    """

    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".txt": "text",
    }

    return lang_map.get(extension.lower(), "text")


@cocoindex.transform_flow()
def code_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[list[float]]:
    """
    Embed the text
    :param text: text
    :return: embedded text
    """

    return text.transform(
        cocoindex.functions.EmbedText(
            api_type=llm.LlmApiType.OLLAMA,
            model=ai_config_.embedding_model
        )
    )
