from logging import getLogger

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.runtime import Runtime

from config import ai_config
from dto import rag_dto
from rag_states import runtime_states, start_and_final_states

logger = getLogger(__name__)
ai_config_ = ai_config.AIConfig()


async def is_rag_required(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> bool:
    """
    Determine if rag required based on user's input
    :param state: current state
    :param runtime: runtime context
    :return: True if rag required, False otherwise
    """

    logger.info("Determine if rag required...")
    logger.info("Initial prompt: %s", state.prompt)

    system_message = SystemMessage(
        content=ai_config_.rag_sys_message,
    )
    user_message = HumanMessage(
        content=(
            "Determine if the RAG-system is required.\n"
            "RAG-system is required if user is asking about something "
            "that would be found in a software project's codebase and the question mentions or implies:\n"
            "- Code structure, files, directories\n"
            "- APIs, endpoints, routes, URLs\n"
            "- Functions, methods, classes\n"
            "- Configuration, settings, environment\n"
            "- Database queries, models, schemas\n"
            "- Any technical term that suggests looking at code\n"
            "- Deployment, building, testing of THIS project\n"
            "- How something works or is implemented\n"
            "If you are uncertain, answer that RAG-system is required."
            f"Question: {state.prompt}"
        )
    )

    ollama_client = runtime.context.ollama_client
    structured_llm = ollama_client.with_structured_output(rag_dto.RAGNecessity)
    response = await structured_llm.ainvoke([system_message, user_message])

    logger.info("Rag required: %s",  response.is_required)

    return response.is_required


async def enhance_prompt(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> start_and_final_states.SimpleAnswer:
    """
    Enhance user's prompt with additional info
    :param state: current state
    :param runtime: runtime context
    :return: enhanced prompt
    """

    logger.info("Enhancing the prompt...")

    system_message = SystemMessage(
        content=ai_config_.prompt_preprocessor_sys_message,
    )
    user_message = HumanMessage(
        content=f"Initial prompt: {state.prompt}\nEnhance the prompt"
    )

    ollama_client = runtime.context.ollama_client
    response = await ollama_client.ainvoke([system_message, user_message])
    enhanced = response.content

    logger.info("Enhanced prompt: %s", enhanced)

    return start_and_final_states.SimpleAnswer(answer=enhanced)
