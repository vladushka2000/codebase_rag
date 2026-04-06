from logging import getLogger

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.runtime import Runtime

from config import ai_config
from dto import rag_dto, git_file_dto
from rag_states import runtime_states, search_states, start_and_final_states
from utils import const

ai_config_ = ai_config.AIConfig()
logger = getLogger(__name__)


async def get_possible_entrypoints(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> search_states.PossibleFilesEntrypoints:
    """
    Get files to start a RAG-search with
    :param state: current state
    :param runtime: runtime context
    :return: list of possible entrypoints
    """

    logger.info("Getting possible entrypoints from DB...")

    found_files = await runtime.context.files_repo.search(search_query=state.prompt)
    all_code_files = await runtime.context.files_repo.list(file_types=[const.FileType.CODE])

    found_files = found_files[:const.MAX_POTENTIAL_ENTRYPOINTS_COUNT]
    entrypoints_left = const.MAX_POTENTIAL_ENTRYPOINTS_COUNT - len(found_files)

    logger.info(
        "Possible entrypoints from DB: %s",
        (
                "\n".join(
                    [el.path for el in found_files]
                ) if found_files else "not found"
            )
    )

    if entrypoints_left > 0:
        logger.info("Invoking LLM search...")

        system_message = SystemMessage(
            content=ai_config_.rag_sys_message,
        )
        user_message = HumanMessage(
            content=(
                "You are given user's prompt and list of file paths in the project.\n"
                "You are to determine which file paths may contain answer to user's questions.\n"
                "User's prompt:\n"
                f"{state.prompt}\n"
                "Prompt key-words:\n"
                f"{' '.join(state.key_words)}\n"
                "List of possible file paths:\n"
                f"{''.join([el.path for el in all_code_files])}"
                f"Potential paths count should not exceed {const.MAX_POTENTIAL_ENTRYPOINTS_COUNT}"
            )
        )

        ollama_client = runtime.context.ollama_client
        structured_llm = ollama_client.with_structured_output(rag_dto.PotentialFilePaths)
        response = await structured_llm.ainvoke([system_message, user_message])

        found_files_with_llm = await runtime.context.files_repo.list(
            paths=response.paths
        )
        found_files_with_llm = found_files_with_llm[:const.MAX_POTENTIAL_ENTRYPOINTS_COUNT]
        found_files.extend(found_files_with_llm)

    return search_states.PossibleFilesEntrypoints(
        user_input=state.prompt,
        files=found_files,
        paths_list=[el.path for el in all_code_files],
        valid_snippets={},
    )


def check_if_files_left(
    state: search_states.PossibleFilesEntrypoints,
) -> bool:
    """
    Check if there are files to check
    :param state: current state
    :return: True if files left, False otherwise
    """

    files_left = len(state.files)
    logger.info("%s possible entrypoints left", str(files_left) if files_left else "No")

    return bool(files_left)


async def check_file(
    state: search_states.PossibleFilesEntrypoints,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> search_states.PossibleFilesEntrypoints:
    """
    Check if file entrypoint is valid to user's input
    :param state: current state
    :param runtime: runtime context
    :return: list of possible entrypoints
    """

    files = [state.files.pop(0),]
    system_message = SystemMessage(
        content=ai_config_.rag_sys_message,
    )
    snippets = []
    imports_to_check = const.ENTRYPOINT_IMPORTS_COUNT

    while files and imports_to_check:
        file = files.pop(0)
        logger.info("Analyzing file %s...", file.path)
        snippet_text_part = (
            "\nSnippets from files related to this by import:"
            f"{'\nSnippet: '.join(snippets)}"
        ) if snippets else ""

        user_message = HumanMessage(
            content=(
                "You are given user's prompt and file content.\n"
                "You are to determine if the file content is accord to the prompt "
                "and give the confidence score from 0 to 1.\n"
                f"You must provide {const.ENTRYPOINT_IMPORTS_COUNT} file paths from code imports in the file, "
                "that may lead to the files relevant to user's input.\n"
                "User's prompt:\n"
                f"{state.user_input}\n"
                "File content:\n"
                f"{file.content}\n"
                "List of possible file paths:\n"
                f"{state.paths_list}"
                f"{snippet_text_part}"
                "In the end you are to give a snippet of the current file (200 symbols maximum), "
                "that is the most relevant to user's prompt, "
                f"if the confidence score higher than {const.MIN_FILE_VALID_SCORE} or empty string otherwise"
            )
        )

        ollama_client = runtime.context.ollama_client
        structured_llm = ollama_client.with_structured_output(rag_dto.FileTraverseInfo)
        response = await structured_llm.ainvoke([system_message, user_message])

        potential_paths = [
            path for path in response.potential_paths if path not in state.valid_snippets
        ]

        if (
            response.file_valid_score > const.MIN_FILE_VALID_SCORE and
            potential_paths and
            response.file_snippet
        ):
            logger.info("File is valid")
            logger.info("Snippet: %s", response.file_snippet)

            found_files = await runtime.context.files_repo.list(
                paths=response.potential_paths[:const.ENTRYPOINT_IMPORTS_COUNT]
            )
            files.extend(found_files)
            snippets.append(response.file_snippet)

            state.valid_snippets[file.path] = git_file_dto.GitFileSnippet(
                content=file.content,
                path=file.path,
            )
            imports_to_check -= 1

    return state
