from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from bases import base_embedder
from bases.orm_repositories import base_files_repository
from dto import git_file_dto
from utils import const


class FilesEmbedder(base_embedder.BaseEmbedder):
    """
    Files content embedder
    """

    def _create_chunks(
        self,
        file: git_file_dto.GitFileInDB
    ) -> List[Document]:
        """
        Create chunks from a file
        :param file: file object
        :return: list of chunks
        """

        if file.type == const.FileType.CODE:
            language = self._detect_language(file.path)

            try:
                splitter = RecursiveCharacterTextSplitter.from_language(
                    language=language,
                    chunk_size=1000,
                    chunk_overlap=200
                )
            except ValueError:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", " ", ""]
                )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

        if not file.content:
            return []

        chunks = splitter.split_text(file.content)

        documents = []

        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "file_id": str(file.id),
                    "path": file.path,
                    "sha": file.sha,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "type": file.type,
                }
            )
            documents.append(doc)

        return documents

    def _detect_language(self, file_path: str) -> Language:
        """
        Detect language from file extension
        :param file_path: file path
        :return: language
        """

        extension = file_path.split(".")[-1].lower() if "." in file_path else ""

        language_map = {
            "py": Language.PYTHON,
            "js": Language.JS,
            "ts": Language.TS,
            "java": Language.JAVA,
            "kt": Language.KOTLIN,
            "cpp": Language.CPP,
            "c": Language.C,
            "go": Language.GO,
            "rs": Language.RUST,
            "php": Language.PHP,
            "rb": Language.RUBY,
            "scala": Language.SCALA,
            "swift": Language.SWIFT,
            "html": Language.HTML,
        }

        language = language_map.get(extension)

        if not language:
            raise ValueError("Unknown language")

        return language

    async def embed(
        self,
        files_repo: base_files_repository.BaseFilesRepository,
        batch_size: int = 100,
        commit_interval: int = 50
    ) -> None:
        """
        Embed files
        :param files_repo: repository for files
        :param batch_size: batch size
        :param commit_interval: commit interval
        """

        offset = 0
        documents_batch = []

        while True:
            files_batch = await files_repo.list(
                limit=batch_size,
                offset=offset,
            )

            if not files_batch:
                break

            for file in files_batch:
                try:
                    docs = self._create_chunks(file)
                    documents_batch.extend(docs)

                    if len(documents_batch) >= commit_interval:
                        await self.vector_store.aadd_documents(documents_batch)
                        documents_batch = []
                except Exception as e:
                    print(f"\nError processing {file.path}: {e}")

                    continue

                if documents_batch:
                    await self.vector_store.aadd_documents(documents_batch)
                    documents_batch = []

                offset += batch_size

        if documents_batch:
            await self.vector_store.aadd_documents(documents_batch)
