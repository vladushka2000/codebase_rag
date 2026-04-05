import asyncio
import logging

from dependency_injector import providers
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from ai_tools import (
    files_entrypoints_finder,
    prompt_tools,
    qdrant_finder,
    rag_answer
)
from di_containers import client_container, repositories_container
from rag_states import runtime_states, start_and_final_states

logging.basicConfig(level=logging.INFO)
client_container_ = client_container.ClientContainer()
repositories_container_ = repositories_container.RepositoryContainer(
    db_dependency=providers.DependenciesContainer(pg_client=client_container_.pg_client)
)

qdrant_client = client_container_.qdrant_client()
pg_client = client_container_.pg_client()
ollama_client = client_container_.ollama_client()
ollama_embeddings = client_container_.ollama_embeddings()

files_repo = repositories_container_.files_repo()

runtime_context = runtime_states.RuntimeContext(
    qdrant_client=qdrant_client,
    pg_client=pg_client,
    ollama_client=ollama_client,
    ollama_embeddings=ollama_embeddings,
    files_repo=files_repo,
)


async def main():
    """
    Start RAG-system
    """

    qdrant_client.connect()
    await pg_client.connect()

    builder = StateGraph(
        runtime_states.GraphState,
        input_schema=start_and_final_states.InputPrompt,
        output_schema=start_and_final_states.SimpleAnswer,
        context_schema=runtime_states.RuntimeContext,
    )

    builder.add_node("prompt_enhancer", prompt_tools.enhance_prompt)
    builder.add_node("simple_answer", rag_answer.get_simple_answer)
    builder.add_node("qdrant_finder", qdrant_finder.get_context_from_qdrant)
    builder.add_node("files_entrypoints_finder", files_entrypoints_finder.get_possible_entrypoints)

    builder.add_conditional_edges(
        START,
        prompt_tools.is_rag_required,
        {True: "prompt_enhancer", False: "simple_answer"}
    )
    builder.add_edge("simple_answer", END)

    builder.add_edge("prompt_enhancer", "qdrant_finder")
    builder.add_edge("prompt_enhancer", "files_entrypoints_finder")

    graph = builder.compile()
    result = await graph.ainvoke(
        input=start_and_final_states.InputPrompt(prompt="Где находятся апихи и роуты?"),
        context=runtime_context,
    )
    print(result["answer"])

    qdrant_client.disconnect()
    await pg_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
