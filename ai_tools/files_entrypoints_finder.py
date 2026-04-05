from logging import getLogger

from langgraph.runtime import Runtime

from rag_states import runtime_states, search_states, start_and_final_states
from utils import const

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

    logger.info(
        "Possible entrypoints from DB:\n%s",
        "\n".join(
            [el.path for el in found_files]
        )
    )

    return search_states.PossibleFilesEntrypoints(
        files=found_files,
        paths_list=[el.path for el in all_code_files],
    )
