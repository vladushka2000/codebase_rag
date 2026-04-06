import enum


class FileType(enum.Enum):
    """
    File type
    """

    CODE = "code"
    DOC = "doc"
    UNKNOWN = "unknown"


class Language(enum.Enum):
    """
    Languages
    """

    EN = "english"
    RU = "russian"


code_extensions = {
    ".py", ".go", ".cs", ".html", ".js", ".ts", ".sql"
}

MIN_FILE_VALID_SCORE = 0.8
MAX_POTENTIAL_ENTRYPOINTS_COUNT = 10
ENTRYPOINT_IMPORTS_COUNT = 3