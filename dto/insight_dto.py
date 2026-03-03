import uuid

from pydantic import BaseModel, Field

from utils import const


class Insight(BaseModel):
    """
    Insight data
    """

    file_ids: list[uuid.UUID] = Field(
        title="List of related file ids",
    )
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
