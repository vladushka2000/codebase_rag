from logging import getLogger

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.runtime import Runtime

from config import ai_config
from dto import rag_dto
from rag_states import runtime_states, search_states, start_and_final_states

logger = getLogger(__name__)
ai_config_ = ai_config.AIConfig()


async def get_simple_answer(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> start_and_final_states.RAGAnswer:
    """
    Get llm-answer based on user's input without context
    :param state: current state
    :param runtime: runtime context
    :return: answer
    """

    logger.info("Generating RAG-system answer...")

    system_message = SystemMessage(
        content=ai_config_.rag_sys_message,
    )
    user_message = HumanMessage(
        content=f"Question: {state.prompt}\nAnswer the question"
    )

    ollama_client = runtime.context.ollama_client
    response = await ollama_client.ainvoke([system_message, user_message])
    answer = response.content

    return start_and_final_states.RAGAnswer(answer=answer, used_paths=[])


async def get_answer_from_context(
    state: search_states.PossibleFilesEntrypoints,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> start_and_final_states.RAGAnswer:
    """
    Get llm-answer based on user's input without context
    :param state: current state
    :param runtime: runtime context
    :return: answer
    """

    logger.info("Generating RAG-system answer...")

    system_message = SystemMessage(
        content=ai_config_.rag_sys_message,
    )
    user_message = HumanMessage(
        content=(
            f"Question: {state.user_input}.\n"
            "Answer the question based on the context:"
            f"{state.get_list_of_snippets()}\n"
            "In your response you must mention context paths you used to answer the question"
        )
    )

    ollama_client = runtime.context.ollama_client
    structured_llm = ollama_client.with_structured_output(rag_dto.RAGAnswer)
    response = await structured_llm.ainvoke([system_message, user_message])

    return start_and_final_states.RAGAnswer(answer=response.answer, used_paths=response.used_paths)
