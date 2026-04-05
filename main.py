import asyncio
import logging

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from ai_tools import prompt_tools, qdrant_finder, rag_answer
from di_containers import client_container
from rag_states import runtime_states, start_and_final_states

logging.basicConfig(level=logging.INFO)
client_container_ = client_container.ClientContainer()

qdrant_client = client_container_.qdrant_client()
pg_client = client_container_.pg_client()
ollama_client = client_container_.ollama_client()
ollama_embeddings = client_container_.ollama_embeddings()

runtime_context = runtime_states.RuntimeContext(
    qdrant_client=qdrant_client,
    pg_client=pg_client,
    ollama_client=ollama_client,
    ollama_embeddings=ollama_embeddings,
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
    builder.add_node("qdrant_finder", qdrant_finder.get_context_from_qdrant)

    builder.add_conditional_edges(
        START,
        prompt_tools.is_rag_required,
        {True: "prompt_enhancer", False: "simple_answer"}
    )
    builder.add_edge("prompt_enhancer", "qdrant_finder")
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
