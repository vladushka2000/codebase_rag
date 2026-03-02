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


class InsightType(enum.Enum):
    """
    Insight types
    """

    CODE_EXPLANATION = "code_explanation"
    POTENTIAL_PROBLEM = "potential_problem"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"


class InsightSeverity(enum.Enum):
    """
    Insight severity
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUGGESTION = "suggestion"


code_extensions = {
    ".py", ".go", ".cs", ".html", ".js", ".ts", ".sql"
}