import asyncio
import logging

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from ai_tools import rag_answer, prompt_tools
from di_containers import client_container
from rag_states import runtime_states, start_and_final_states

logging.basicConfig(level=logging.INFO)
client_container_ = client_container.ClientContainer()

qdrant_client = client_container_.qdrant_client()
pg_client = client_container_.pg_client()
ollama_client = client_container_.ollama_client()

runtime_context = runtime_states.RuntimeContext(
    qdrant_client=qdrant_client,
    pg_client=pg_client,
    ollama_client=ollama_client,
)


async def main():
    """
    Start RAG-system
    """

    qdrant_client.connect()

    builder = StateGraph(
        runtime_states.GraphState,
        input_schema=start_and_final_states.InputPrompt,
        output_schema=start_and_final_states.SimpleAnswer,
        context_schema=runtime_states.RuntimeContext,
    )

    builder.add_node("prompt_enhancer", prompt_tools.enhance_prompt)
    builder.add_node("simple_answer", rag_answer.get_simple_answer)

    builder.add_conditional_edges(
        START,
        prompt_tools.is_rag_required,
        {True: "prompt_enhancer", False: "simple_answer"}
    )
    builder.add_edge("prompt_enhancer", END)
    builder.add_edge("simple_answer", END)

    graph = builder.compile()
    result = await graph.ainvoke(
        input=start_and_final_states.InputPrompt(prompt="Где находятся апихи и роуты?"),
        context=runtime_context,
    )
    print(result["answer"])

    qdrant_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())


# from langchain.tools import tool
# from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
# from langchain_core.prompts import ChatPromptTemplate
#
# from clients import ollama_client
#
# # 1. Создаем тулзу для вычислений
# @tool
# def calculate(expression: str) -> str:
#     """Вычисляет математическое выражение.
#     Примеры: '2+2', '10*5', '100/4', '2^3'"""
#     try:
#         result = eval(expression)
#         return f"Результат: {result}"
#     except Exception as e:
#         return f"Ошибка: {e}"
#
# # 2. Создаем LLM
# llm = ollama_client.ollama_client
#
# # 3. Создаем промпт
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "Ты помощник, который решает математические задачи. Используй калькулятор для вычислений."),
#     ("human", "{input}"),
#     ("placeholder", "{agent_scratchpad}"),
# ])
#
# # 4. Создаем агента
# agent = create_tool_calling_agent(llm, [calculate], prompt)
# agent_executor = AgentExecutor(agent=agent, tools=[calculate], verbose=True)
#
# # 5. Используем
# result = agent_executor.invoke({"input": "Сколько будет 15 * 8 + 12?"})
# print(result["output"])