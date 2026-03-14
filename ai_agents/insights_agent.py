import asyncio
from typing import AsyncGenerator, List, Tuple

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from bases.repositories import base_files_repository, base_insights_repository
from config import ai_config, pg_config, qdrant_config
from db.repositories import files_repository, insights_repository
from db_clients import alchemy_pg_client, qdrant_client
from dto import git_file_dto, insight_dto
from factories import vector_store_factories
from utils import const

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()
qdrant_config_ = qdrant_config.QdrantConfig()


class InsightAgent:

    def __init__(
        self,
        files_repo: base_files_repository.BaseFilesRepository,
        insights_repo: base_insights_repository.BaseInsightsRepository,
        vector_store: QdrantVectorStore,
        llm: ChatOllama,
        batch_size: int = 10,
        confidence_threshold: float = 0.6,
        top_k: int = 5,
    ):
        """
        Init variables
        :param files_repo: repository for the files
        :param insights_repo: repository for the insights
        :param vector_store: qdrant vector store
        :param llm: llm model
        :param batch_size: number of files to analyze per batch
        :param confidence_threshold: llm insight confidence threshold
        :param top_k: number of similar objects to return from qdrant
        """

        self.files_repo = files_repo
        self.insights_repo = insights_repo
        self.vector_store = vector_store
        self.llm = llm
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        self.top_k = top_k
        self.output_parser = PydanticOutputParser(pydantic_object=insight_dto.AgentInsightResponse)

        system_template = (
            "You are an expert code analyst. Your task is to analyze code files and generate insights.\n\n"
            "For every file you should generate list of insights. Each insight should:\n"
            "1. Identify patterns, potential issues, or important observations;\n"
            "2. Be specific and actionable;\n"
            "3. Reference relevant code fragments;\n"
            "4. Explain code flow and business logic;\n"
            "5. Include confidence score based on how certain you are.\n\n"
            "{format_instructions}"
            "Do not use double quotes in the answer, use single quotes instead."
            f"Insight should be in {ai_config_.language.RU.value}"
        )

        human_template = (
            "Analyze the following code file and similar code fragments found in the codebase:\n\n"
            "CURRENT FILE:\n"
            "Path: {file_path}\n"
            "Type: {file_type}\n"
            "Content:\n"
            "```{language}\n"
            "{file_content}\n"
            "```\n\n"
            "SIMILAR CODE FRAGMENTS FOUND (similarity > 0.6):\n"
            "{similar_fragments}\n\n"
            "Generate insights based on the analysis.\n\n"
            "Return the insights in the specified format."
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(human_template),
            ]
        )

    async def _get_files_batch(self) -> AsyncGenerator[List[git_file_dto.GitFileInDB], None]:
        """
        Get files batch
        :return: files batch
        """

        offset = 0
        files_count = await self.files_repo.get_files_count(file_type=const.FileType.CODE)

        while offset < files_count:
            files = await self.files_repo.list(
                file_type=const.FileType.CODE,
                limit=self.batch_size,
                offset=offset,
            )
            offset += self.batch_size
            files = [file for file in files if file.content]

            yield files

    async def _find_similar_fragments(
        self,
        file_content: str,
        file_path: str,
    ) -> List[Tuple[Document, float]]:
        """
        Find similar chunks in qdrant
        :param file_content: file content
        :param file_path: file path
        :return: list of similar fragments with scores
        """

        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=ai_config_.embedder_chunk_size,
            chunk_overlap=ai_config_.embedder_chunk_overlap,
        )
        chunks = splitter.split_text(file_content)
        chunks_to_process = chunks[:3]

        if not chunks_to_process:
            return []

        async def search_chunk(chunk: str) -> List[Tuple[Document, float]]:
            try:
                results = await self.vector_store.asimilarity_search_with_relevance_scores(
                    query=chunk,
                    k=self.top_k * 2,
                    filter=Filter(
                        must_not=[
                            FieldCondition(
                                key="metadata.file_path",
                                match=MatchValue(value=file_path),
                            )
                        ]
                    ),
                )
                return results
            except Exception as e:
                print(f"Error searching for chunk: {e}")
                return []

        tasks = [search_chunk(chunk) for chunk in chunks_to_process]
        all_results_lists = await asyncio.gather(*tasks)
        all_results = []

        for results in all_results_lists:
            all_results.extend(results)

        seen = set()
        unique_results = []

        for doc, score in sorted(all_results, key=lambda x: x[1], reverse=True):
            if score < self.confidence_threshold:
                continue

            doc_id = f"{doc.metadata.get('file_path')}:{doc.metadata.get('start_line')}"

            if doc_id not in seen:
                seen.add(doc_id)
                unique_results.append((doc, score))
                if len(unique_results) >= self.top_k:
                    break

        return unique_results

    def _format_similar_fragments(self, fragments: List[Tuple[Document, float]]) -> str:
        """
        Format string from prompt for similar fragments
        :param fragments: list of similar fragments
        :return: formatted string
        """

        if not fragments:
            return "No similar fragments found."

        formatted = []

        for i, (doc, score) in enumerate(fragments, 1):
            metadata = doc.metadata
            formatted.append(
                f"{i}. From {metadata.get('file_path', 'unknown')} "
                f"(lines {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}), "
                f"similarity: {score:.2f}\n"
                f"```\n{doc.page_content}\n```\n"
            )

        return "\n".join(formatted)

    async def process_file(self, file: git_file_dto.GitFileInDB) -> List[insight_dto.Insight]:
        """
        Process file
        :param file: file object
        :return: list of insights
        """

        similar_fragments = await self._find_similar_fragments(file.content, file.path)

        messages = self.prompt.format_messages(
            file_path=file.path,
            file_type=file.type.value,
            file_content=file.content,
            language="python" if file.path.endswith('.py') else "code",
            similar_fragments=self._format_similar_fragments(similar_fragments),
            format_instructions=self.output_parser.get_format_instructions(),
        )

        response = await self.llm.ainvoke(messages)
        parsed_response = self.output_parser.parse(response.content)

        return parsed_response.insights

    async def process_batch(self, files: List[git_file_dto.GitFileInDB]) -> List[insight_dto.Insight]:
        """
        Process multiple files in batch
        :param files: list of files
        :return: list of insights
        """

        semaphore = asyncio.Semaphore(10)

        async def process_single_file(file: git_file_dto.GitFileInDB) -> List[insight_dto.Insight]:
            async with semaphore:
                try:
                    insights = await self.process_file(file)
                    print(f"Processed file {file.path}, generated {len(insights)} insights")

                    return insights
                except Exception as e:
                    print(f"Error processing file {file.path}: {e}")
                    return []

        tasks = [process_single_file(file) for file in files]
        results = await asyncio.gather(*tasks)
        all_insights = []

        for insights in results:
            all_insights.extend(insights)

        return all_insights

    async def run(self) -> None:

        print("Starting insight agent...")
        total_insights = 0

        async for files_batch in self._get_files_batch():
            if not files_batch:
                continue

            print(f"Processing batch of {len(files_batch)} files...")
            insights = await self.process_batch(files_batch)

            if insights:
                saved_insights = await self.insights_repo.batch_create(insights)
                total_insights += len(saved_insights)
                print(f"Saved {len(saved_insights)} insights")

        print(f"Completed. Total insights generated: {total_insights}")


async def run_agent() -> None:
    """
    Run insights agent
    """

    pg_client = alchemy_pg_client.AlchemyPGClient(
        database_url=str(pg_config_.postgres_dsn),
    )
    qdrant_client_ = qdrant_client.QdrantClient()

    await pg_client.connect()
    qdrant_client_.connect()

    files_repo = files_repository.FilesRepository(pg_client)
    insights_repo = insights_repository.InsightsRepository(pg_client)

    embeddings = OllamaEmbeddings(
        model=ai_config_.embedding_model,
        base_url=ai_config_.ollama_url
    )
    vector_store = vector_store_factories.create_vector_store(
        qdrant_client=qdrant_client_.client,
        embeddings=embeddings,
        collection_name=qdrant_config_.ast_collection_python
    )
    llm = ChatOllama(
        model=ai_config_.llm,
        base_url=ai_config_.ollama_url,
        temperature=0.3,
        num_predict=4096,
    )
    agent = InsightAgent(
        files_repo=files_repo,
        insights_repo=insights_repo,
        vector_store=vector_store,
        llm=llm,
        batch_size=10,
        confidence_threshold=0.6,
        top_k=5,
    )

    await agent.run()

    await pg_client.disconnect()
    qdrant_client_.disconnect()
    vector_store.client.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
