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