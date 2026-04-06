from pydantic import BaseModel, Field

from dto import git_file_dto


class PossibleFilesEntrypoints(BaseModel):
    """
    Possible entrypoints
    """

    user_input: str = Field(description="Initial user's input")
    files: list[git_file_dto.GitFileInDB] = Field(description="List of files to check")
    paths_list: list[str] = Field(description="List of all code paths")
    valid_snippets: dict[str, git_file_dto.GitFileSnippet] = Field(
        description="Map of valid code snippets. Key - path, value - file data"
    )
    recursion_depth: int = Field(description="Current recursion depth", default=1)

    def get_list_of_snippets(self) -> str:
        """
        Format list of snippets
        :return: list of snippets
        """

        snippets: list[str] = []
        result = ""

        for path, snippet in self.valid_snippets.items():
            snippets.append(
                f"- File path: {path}\n"
                f"- Content: {snippet.content}"
            )

        for i, snippet in enumerate(snippets, start=1):
            result += f"\nSnippet {i}:\n{snippet}"

        return result
