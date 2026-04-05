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


class ASTNodeType(enum.Enum):
    """
    Object types for python AST
    """

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"


class CollectionPriority(enum.Enum):
    """
    Collection priority levels
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


code_extensions = {
    ".py", ".go", ".cs", ".html", ".js", ".ts", ".sql"
}

MIN_FILE_VALID_SCORE = 0.8
MAX_POTENTIAL_ENTRYPOINTS_COUNT = 10
ENTRYPOINT_IMPORTS_COUNT = 3