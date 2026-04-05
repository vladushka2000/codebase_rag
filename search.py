from ai_agents import rag_agent
from clients import qdrant_client
from langchain_ollama import ChatOllama
from config import ai_config

ai_config_ = ai_config.AIConfig()


def main():
    # Connect to Qdrant
    client = qdrant_client.QdrantClient()
    client.connect()

    try:
        # Initialize LLM and RAG service
        llm = ChatOllama(
            model=ai_config_.llm,
            base_url=ai_config_.ollama_url,
            temperature=0.3,
        )

        rag = rag_agent.RAGAgent(llm, client.client)

        # Ask a question - system will automatically prioritize collections
        response = rag.answer_question(
            question="Какие middleware использует сервис?",
            total_results=50,
            score_threshold=0.6,
        )

        print(f"\n💡 Ответ:\n{response.answer}")

        for i, result in enumerate(response.results, 1):
            print(f"\n  {i}. Релевантность: {result.score:.3f}")
            if 'file_path' in result.metadata:
                print(f"     Файл: {result.metadata['file_path']}")
            elif 'path' in result.metadata:
                print(f"     Файл: {result.metadata['path']}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()