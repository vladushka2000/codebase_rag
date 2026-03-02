from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bases import base_embedder
from bases.orm_repositories import base_insights_repository
from dto import insight_dto


class InsightsEmbedder(base_embedder.BaseEmbedder):
    """
    Insights content embedder
    """

    def _create_chunks(
        self,
        insight: insight_dto.InsightInDB
    ) -> List[Document]:
        """
        Create chunks from an insight
        :param insight: insight object
        :return: list of chunks
        """

        if not insight.content:
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_text(insight.content)
        documents = []

        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "file_ids": insight.file_ids,
                    "insight_type": insight.insight_type,
                    "severity": insight.severity,
                    "chunk_index": i,
                    "created_at": insight.created_at,
                    "confidence": insight.confidence,
                }
            )
            documents.append(doc)

        return documents

    async def embed(
        self,
        insights_repo: base_insights_repository.BaseInsightsRepository,
        batch_size: int = 100,
        commit_interval: int = 50
    ) -> None:
        """
        Embed insights
        :param insights_repo: repository for insights
        :param batch_size: batch size
        :param commit_interval: commit interval
        """

        offset = 0
        documents_batch = []

        while True:
            insights_batch = await insights_repo.list(
                limit=batch_size,
                offset=offset,
            )

            if not insights_batch:
                break

            for insight in insights_batch:
                try:
                    docs = self._create_chunks(insight)
                    documents_batch.extend(docs)

                    if len(documents_batch) >= commit_interval:
                        await self.vector_store.aadd_documents(documents_batch)
                        documents_batch = []
                except Exception as e:
                    print(f"\nError processing {insight.content[:200]}...: {e}")

                    continue

                if documents_batch:
                    await self.vector_store.aadd_documents(documents_batch)
                    documents_batch = []

                offset += batch_size

        if documents_batch:
            await self.vector_store.aadd_documents(documents_batch)
