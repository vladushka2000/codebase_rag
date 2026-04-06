from logging import getLogger

from langgraph.runtime import Runtime

from config import qdrant_config
from dto import git_file_dto
from factories import vector_store_factories
from rag_states import runtime_states, search_states, start_and_final_states

qdrant_config_ = qdrant_config.QdrantConfig()
logger = getLogger(__name__)


def get_context_from_qdrant(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> search_states.PossibleFilesEntrypoints:
    """
    Get qdrant data from the collections based on user's input
    :param state: current state
    :param runtime: runtime context
    :return: found qdrant data
    """

    logger.info("Getting context from qdrant...")

    vector_stores = {
        qdrant_config_.docs_collection: vector_store_factories.create_vector_store(
            qdrant_client=runtime.context.qdrant_client.client,
            embeddings=runtime.context.ollama_embeddings,
            collection_name=qdrant_config_.docs_collection,
        ),
    }
    result = search_states.PossibleFilesEntrypoints(
        user_input=" ".join(state.key_words),
        files=[],
        paths_list=[],
        valid_snippets={}
    )

    # list of tuples (snippet data, confidence score)
    valid_snippets_sorted: list[tuple[git_file_dto.GitFileSnippet, float]] = []

    for store_name, store in vector_stores.items():
        docs_with_scores = store.similarity_search_with_score(
            query=state.prompt,
            k=qdrant_config_.max_results,
            score_threshold=qdrant_config_.score_threshold,
        )

        for doc, score in docs_with_scores:
            valid_snippets_sorted.append(
                (
                    git_file_dto.GitFileSnippet(
                        content=doc.page_content,
                        path=doc.metadata["path"],
                    ),
                    score
                )
            )

        valid_snippets_sorted.sort(key=lambda el: el[1], reverse=True)
        valid_snippets_sorted = valid_snippets_sorted[:10]

    logger.info(
        "Qdrant context: %s",
        (
            "\n".join(
                ["Text: '{text}'. Score: {score}".format(
                    text=el[0].text[:50],
                    score=el[1]
                ) for el in valid_snippets_sorted]
            ) if valid_snippets_sorted else "not found"
        )
    )

    result.valid_snippets = {el[0].path: el[0] for el in valid_snippets_sorted}

    return result
