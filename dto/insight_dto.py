import uuid
from typing import Dict, Any

from pydantic import BaseModel, Field

from dto import to_embed_dto
from utils import const


class Insight(BaseModel, to_embed_dto.ToEmbedDTO):
    """
    Insight data
    """

    content: str = Field(title="Insight content")
    insight_type: const.InsightType = Field(
        title="Insight type",
    )
    severity: const.InsightSeverity = Field(
        title="Insight severity",
    )
    confidence: float = Field(
        title="Confidence score",
        ge=0.0,
        le=1.0,
    )

    def to_embedding_document(
        self,
        chunk_index: int,
        total_chunks: int,
        chunk_content: str,
    ) -> Dict[str, Any]:
        """
        Transform to embedding document
        """

        return {
            "id": str(uuid.uuid4()),
            "text": chunk_content,
            "metadata": {
                "insight_type": self.insight_type.value,
                "severity": self.severity.value,
                "confidence": self.confidence,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
            }
        }


class InsightInDB(Insight):
    """
    Insight as DB object
    """

    id: uuid.UUID = Field(title="Id in DB")


class AgentInsightResponse(BaseModel):
    """
    Insight AI agent response
    """

    insights: list[Insight] = Field(title="Insights")
