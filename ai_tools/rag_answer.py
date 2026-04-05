from logging import getLogger

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.runtime import Runtime

from config import ai_config
from rag_states import runtime_states, start_and_final_states

logger = getLogger(__name__)
ai_config_ = ai_config.AIConfig()


async def get_simple_answer(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> start_and_final_states.SimpleAnswer:
    """
    Get llm-answer based on user's input without context
    :param state: current state
    :param runtime: runtime context
    :return: answer
    """

    logger.info("Generating simple answer...")

    system_message = SystemMessage(
        content=ai_config_.rag_sys_message,
    )
    user_message = HumanMessage(
        content=f"Question: {state.prompt}\nAnswer the question"
    )

    ollama_client = runtime.context.ollama_client
    response = await ollama_client.ainvoke([system_message, user_message])
    answer = response.content

    return start_and_final_states.SimpleAnswer(answer=answer)
