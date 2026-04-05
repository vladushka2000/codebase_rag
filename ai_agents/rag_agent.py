# rag_service.py
import json
import re
from typing import List, Optional, Dict

import qdrant_client as qdrant_client_
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from config import ai_config, qdrant_config, rag_config
from dto import rag_dto
from factories import vector_store_factories
from utils import const

ai_config_ = ai_config.AIConfig()
qdrant_config_ = qdrant_config.QdrantConfig()
rag_config_ = rag_config.RAGConfig()


class RAGAgent:
    """
    RAG agent for semantic search with intelligent collection prioritization
    """

    def __init__(
            self,
            llm: ChatOllama,
            qdrant_client: qdrant_client_.QdrantClient
    ):
        """
        Init RAG service
        :param llm: language model for query analysis
        :param qdrant_client: qdrant client
        """

        self.llm = llm
        self._qdrant_client = qdrant_client
        self._embeddings = OllamaEmbeddings(
            model=ai_config_.embedding_model,
            base_url=ai_config_.ollama_url
        )

        # Setup collection info
        self._collections = {
            qdrant_config_.docs_collection: {
                "name": qdrant_config_.docs_collection,
                "description": "documentation, text and infrastructure files",
                "keywords": ["documentation", "doc", "manual", "guide", "readme", "instruction", "howto"],
                "priority": const.CollectionPriority.MEDIUM,
            },
            qdrant_config_.insights_collection: {
                "name": qdrant_config_.insights_collection,
                "description": "code insights, potential problems, architecture, security, performance recommendations",
                "keywords": ["insight", "problem", "vulnerability", "security", "bug", "error", "suggestion",
                             "architecture", "performance"],
                "priority": const.CollectionPriority.HIGH,
            },
            qdrant_config_.ast_collection_python: {
                "name": qdrant_config_.ast_collection_python,
                "description": "python code structure, functions, classes, methods, variables, code explanation",
                "keywords": ["code", "function", "class", "method", "implementation", "variable", "api", "interface", "what does"],
                "priority": const.CollectionPriority.HIGH,
            },
        }
        self._vector_stores = {
            collection: vector_store_factories.create_vector_store(
                qdrant_client=self._qdrant_client,
                embeddings=self._embeddings,
                collection_name=collection,
            )
            for collection in self._collections.keys()
        }
        # Setup query analysis chain
        system_template = (
            "You are a query analyzer for a code knowledge base. "
            "Determine which types of information are most relevant to the user's query.\n\n"
            "Available collections:\n"
            "{collections_description}\n\n"
            "Return a JSON with priority distribution for the three collections: "
            "specify how many results (from 0 to {total_results}) should be taken from each. "
            "The sum must equal {total_results}. "
            "Consider score_threshold = {score_threshold} (results below this threshold are not counted).\n\n"
            "Response format:\n"
            "{{\n"
            f'    "{qdrant_config_.docs_collection}": <number>,\n'
            f'    "{qdrant_config_.insights_collection}": <number>,\n'
            f'    "{qdrant_config_.ast_collection_python}": <number>\n'
            "}}\n\n"
            "Respond with JSON only, no explanations."
            f"Answer in {ai_config_.language.value}"
        )

        self.query_analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("User query: {query}")
        ])

        # Setup answer generation chain
        answer_template = (
            "You are an assistant answering questions about a software project.\n"
            "Use only the information from the provided context.\n"
            "If the answer is not in the context, say that you don't know.\n"
            "Be detailed but concise.\n\n"
            "Context:\n{context}\n\n"
            "User question: {question}\n\n"
            f"Answer in {ai_config_.language.value}"
        )

        self.answer_prompt = ChatPromptTemplate.from_template(answer_template)
        self.answer_chain = self.answer_prompt | llm | StrOutputParser()

    def _get_collections_description(self) -> str:
        """
        Get formatted collections description for prompt
        :return: formatted string
        """

        descriptions = []
        for coll_name, coll_info in self._collections.items():
            descriptions.append(
                f"- {coll_name}: {coll_info['description']}"
            )
        return "\n".join(descriptions)

    def _analyze_query(
            self,
            query: str,
            total_results: int = 10,
            score_threshold: float = 0.6,
    ) -> Dict[str, int]:
        """
        Analyze query to determine priority distribution across collections
        :param query: user query
        :param total_results: total number of results to fetch
        :param score_threshold: similarity score threshold
        :return: dict with collection names and number of results to fetch
        """

        try:
            # Try to use LLM for intelligent distribution
            chain = self.query_analysis_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "collections_description": self._get_collections_description(),
                "total_results": total_results,
                "score_threshold": score_threshold,
                "query": query,
            })

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                distribution = json.loads(json_match.group())

                # Validate and normalize
                for coll in self._collections.keys():
                    if coll not in distribution:
                        distribution[coll] = 0

                total = sum(distribution.values())
                if total != total_results:
                    # Normalize to total_results
                    factor = total_results / total if total > 0 else 1
                    distribution = {
                        coll: int(count * factor)
                        for coll, count in distribution.items()
                    }

                # Ensure at least 1 result for collections with non-zero distribution
                for coll in distribution:
                    if distribution[coll] > 0 and distribution[coll] < 1:
                        distribution[coll] = 1

                return distribution

        except Exception as e:
            print(f"Error in query analysis: {e}, falling back to keyword-based prioritization")

        distribution = {
            qdrant_config_.ast_collection_python: int(total_results * 0.4),  # 40% code
            qdrant_config_.insights_collection: int(total_results * 0.3),  # 30% insights
            qdrant_config_.docs_collection: int(total_results * 0.3),  # 30% docs
        }

        current_total = sum(distribution.values())
        if current_total != total_results:
            diff = total_results - current_total
            if diff > 0:
                # Add to collection with highest score
                max_coll = max(distribution.items(), key=lambda x: x[1])[0]
                distribution[max_coll] += diff
            else:
                # Subtract from collection with highest count, ensuring it stays >= 1
                max_coll = max(distribution.items(), key=lambda x: x[1])[0]
                distribution[max_coll] = max(1, distribution[max_coll] + diff)

        return distribution

    def _search_collection(
            self,
            collection_name: str,
            query: str,
            k: int,
            score_threshold: float,
            filter_conditions: Optional[dict] = None,
    ) -> List[rag_dto.SearchResult]:
        """
        Search in a single collection with score threshold
        :param collection_name: name of the collection
        :param query: search query
        :param k: number of results to fetch
        :param score_threshold: minimum similarity score
        :param filter_conditions: optional filters
        :return: list of search results
        """

        vector_store = self._vector_stores.get(collection_name)
        if not vector_store or k <= 0:
            return []

        # Build filter if provided
        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{field}",
                        match=MatchValue(value=value)
                    )
                )
            qdrant_filter = Filter(must=conditions)

        try:
            # Fetch more results than needed to account for threshold filtering
            fetch_k = min(k * 3, 20)  # Don't fetch too many
            docs_with_scores = vector_store.similarity_search_with_score(
                query=query,
                k=fetch_k,
                filter=qdrant_filter,
            )

            results = []
            for doc, score in docs_with_scores:
                if score >= score_threshold:
                    results.append(rag_dto.SearchResult(
                        text=doc.page_content,
                        score=score,
                        metadata=doc.metadata,
                    ))

            # Return top k results after threshold filtering
            return results[:k]

        except Exception as e:
            print(f"Error searching collection {collection_name}: {e}")
            return []

    def answer_question(
            self,
            question: str,
            total_results: int = 10,
            score_threshold: float = 0.6,
            filter_by_file: Optional[str] = None,
    ) -> rag_dto.RAGResponse:
        """
        Answer user question using intelligent collection prioritization
        :param question: user question
        :param total_results: total number of results to consider
        :param score_threshold: minimum similarity score
        :param filter_by_file: optional file path to filter by
        :return: RAG response with answer and sources
        """

        # Step 1: Analyze query to get collection distribution
        distribution = self._analyze_query(question, total_results, score_threshold)

        print(f"\n📊 Collection distribution: {distribution}")

        # Step 2: Search in each collection according to distribution
        all_results = []

        for collection_name, num_results in distribution.items():
            if num_results <= 0:
                continue

            filter_conditions = None
            if filter_by_file:
                if collection_name == qdrant_config_.docs_collection:
                    filter_conditions = {"path": filter_by_file}
                elif collection_name == qdrant_config_.ast_collection_python:
                    filter_conditions = {"file_path": filter_by_file}

            results = self._search_collection(
                collection_name=collection_name,
                query=question,
                k=num_results,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions,
            )

            all_results.extend(results)

        # Step 3: Sort all results by score
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Step 4: Prepare context for LLM
        context_parts = []
        for i, result in enumerate(all_results, 1):
            # Add source information
            source_info = []
            if "file_path" in result.metadata:
                source_info.append(f"File: {result.metadata['file_path']}")
            elif "path" in result.metadata:
                source_info.append(f"File: {result.metadata['path']}")

            if "object_name" in result.metadata:
                source_info.append(f"Object: {result.metadata['object_name']}")
            if "node_type" in result.metadata:
                source_info.append(f"Type: {result.metadata['node_type']}")
            if "insight_type" in result.metadata:
                source_info.append(f"Insight: {result.metadata['insight_type']}")

            context_parts.append(
                f"[{i}] Relevance: {result.score:.3f}\n"
                f"{', '.join(source_info) if source_info else 'Source: unknown'}\n"
                f"{result.text}\n"
                f"{'-' * 40}"
            )

        context = "\n".join(context_parts) if context_parts else "No context found."

        # Step 5: Generate answer
        if not all_results:
            answer_text = "Sorry, I couldn't find relevant information to answer your question."
        else:
            answer_text = self.answer_chain.invoke({
                "context": context,
                "question": question
            })

        # Step 6: Return response
        return rag_dto.RAGResponse(
            results=all_results,
            answer=answer_text,
        )

    def search(
            self,
            query: str,
            collection: Optional[str] = None,
            k: int = 5,
            score_threshold: Optional[float] = None,
    ) -> List[rag_dto.SearchResult]:
        """
        Search across collections (backward compatibility)
        :param query: search query
        :param collection: specific collection to search (if None, search all)
        :param k: number of results per collection
        :param score_threshold: minimum similarity score
        :return: list of search results
        """

        k = k or rag_config_.max_results
        score_threshold = score_threshold or rag_config_.score_threshold
        results = []

        if collection:
            collections_to_search = {collection: self._vector_stores.get(collection)}
        else:
            collections_to_search = self._vector_stores

        for coll_name, vector_store in collections_to_search.items():
            if not vector_store:
                continue

            try:
                docs_with_scores = vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                )

                for doc, score in docs_with_scores:
                    if score >= score_threshold:
                        result = rag_dto.SearchResult(
                            text=doc.page_content,
                            score=score,
                            metadata=doc.metadata,
                        )
                        results.append(result)

            except Exception as e:
                print(f"Error searching collection {coll_name}: {e}")
                continue

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def search_with_filter(
            self,
            query: str,
            collection: str,
            filter_conditions: dict,
            k: int = 5,
    ) -> List[rag_dto.SearchResult]:
        """
        Search with metadata filters (backward compatibility)
        :param query: search query
        :param collection: collection name
        :param filter_conditions: dict with field:value pairs for filtering
        :param k: number of results
        :return: list of filtered search results
        """

        vector_store = self._vector_stores.get(collection)
        if not vector_store:
            return []

        # Build Qdrant filter
        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{field}",
                        match=MatchValue(value=value)
                    )
                )
            qdrant_filter = Filter(must=conditions)

        try:
            docs_with_scores = vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=qdrant_filter,
            )

            results = []

            for doc, score in docs_with_scores:
                if score >= rag_config_.score_threshold:
                    result = rag_dto.SearchResult(
                        text=doc.page_content,
                        score=score,
                        metadata=doc.metadata,
                    )
                    results.append(result)

            return results

        except Exception as e:
            print(f"Error searching with filter: {e}")
            return []

    def search_by_file_path(
            self,
            query: str,
            file_path: str,
            k: int = 5,
    ) -> List[rag_dto.SearchResult]:
        """
        Search within specific file (backward compatibility)
        :param query: search query
        :param file_path: file path to filter by
        :param k: number of results
        :return: list of search results
        """

        results = []

        # Search in docs collection
        docs_results = self.search_with_filter(
            query=query,
            collection=qdrant_config_.docs_collection,
            filter_conditions={"path": file_path},
            k=k,
        )
        results.extend(docs_results)

        # Search in AST collection
        ast_results = self.search_with_filter(
            query=query,
            collection=qdrant_config_.ast_collection_python,
            filter_conditions={"file_path": file_path},
            k=k,
        )
        results.extend(ast_results)

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]