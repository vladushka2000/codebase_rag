import uuid
from math import ceil
from typing import List, Dict

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_postgres import PGVectorStore

from bases.orm_repositories import (
    base_insights_repository,
    base_files_repository,
    base_dependency_graph_repository
)
from dto import insight_dto, git_file_dto


class CodeInsightAgent:
    """
    Единый агент для генерации инсайтов по кодовой базе
    """

    def __init__(
        self,
        vector_store: PGVectorStore,
        files_repo: base_files_repository.BaseFilesRepository,
        insights_repo: base_insights_repository.BaseInsightsRepository,
        deps_repo: base_dependency_graph_repository.BaseDependencyGraphRepository,
        ollama_url: str,
        model: str = "qwen2.5-coder:32b-instruct",
        batch_size: int = 5,
        max_context_files: int = 3,
        min_confidence: float = 0.6,
        temperature: float = 0.1,
    ):
        """
        Инициализация агента

        :param vector_store: векторное хранилище с эмбеддингами
        :param files_repo: репозиторий файлов
        :param insights_repo: репозиторий инсайтов
        :param deps_repo: python dependencies repository
        :param ollama_url: URL для Ollama
        :param model: модель LLM
        :param batch_size: размер батча файлов
        :param max_context_files: максимум связанных файлов для контекста
        :param min_confidence: минимальная уверенность для сохранения
        :param temperature: температура генерации
        """

        self.vector_store = vector_store
        self.files_repo = files_repo
        self.insights_repo = insights_repo
        self.deps_repo = deps_repo
        self.batch_size = batch_size
        self.max_context_files = max_context_files
        self.min_confidence = min_confidence

        self.llm = ChatOllama(
            model=model,
            base_url=ollama_url,
            temperature=temperature,
        )
        self.output_parser = PydanticOutputParser(
            pydantic_object=insight_dto.AgentInsightResponse
        )
        self.analysis_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", """Ты - эксперт по анализу кода. 
            Проанализируй предоставленный код и верни JSON с инсайтами.
            ВАЖНО: Всегда возвращай ТОЛЬКО валидный JSON без дополнительного текста.
            Формат ответа:
            {format_instructions}

            Анализируй код на предмет:
            - Сложных участков, требующих объяснения
            - Потенциальных проблем и багов
            - Проблем безопасности
            - Возможностей оптимизации
            - Архитектурных проблем
            """
                ),
                (
                    "human", """
            Файл: {file_path}

            Код:
            {code}

            Связанные файлы:
            {related_files}

            Верни JSON с инсайтами.
            """
                )
            ]
        )

    async def run(self):
        """
        Запуск агента для обработки всех файлов
        """

        total_files = await self.files_repo.get_files_count()
        total_batches = ceil(total_files / self.batch_size)

        for batch_num in range(total_batches):
            await self._process_batch(batch_num, total_batches)

    async def _process_batch(self, batch_num: int, total_batches: int):
        """
        Обработка одного батча файлов
        """

        offset = batch_num * self.batch_size
        files = await self.files_repo.list(
            limit=self.batch_size,
            offset=offset,
        )

        for file in files:
            related = await self._get_related_files(file.id)
            insights = await self._analyze_file(file, related)

            if insights:
                await self.insights_repo.batch_create(insights)

    async def _get_related_files(self, file_id: uuid.UUID) -> List[Dict]:
        """
        Получение связанных файлов через репозиторий зависимостей и эмбеддинги
        """

        related_candidates = {}
        all_candidate_ids = set()

        dependencies = await self.deps_repo.get_dependencies(file_id)

        for dep_id in dependencies:
            related_candidates[str(dep_id)] = {
                "source": "dependency",
                "score": 1.0,
                "priority": 3
            }
            all_candidate_ids.add(dep_id)

        dependents = await self.deps_repo.get_dependents(file_id)

        for dep_id in dependents:
            related_candidates[str(dep_id)] = {
                "source": "dependent",
                "score": 0.9,
                "priority": 2
            }
            all_candidate_ids.add(dep_id)

        print(f"  📊 Найдено зависимостей: {len(dependencies)} прямых, {len(dependents)} обратных")

        current_file = await self.files_repo.get_by_id(file_id)

        if current_file and current_file.content:
            similar_chunks = await self.vector_store.asimilarity_search_with_score(
                current_file.content[:2000],
                k=10
            )

            file_scores = {}
            for doc, score in similar_chunks:
                similar_file_id = doc.metadata.get("file_id")
                if similar_file_id and similar_file_id != file_id:
                    if similar_file_id not in file_scores or score > file_scores[similar_file_id]:
                        file_scores[similar_file_id] = score

            for sim_id, score in file_scores.items():
                str_id = str(sim_id)
                if str_id not in related_candidates:
                    related_candidates[str_id] = {
                        "source": "semantic",
                        "score": score,
                        "priority": 1
                    }
                    all_candidate_ids.add(sim_id)
                else:
                    current = related_candidates[str_id]
                    current["score"] = max(current["score"], score * 0.8)

        if not all_candidate_ids:
            return []

        candidate_ids_list = list(all_candidate_ids)
        files_dict = await self.files_repo.get_by_ids(candidate_ids_list)

        sorted_candidates = sorted(
            related_candidates.items(),
            key=lambda x: (x[1]["priority"], x[1]["score"]),
            reverse=True
        )

        related_files = []
        for rel_id_str, info in sorted_candidates[:self.max_context_files]:
            rel_id = uuid.UUID(rel_id_str)
            if rel_id in files_dict:
                rel_file = files_dict[rel_id]

                content = rel_file.content[:500] if rel_file.content else ""
                if len(rel_file.content or "") > 500:
                    content += "..."

                related_files.append({
                    "id": rel_id_str,
                    "path": rel_file.path,
                    "content": content,
                    "type": rel_file.type.value if rel_file.type else "unknown",
                    "relation_type": info["source"],
                    "similarity_score": round(info["score"], 2),
                    "priority": info["priority"]
                })

        if related_files:
            print(f"  🔗 Найдено связанных файлов: {len(related_files)}")
            for rf in related_files:
                print(f"     - {rf['path']} ({rf['relation_type']}, score: {rf['similarity_score']})")

        return related_files

    async def _analyze_file(
        self,
        file: git_file_dto.GitFileInDB,
        related_files: List[Dict]
    ) -> List[insight_dto.Insight]:
        """
        Анализ одного файла
        """

        code = file.content[:3000] if file.content else ""

        if not code:
            return []

        prompt = self.analysis_prompt.format_messages(
            format_instructions=self.output_parser.get_format_instructions(),
            file_path=file.path,
            code=code,
            related_files=related_files or "Нет связанных файлов"
        )

        try:
            response = await self.llm.ainvoke(prompt)
            parsed_response = self.output_parser.parse(response.content)

            return [
                obj for obj in parsed_response.insights if obj.confidence >= self.min_confidence
            ]

        except Exception as e:
            print(f"  ⚠️ Ошибка парсинга ответа для {file.path}: {e}")

            return []
