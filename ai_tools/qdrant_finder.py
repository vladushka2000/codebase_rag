from logging import getLogger
from langgraph.runtime import Runtime

from config import qdrant_config
from factories import vector_store_factories
from rag_states import runtime_states, search_states, start_and_final_states

qdrant_config_ = qdrant_config.QdrantConfig()
logger = getLogger(__name__)


def get_context_from_qdrant(
    state: start_and_final_states.InputPrompt,
    runtime: Runtime[runtime_states.RuntimeContext],
) -> search_states.VectorStoreSearchResults:
    """
    Get qdrant data from the collections based on user's input
    :param state: current state
    :param runtime: runtime context
    :return: found qdrant data
    """

    logger.info("Getting context from qdrant...")

    vector_stores = {
        qdrant_config_.insights_collection: vector_store_factories.create_vector_store(
            qdrant_client=runtime.context.qdrant_client.client,
            embeddings=runtime.context.ollama_embeddings,
            collection_name=qdrant_config_.insights_collection,
        ),
        qdrant_config_.docs_collection: vector_store_factories.create_vector_store(
            qdrant_client=runtime.context.qdrant_client.client,
            embeddings=runtime.context.ollama_embeddings,
            collection_name=qdrant_config_.docs_collection,
        ),
    }
    result = search_states.VectorStoreSearchResults(results=[])

    for store_name, store in vector_stores.items():
        docs_with_scores = store.similarity_search_with_score(
            query=state.prompt,
            k=qdrant_config_.max_results,
            score_threshold=qdrant_config_.score_threshold,
        )

        for doc, score in docs_with_scores:
            result.results.append(
                search_states.VectorStoreSearchResult(
                    text=doc.page_content,
                    score=score,
                    metadata=doc.metadata,
                )
            )

        result.results.sort(key=lambda r: r.score, reverse=True)
        result.results = result.results[:10]

    logger.info(
        "Qdrant context:\n%s",
        "\n".join(
            ["Text: '{text}'. Score: {score}".format(
                text=el.text[:50],
                score=el.score
            ) for el in result.results]
        )
    )

    return result
